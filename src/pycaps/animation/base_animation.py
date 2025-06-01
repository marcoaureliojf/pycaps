from typing import Tuple, Callable, Optional
from ..tagger.models import WordClip, Document
from .animation_config import AnimationConfig
from ..element import EventType, ElementType
from ..tag.tag_condition import TagCondition
from ..element.word_clip_selector import WordClipSelector
from abc import ABC, abstractmethod

class BaseAnimation(ABC):
    def __init__(
            self,
            config: AnimationConfig,
            what: ElementType = ElementType.WORD,
            when: EventType = EventType.ON_NARRATION_STARTS,
            tag_condition: Optional[TagCondition] = None,
        ) -> None:
        self._config: AnimationConfig = config
        self._what: ElementType = what
        self._when: EventType = when        
        self._position_transform: Optional[Callable[[], None]] = None
        self._size_transform: Optional[Callable[[], None]] = None
        self._opacity_transform: Optional[Callable[[], None]] = None

        self._selector = WordClipSelector().filter_by_time(when, what, self._config.duration, self._config.delay)
        if tag_condition:
            self._selector = self._selector.filter_by_tag(tag_condition)

    @abstractmethod
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        pass

    def run(self, document: Document) -> None:
        clips = self._selector.select(document)
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
        if self._when == EventType.ON_NARRATION_STARTS:
            return self.__get_on_start_offset(clip)
        elif self._when == EventType.ON_NARRATION_ENDS:
            return self.__get_on_end_offset(clip)
    
    def __get_on_start_offset(self, clip: WordClip) -> float:
        start_time = 0
        if self._what == ElementType.WORD:
            start_time = clip.get_word().time.start
        elif self._what == ElementType.LINE:
            start_time = clip.get_line().time.start
        elif self._what == ElementType.SEGMENT:
            start_time = clip.get_segment().time.start

        return clip.image_clip.start - start_time - self._config.delay

    def __get_on_end_offset(self, clip: WordClip) -> float:
        end_time = 0
        if self._what == ElementType.WORD:
            end_time = clip.get_word().time.end
        elif self._what == ElementType.LINE:
            end_time = clip.get_line().time.end
        elif self._what == ElementType.SEGMENT:
            end_time = clip.get_segment().time.end
        return -(end_time - self._config.duration - self._config.delay - clip.image_clip.start)
