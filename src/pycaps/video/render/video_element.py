from .media_element import MediaElement
import cv2
import numpy as np
import os
from typing import List
import subprocess
import shlex
from pathlib import Path
from imageio_ffmpeg import get_ffmpeg_exe

ffmpeg_exe = get_ffmpeg_exe()

class VideoElement(MediaElement):

    def __init__(self, path: str, start: float, duration: float):
        super().__init__(start, duration)
        ext = os.path.splitext(path)[1].lower()
        if ext not in ['.mp4', '.mov', '.avi', '.mkv']:
            raise ValueError(f"Unsupported video format: {ext}")

        # self._load_frames(path)
        self._load_frames_with_ffmpeg(path)

    def get_frame(self, t_rel: float) -> np.ndarray:
        idx = int(t_rel * self._fps)
        idx = max(0, min(idx, self._num_frames - 1))
        return self._frames[idx].copy()
    
    def _load_frames(self, path: str):
        video_capture = cv2.VideoCapture(path)
        self._fps = video_capture.get(cv2.CAP_PROP_FPS)
        if not self._fps:
            raise RuntimeError(f"Unable to get video FPS prop for video: {path}")
        self._frames: List[np.ndarray] = []
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            if frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            self._frames.append(frame.astype(np.float32))

        self._num_frames = len(self._frames)
        if self._num_frames == 0:
            raise RuntimeError(f"Invalid video '{path}': 0 frames?")
        self._size = self._frames[0].shape[1], self._frames[0].shape[0]
        video_capture.release()
    
    def _load_frames_with_ffmpeg(self, path: str):
        path = Path(path).resolve().as_posix()
        probe = subprocess.run(
            shlex.split(f"ffprobe -v error -select_streams v:0 "
                        f"-show_entries stream=width,height,r_frame_rate,nb_frames "
                        f"-of default=noprint_wrappers=1:nokey=1 {path}"),
            capture_output=True, text=True, check=True
        )
        w, h, fps_str, nb_frames = probe.stdout.strip().splitlines()
        w, h = int(w), int(h)
        self._size = (w, h)
        # fps_str puede ser fracción como "30/1"
        num, den = fps_str.split('/')
        self._fps = int(float(num) / float(den))
        nb_frames = int(nb_frames) if nb_frames.isdigit() else None

        cmd = (
            f"{ffmpeg_exe} -i {path} -f rawvideo -pix_fmt rgba "
            f"-vf scale={w}:{h} -hide_banner -loglevel error pipe:1"
        )
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            bufsize=10**8
        )

        frame_size = w * h * 4
        frames = []
        while True:
            raw = proc.stdout.read(frame_size)
            if len(raw) < frame_size:
                break
            arr = np.frombuffer(raw, dtype=np.uint8)
            arr = arr.reshape((h, w, 4))
            arr = arr.astype(np.float32)
            arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
            frames.append(arr)

        proc.wait()
        self._frames = frames
        self._num_frames = len(frames)
