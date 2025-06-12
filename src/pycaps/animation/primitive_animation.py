from typing import Tuple, Callable, Optional
from pycaps.common import WordClip, ElementType
from .definitions import Transformer
from abc import abstractmethod
from .animation import Animation

class PrimitiveAnimation(Animation):
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
        old_position_transform = clip.moviepy_clip.pos
        def transform() -> None:
            def new_position_transform(t):
                if t + offset < 0 or t + offset > self._duration:
                    return old_position_transform(t)
                
                return get_position_fn(self._normalice_time(t + offset))

            clip.moviepy_clip = clip.moviepy_clip.set_position(new_position_transform)
        
        self._position_transform = transform

    def _apply_size(self, clip: WordClip, offset: float, get_resize_fn: Callable[[float], float]) -> None:
        import cv2
        import numpy as np

        original_size = clip.moviepy_clip.size
        def transform() -> None:
            def resize(frame, t):
                if t + offset < 0:
                    return frame
                scale = get_resize_fn(self._normalice_time(t + offset))
                if scale == 1.0:
                    return frame

                nw = int(original_size[0] * scale)
                nh = int(original_size[1] * scale)
                # source: https://docs.opencv.org/3.4/da/d54/group__imgproc__transform.html#ga47a974309e9102f5f08231edc7e7529d
                # "To shrink an image, it will generally look best with INTER_AREA interpolation, whereas to enlarge an image,
                #  it will generally look best with INTER_CUBIC (slow) or INTER_LINEAR (faster but still looks OK)."
                interpolation_method = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
                return cv2.resize(frame, (nw, nh), interpolation=interpolation_method)

            clip.moviepy_clip = clip.moviepy_clip.fl(lambda gf, t: resize(gf(t), t))
            if clip.moviepy_clip.mask is not None:
                # moviepy normalices and transforms the mask to uint8 in their resize() function
                # I think that is the reason why we lose quality in images with alpha channel (I'm not totally sure)
                # For that reason, we'll use our own resize function
                # Note that np.clip() is needed since some interpolation methods can return values out of range (0, 1)
                clip.moviepy_clip.mask = clip.moviepy_clip.mask.fl(lambda gf, t: np.clip(resize(gf(t), t), 0, 1).astype(np.float64))

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

            if clip.moviepy_clip.mask is None:
                clip.moviepy_clip = clip.moviepy_clip.add_mask()

            clip.moviepy_clip = clip.moviepy_clip.fl(fl, apply_to=['mask'])
        
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
