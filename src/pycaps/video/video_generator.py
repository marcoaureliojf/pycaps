from typing import Optional, Dict, Any, Literal
import os
from moviepy.editor import VideoFileClip, CompositeVideoClip, CompositeAudioClip
import tempfile
from pycaps.common import Document, VideoResolution
from pathlib import Path

class VideoGenerator:
    def __init__(self):
        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None
        self._audio_path: Optional[str] = None
        self._moviepy_write_options: Optional[Dict[str, Any]] = None

        # State of video generation
        self._has_video_generation_started: bool = False
        self._is_temp_audio_file: bool = False
        self._final_video: Optional[VideoFileClip] = None
        self._video_clip: Optional[VideoFileClip] = None
        self._video_resolution: Optional[VideoResolution] = None
        self._fragment_time: Optional[tuple[float, float]] = None

    def set_audio_path(self, audio_path: str):
        self._audio_path = audio_path

    def set_moviepy_write_options(self, moviepy_write_options: Dict[str, Any]):
        self._moviepy_write_options = moviepy_write_options

    def set_video_resolution(self, resolution: VideoResolution):
        self._video_resolution = resolution

    def set_fragment_time(self, fragment_time: tuple[float, float]):
        self._fragment_time = fragment_time

    def start(self, input_video_path: str, output_video_path: str):
        if not os.path.exists(input_video_path):
            print(f"Error: Input video file not found: {input_video_path}")
            return

        self._input_video_path = input_video_path
        self._output_video_path = output_video_path
        self._video_clip = VideoFileClip(self._input_video_path)
        if self._fragment_time:
            start = min(max(self._fragment_time[0], 0), self._video_clip.duration - 2)
            end = min(max(self._fragment_time[1], 0), self._video_clip.duration)
            self._video_clip = self._video_clip.subclip(start, end)

        should_extract_audio = self._audio_path is None
        self._audio_path = self._get_audio_path_to_transcribe(self._video_clip)
        self._is_temp_audio_file = should_extract_audio and self._audio_path is not None and os.path.exists(self._audio_path)
        
        self._has_video_generation_started = True

    def _get_audio_path_to_transcribe(self, video_clip: VideoFileClip) -> str:
        if self._audio_path:
            if not os.path.exists(self._audio_path):
                print(f"Error: External audio file not found: {self._audio_path}")
                video_clip.close()
                return
            print(f"Using external audio: {self._audio_path}")
            return self._audio_path
        
        print("Extracting audio from video...")
        # Create a temporary file that is not deleted immediately for Whisper to access
        fd, temp_audio_file_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd) # Close the file descriptor as MoviePy will open/write to the path
        try:
            if video_clip.audio is None:
                print("Error: The video does not contain an audio track.")
                video_clip.close()
                if os.path.exists(temp_audio_file_path):
                        os.remove(temp_audio_file_path)
                return
            video_clip.audio.write_audiofile(temp_audio_file_path, verbose=False, logger=None)
            print(f"Audio extracted to: {temp_audio_file_path}")
            return temp_audio_file_path
        except Exception as e:
            print(f"Error extracting audio: {e}")
            video_clip.close()
            if os.path.exists(temp_audio_file_path):
                os.remove(temp_audio_file_path)
            raise e
        
    def get_audio_path(self) -> str:
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        if not self._audio_path:
            raise RuntimeError("Audio path is not set. This is an unexpected error.")
        
        return self._audio_path
    
    def get_video_clip(self) -> VideoFileClip:
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        if not self._video_clip:
            raise RuntimeError("Video clip is not set. This is an unexpected error.")
        
        return self._video_clip

    def generate(self, document: Document):
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        
        clips = document.get_moviepy_clips()
        if not clips:
            print("No subtitle clips were generated. The original video (or with external audio if provided) will be saved.")
            self._final_video = self._video_clip 
        else:
            print("Compositing final video with subtitles...")
            video_with_subtitles = self._video_clip.set_audio(None)
            self._final_video = CompositeVideoClip([video_with_subtitles] + clips, size=self._video_clip.size)
            if self._video_clip.audio:
                final_audio = CompositeAudioClip([self._video_clip.audio] + document.sfxs) if len(document.sfxs) > 0 else self._video_clip.audio
                self._final_video = self._final_video.set_audio(final_audio)
            else:
                print("Warning: Original video had no audio. Final video will also have no audio.")

        print(f"Writing final video to: {self._output_video_path}")
        codecs = self._get_codecs_for_output()
        default_write_options = {
            "codec": codecs["codec"],
            "audio_codec": codecs["audio_codec"],
            "threads": os.cpu_count() or 2,
            "logger": "bar",
            "fps": 30
        }
        if self._moviepy_write_options:
            default_write_options.update(self._moviepy_write_options)
        
        self._final_video = self._apply_video_resolution(self._final_video)
        self._final_video.write_videofile(self._output_video_path, **default_write_options)

    def _get_codecs_for_output(self) -> list[str]:
        output_path = Path(self._output_video_path)
        ext = output_path.suffix.lower()
        codec_map = {
            ".mp4":  {"codec": "libx264", "audio_codec": "aac"},
            ".mov":  {"codec": "libx264", "audio_codec": "aac"},
            ".avi":  {"codec": "mpeg4",   "audio_codec": "libmp3lame"},
            ".mkv":  {"codec": "libx264", "audio_codec": "aac"},
            ".webm": {"codec": "libvpx",  "audio_codec": "libvorbis"},
            ".ogv":  {"codec": "libtheora", "audio_codec": "libvorbis"},
        }

        return codec_map.get(ext, codec_map[".mp4"])
    
    def _apply_video_resolution(self, video_clip: VideoFileClip) -> VideoFileClip:
        if self._video_resolution is None:
            return video_clip
    
        height: int
        match self._video_resolution:
            case VideoResolution._4K:
                height = 4096
            case VideoResolution._2K:
                height = 2048
            case VideoResolution._1080P:
                height = 1080
            case VideoResolution._720P:
                height = 720
            case VideoResolution._480P:
                height = 480
            case VideoResolution._360P:
                height = 360
        
        return video_clip.resize(height=height)

    def close(self):
        self._remove_audio_file_if_needed()
        if self._video_clip:
            self._video_clip.close()
        if self._final_video:
            self._final_video.close()
        
        self._has_video_generation_started = False
        self._is_temp_audio_file = False
        self._video_clip = None
        self._final_video = None

    def _remove_audio_file_if_needed(self):
        if not self._is_temp_audio_file:
            return
        try:
            os.remove(self._audio_path)
            print(f"Temporary audio file deleted: {self._audio_path}")
        except Exception as e:
            print(f"Error deleting temporary audio file {self._audio_path}: {e}")
