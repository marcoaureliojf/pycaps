from abc import ABC, abstractmethod
from typing import List
from moviepy.editor import VideoClip
from ..renderers.base_subtitle_renderer import BaseSubtitleRenderer
from ..models import TranscriptionSegment

class SubtitleEffectGenerator(ABC):
    def __init__(self, renderer: BaseSubtitleRenderer):
        self.renderer = renderer

    @abstractmethod
    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[VideoClip]:
        """
        Generates a list of MoviePy VideoClips based on transcription segments
        and effect-specific options.

        Args:
            segments: A list of TranscriptionSegment objects.
            video_clip: The MoviePy VideoClip to which subtitles will be added.
                        Used for dimensions (video_clip.w, video_clip.h) and timing reference.

        Returns:
            A list of VideoClip objects (or subclasses like ImageClip) ready to be
            composited with the main video.
        """
        pass 