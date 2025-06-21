import cv2
import numpy as np
import multiprocessing as mp
import subprocess
import os
import tempfile
import math
import time
import shutil
from typing import Tuple, List, Optional
from .media_element import MediaElement
from .audio_element import AudioElement

# TODO: we need to create a new class VideoFile (or something like that)
#  then, the composer should receive a VideoFile instance
#  and, the VideoFile could have methods like "set_fps" or "set_size", to change the fps and the resolution
#  currently, we're not changing the input video fps/size, so we're working with the full video resolution received and theen
#  before saving, we are changing the resolution/fps for the output
#  this could be not the best approach... since if the input video has a big resolution, we would be working with that (instead the output res)
class VideoComposer:

    def __init__(self, input: str, output: str):
        self._input: str = input
        self._output: str = output
        self._elements: List[MediaElement] = []
        self._audio_elements: List[AudioElement] = []

        self._load_input_properties()
    
    def _load_input_properties(self) -> None:
        cap = cv2.VideoCapture(self._input)
        self._input_fps = cap.get(cv2.CAP_PROP_FPS)
        if self._input_fps <= 0:
            raise RuntimeError(f"Unable to get FPS from video {self._input}")
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if w <= 0 or h <= 0:
            raise RuntimeError(f"Unable to get size from video {self._input}")
        self._input_size: Tuple[int, int] = (w, h)
        self._input_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if self._input_total_frames <= 0:
            raise RuntimeError(f"Unable to get frame count for video {self._input}")
        cap.release()

        self._output_from_frame = 0
        self._output_to_frame = self._input_total_frames

    def get_input_fps(self) -> float:
        return self._input_fps
    
    def get_input_size(self) -> Tuple[int, int]:
        return self._input_size
    
    def get_input_duration(self) -> float:
        return self._input_total_frames * self._input_fps
    
    def cut_input(self, start: float, end: float) -> None:
        if start >= end:
            raise ValueError(f"Invalid (start, end) for cutting video: {start, end}")
        self._output_from_frame = int(start * self._input_fps)
        self._output_to_frame = int(end * self._input_fps)

    def add_element(self, element: MediaElement) -> None:
        self._elements.append(element)

    def add_audio(self, audio_element: AudioElement) -> None:
        """Schedule an audio file to start at start_time (seconds)."""
        self._audio_elements.append(audio_element)

    def _render_range(self, start_frame: int, end_frame: int, part_path: str) -> None:
        cap = cv2.VideoCapture(self._input)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        start_sec = start_frame / self._input_fps
        duration = (end_frame - start_frame) / self._input_fps

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            # Input video
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._input_size[0]}x{self._input_size[1]}",
            "-r", str(self._input_fps),
            "-i", "pipe:0",
            # Audio
            "-ss", str(start_sec),
            "-t", str(duration),
            "-i", self._input,
            # Maps
            "-map", "0:v",
            "-map", "1:a",
            # output codecs
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            # output config
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            part_path,
            # no logs
            "-loglevel", "error",
            "-hide_banner"
        ]

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE
        )

        frame_idx = start_frame
        while frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            for el in self._elements:
                frame = el.render(frame, frame_idx / self._input_fps)
            try:
                process.stdin.write(frame.astype(np.uint8).tobytes())
            except BrokenPipeError:
                print("FFmpeg process died early.")
                break
            frame_idx += 1

        cap.release()
        process.stdin.close()
        process.wait()

    def _merge_parts(self, part_paths: List[str], merged_path: str) -> None:
        # Create a concat file
        list_path = os.path.join(os.path.dirname(merged_path), "parts.txt")
        with open(list_path, 'w') as f:
            for p in part_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        # Merge using ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            merged_path,
            "-loglevel", "error",
            "-hide_banner"
        ]
        subprocess.run(cmd, check=True)

    def _mux_audio(
        self,
        video_path: str,
        output_path: str,
        aac_bitrate: str = "192k"
    ) -> None: 
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-hide_banner",
            "-i", video_path
        ]
        if len(self._audio_elements) == 0:
            ffmpeg_cmd += [
                "-c:v", "copy",
                "-c:a", "copy",
                "-b:a", aac_bitrate,
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True)
            return
        
        for audio in self._audio_elements:
            ffmpeg_cmd += ["-i", audio.path]
        
        # Build the filter_complex:
        #   0:a is the original audio
        #   For each SFX i, we apply adelay=ms|all=1 and name it [s{i}]
        #   Finally, we mix all of them with amix=inputs=N
        filter_parts = []
        inputs = ["[0:a]"]
        for idx, audio in enumerate(self._audio_elements, start=1):
            delay_ms = int(audio.start * 1000)
            part = (
                f"[{idx}:a]adelay={delay_ms}|all=1"
                f"[s{idx}]"
            )
            filter_parts.append(part)
            inputs.append(f"[s{idx}]")
        
        # amix line
        num_inputs = len(inputs)
        amix = "".join(inputs) + f"amix=inputs={num_inputs}:dropout_transition=0[aout]"
        filter_parts.append(amix)
        
        filter_complex = ";".join(filter_parts)
        
        # Add filter_complex, map, and codec options
        ffmpeg_cmd += [
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", aac_bitrate,
            output_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)

    def render(self, use_multiprocessing: bool = True, processes: Optional[int] = None) -> None:
        temp_dir = tempfile.mkdtemp()

        if use_multiprocessing:
            processes = processes or mp.cpu_count()
            total_frames = self._output_to_frame - self._output_from_frame
            chunk_size = math.ceil(total_frames / processes)
            part_paths = []
            jobs = []
            for i in range(processes):
                start = self._output_from_frame + i * chunk_size
                end = min(self._output_from_frame + ((i+1) * chunk_size), self._output_to_frame)
                part_path = os.path.join(temp_dir, f"part_{i}.mp4")
                part_paths.append(part_path)
                p = mp.Process(
                    target=self._render_range, 
                    args=(start, end, part_path)
                )
                jobs.append(p)
                p.start()
            for p in jobs:
                p.join()
            merged_no_audio = os.path.join(temp_dir, "merged_no_audio.mp4")
            self._merge_parts(part_paths, merged_no_audio)
            final = self._output
            start = time.time()
            self._mux_audio(merged_no_audio, final)
            print(f"self._mux_audio took {time.time()-start}")
        else:
            # Single-process
            start = time.time()
            tmp = os.path.join(temp_dir, "noaudio.mp4")
            self._render_range(self._output_from_frame, self._output_to_frame, tmp)
            middle = time.time()
            print(f"self._render_range took {middle-start}")
            self._mux_audio(tmp, self._output)
            print(f"self._mux_audio took {time.time()-middle}")
        
        shutil.rmtree(temp_dir)
