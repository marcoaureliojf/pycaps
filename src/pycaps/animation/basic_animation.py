from typing import Tuple, Callable, Optional
from ..tagger.models import WordClip
from .animation_config import Transformer
from ..element import ElementType
from abc import abstractmethod
from .animation import Animation

class BasicAnimation(Animation):
    def __init__(
            self,
            duration: float,
            delay: float = 0.0,
            transformer: Callable[[float], float] = Transformer.LINEAR,
        ) -> None:
        super().__init__(duration, delay)
        self._transformer: Callable[[float], float] = transformer
        self._position_transform: Optional[Callable[[], None]] = None
        self._size_transform: Optional[Callable[[], None]] = None
        self._opacity_transform: Optional[Callable[[], None]] = None
        self._what: ElementType = ElementType.WORD

    @abstractmethod
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        pass

    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        self._what = what
        self._apply_animation(clip, offset)

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
        if self._duration == 0:
            raise ValueError("Animation duration can't be 0")
        
        normalice = lambda n: min(1, max(0, n))
        progress = normalice(t / self._duration)
        return normalice(self._apply_transformer(progress))

    def _apply_transformer(self, t: float) -> float:
        if not isinstance(self._transformer, Callable):    
            raise ValueError(f"Invalid transformer: {self._transformer}")
        
        return self._transformer(t)
