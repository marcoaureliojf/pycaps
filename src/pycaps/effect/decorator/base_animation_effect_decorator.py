from ..base_effect_generator import BaseEffectGenerator
from ...models import TranscriptionSegment
from moviepy.editor import VideoClip
from typing import List, Tuple
from ...renderer.base_subtitle_renderer import BaseSubtitleRenderer
from ...layout.models import SegmentClipData, ElementLayout
from abc import abstractmethod

class BaseAnimationEffectDecorator(BaseEffectGenerator):
    def __init__(self, effect_generator: BaseEffectGenerator, renderer: BaseSubtitleRenderer):
        super().__init__(renderer)
        self.effect_generator = effect_generator

    @abstractmethod
    def _get_position_in_time(self, layout: ElementLayout, t: float) -> Tuple[float, float]:
        pass

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[SegmentClipData]:
        segments_clip_data = self.effect_generator.generate(segments, video_clip)
        print("Generating animation effect...")
        for segment_clip_data in segments_clip_data:
            for line_clip_data in segment_clip_data.lines:
                for word_clip_data in line_clip_data.words:
                    layout = word_clip_data.layout
                    for i in range(len(word_clip_data.clips)):
                        # Important: note that the position of the clip is updated but the layout.x and layout.y are not updated
                        #  It could be done but since the object is frozen, we should create a new object every time (or set as a mutable object)
                        #  and so far it is not worth it
                        offset_time = word_clip_data.clips[i].start - segment_clip_data.start
                        word_clip_data.clips[i] = word_clip_data.clips[i].set_position(
                            lambda t, layout=layout, offset_time=offset_time: self._get_position_in_time(layout, offset_time + t)
                        )
        
        return segments_clip_data
