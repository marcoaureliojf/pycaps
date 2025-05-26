from abc import ABC, abstractmethod
from typing import List
from moviepy.editor import VideoClip
from ..renderer.base_subtitle_renderer import BaseSubtitleRenderer
from ..models import TranscriptionSegment
from ..layout.models import SegmentClipData

class BaseEffectGenerator(ABC):
    def __init__(self, renderer: BaseSubtitleRenderer):
        self.renderer = renderer

    @abstractmethod
    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[SegmentClipData]:
        """
        Generates a list of MoviePy VideoClips based on transcription segments
        and effect-specific options.

        Args:
            segments: A list of TranscriptionSegment objects.
            video_clip: The MoviePy VideoClip to which subtitles will be added.
                        Used for dimensions (video_clip.w, video_clip.h) and timing reference.

        Returns:
            A list of segment clip data objects.
            These objects contain the layout and the clips for each line and word.
        """
        pass 