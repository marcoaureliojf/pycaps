from typing import List, Tuple, Callable, Optional
from ..tagger.models import WordClip
import numpy as np
from .animation_config import AnimationConfig
from ..element import EventType, ElementType

class BaseAnimation:
    def __init__(self, config: AnimationConfig, element_type: ElementType, event_type: EventType) -> None:
        self._config: AnimationConfig = config
        self._element_type: ElementType = element_type
        self._event_type: EventType = event_type
        self._position_transform: Optional[Callable[[], None]] = None
        self._size_transform: Optional[Callable[[], None]] = None
        self._opacity_transform: Optional[Callable[[], None]] = None

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        pass

    def run(self, clips: List[WordClip]) -> None:
        for clip in clips:
            self._apply_animation(clip, self.__get_time_offset(clip))

            # apply transforms in order (order is important)
            if self._size_transform: self._size_transform()
            if self._position_transform: self._position_transform()
            if self._opacity_transform: self._opacity_transform()

    def _apply_position(self, clip: WordClip, offset: float, get_position_fn: Callable[[float], Tuple[float, float]]) -> None:
        start_pos = clip.image_clip.pos(0)
        def transform() -> None:
            clip.image_clip = clip.image_clip.set_position(
                lambda t: get_position_fn(self._normalice_time(t + offset)) if t + offset >= 0 else start_pos)
        
        self._position_transform = transform

    def _apply_size(self, clip: WordClip, offset: float, get_resize_fn: Callable[[float], float]) -> None:
        def transform() -> None:
            clip.image_clip = clip.image_clip.resize(
                lambda t: get_resize_fn(self._normalice_time(t + offset)) if t + offset >= 0 else 1)
        
        self._size_transform = transform
    
    def _apply_opacity(self, clip: WordClip, offset: float, get_opacity_fn: Callable[[float], float]) -> None:
        def transform() -> None:
            def fl(gf, t):
                # please, note that gf(t) is clip.get_frame(t), which was previously called (in blit_on) and memoized
                # so, getting it shouldn't be a performance issue
                # this function will be called when clip.mask.get_frame(t) is called
                clip_frame = gf(t)
                if t + offset < 0:
                    return clip_frame
                return clip_frame * get_opacity_fn(self._normalice_time(t + offset))

            if clip.image_clip.mask is None:
                clip.image_clip = clip.image_clip.add_mask()

            clip.image_clip = clip.image_clip.fl(fl, apply_to=['mask'])
        
        self._opacity_transform = transform

    def _normalice_time(self, t: float) -> float:
        '''
        Normalize the time to be between 0 and 1 using the duration of the animation
        And apply the easing function to the time
        '''
        if self._config.duration == 0:
            raise ValueError("Animation duration can't be 0")
        
        normalice = lambda n: min(1, max(0, n))
        progress = normalice(t / self._config.duration)
        return normalice(self._apply_easing(progress))

    def _apply_easing(self, t: float) -> float:
        if not isinstance(self._config.easing, Callable):    
            raise ValueError(f"Invalid easing function: {self._config.easing}")
        
        return self._config.easing(t)

    def __get_time_offset(self, clip: WordClip) -> float:
        if self._event_type == EventType.ON_NARRATION_STARTS:
            return self.__get_on_start_offset(clip)
        elif self._event_type == EventType.ON_NARRATION_ENDS:
            return self.__get_on_end_offset(clip)
    
    def __get_on_start_offset(self, clip: WordClip) -> float:
        start_time = 0
        if self._element_type == ElementType.LINE:
            start_time = clip.get_line().time.start
        elif self._element_type == ElementType.SEGMENT:
            start_time = clip.get_segment().time.start

        return clip.image_clip.start - start_time - self._config.delay

    def __get_on_end_offset(self, clip: WordClip) -> float:
        end_time = 0
        if self._element_type == ElementType.LINE:
            end_time = clip.get_line().time.end
        elif self._element_type == ElementType.SEGMENT:
            end_time = clip.get_segment().time.end
        return -(end_time - self._config.duration - self._config.delay - clip.image_clip.start)

class FadeInAnimationEffect(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        self._apply_opacity(clip, offset, lambda t: t)

class FadeOutAnimationEffect(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        self._apply_opacity(clip, offset, lambda t: 1 - t)

class BounceInAnimationEffect(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            pos = clip.layout.position
            return pos.x, pos.y + 50 * (1 - t)**2
        
        self._apply_position(clip, offset, get_position)

class CenteredPopInEffect(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        group_center = self._get_group_center(clip)
        word_original_width, word_original_height = clip.layout.size.width, clip.layout.size.height
        word_final_center = (
            clip.layout.position.x + word_original_width / 2,
            clip.layout.position.y + word_original_height / 2
        )
    
        def get_size_factor(t: float) -> float:
            return 0.8 + 0.2 * (t**0.5)

        def get_position(t: float) -> Tuple[float, float]:
            scale = get_size_factor(t)
            current_width = word_original_width * scale
            current_height = word_original_height * scale

            current_center_x = group_center[0] + (word_final_center[0] - group_center[0]) * t
            current_center_y = group_center[1] + (word_final_center[1] - group_center[1]) * t

            final_x = current_center_x - (current_width / 2)
            final_y = current_center_y - (current_height / 2)
            
            return (final_x, final_y)

        self._apply_opacity(clip, offset, lambda t: t)
        self._apply_size(clip, offset, get_size_factor)
        self._apply_position(clip, offset, get_position)

    def _get_group_center(self, clip: WordClip) -> Tuple[float, float]:
        if self._element_type == ElementType.LINE:
            line = clip.get_line()
            return (
                line.max_layout.position.x + line.max_layout.size.width / 2,
                line.max_layout.position.y + line.max_layout.size.height / 2
            )
        
        if self._element_type == ElementType.SEGMENT:
            segment = clip.get_segment()
            return (
                segment.max_layout.position.x + segment.max_layout.size.width / 2,
                segment.max_layout.position.y + segment.max_layout.size.height / 2
            )

        return (
            clip.layout.position.x + clip.layout.size.width / 2,
            clip.layout.position.y + clip.layout.size.height / 2
        )
    
class BlockScaleInEffect(BaseAnimation):

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        group_center = self._get_group_center(clip)
        word_final_center = (
            clip.layout.position.x + clip.layout.size.width / 2,
            clip.layout.position.y + clip.layout.size.height / 2
        )
        relative_pos_vector = (
            word_final_center[0] - group_center[0],
            word_final_center[1] - group_center[1]
        )

        def get_size_factor(t: float) -> float:
            return 0.8 + 0.2 * (t**0.5)

        def get_position(t: float) -> Tuple[float, float]:
            progress = get_size_factor(t)
            
            current_width = clip.layout.size.width * progress
            current_height = clip.layout.size.height * progress

            current_center_x = group_center[0] + (relative_pos_vector[0] * progress)
            current_center_y = group_center[1] + (relative_pos_vector[1] * progress)

            final_x = current_center_x - (current_width / 2)
            final_y = current_center_y - (current_height / 2)
            
            return (final_x, final_y)

        self._apply_opacity(clip, offset, lambda t: t)
        self._apply_position(clip, offset, get_position)
        self._apply_size(clip, offset, get_size_factor)


    def _get_group_center(self, clip: WordClip) -> Tuple[float, float]:
        if self._element_type == ElementType.LINE:
            line = clip.get_line()
            return (
                line.max_layout.position.x + line.max_layout.size.width / 2,
                line.max_layout.position.y + line.max_layout.size.height / 2
            )
        
        if self._element_type == ElementType.SEGMENT:
            segment = clip.get_segment()
            return (
                segment.max_layout.position.x + segment.max_layout.size.width / 2,
                segment.max_layout.position.y + segment.max_layout.size.height / 2
            )

        return (
            clip.layout.position.x + clip.layout.size.width / 2,
            clip.layout.position.y + clip.layout.size.height / 2
        )

class SlideInFromLeftAnimationEffect(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            pos = clip.layout.position
            return pos.x - 100 + t * 100, pos.y
        
        self._apply_position(clip, offset, get_position)

class WaveAnimationEffect(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            wave_amplitude = 7
            wave_period = 3
            y_offset = wave_amplitude * np.sin(2 * np.pi * t / wave_period)
            return clip.layout.position.x, clip.layout.position.y + y_offset
        
        self._apply_position(clip, offset, get_position)
