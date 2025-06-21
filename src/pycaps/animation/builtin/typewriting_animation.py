from ..animation import Animation
from typing import List, TYPE_CHECKING
from pycaps.common import WordClip
from pycaps.common import ElementType
from pycaps.logger import logger

if TYPE_CHECKING:
    import numpy as np

# TODO: remove
class TypewritingAnimation(Animation):
    '''
        A typewriting animation that animates the text in a word clip.
        This class modifies the frame of the word clip to simulate a typewriting effect.
        It applies some easy techniques to try to split each word into letters, identifying the spaces between them.
        It works fine when the words don't have big shadows/borders, and there space between the letters.
        Otherwise, it will not work.

        The good news is that this animation is faster to compute than TypewritingEffect alternative (and it could be even faster with some work).
        However, this class is not mantained anymore, and it's not well tested, so it might not work as expected.
    '''

    def __init__(self) -> None:
        super().__init__(0)
        logger().warning("TypewritingAnimation is deprecated and could generate unexpected results.")
        self._cached_letter_bounds = {}

    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        import numpy as np

        def fl(gf, t):
            frame = gf(t)
            t = t + offset
            if t < 0 or t > clip.media_clip.duration:
                return frame
            bounds = self._get_letter_bounds(clip.get_word().text, frame)
            number_of_letters = len(bounds)
            if number_of_letters == 0:
                return frame
            letter_duration = clip.media_clip.duration / number_of_letters
            last_letter_index = int(t / letter_duration)
            end_x = bounds[last_letter_index][1]
            new_frame = np.zeros_like(frame)
            new_frame[:, :end_x] = frame[:, :end_x]
            return new_frame

        clip.media_clip = clip.media_clip.fl(fl)
        if clip.media_clip.mask is not None:
            clip.media_clip.mask = clip.media_clip.mask.fl(fl)


    def _get_background_color(self, frame: 'np.ndarray') -> 'np.ndarray':
        import numpy as np

        h, w, _ = frame.shape
        corners = np.array([
            frame[0, 0],
            frame[0, w - 1],
            frame[h - 1, 0],
            frame[h - 1, w - 1]
        ])
        return corners.mean(axis=0)
    
    def _is_background(self, pixel: 'np.ndarray', bg_color: 'np.ndarray') -> bool:
        import numpy as np

        threshold = 30
        return np.linalg.norm(pixel[:3] - bg_color[:3]) < threshold 
    
    def _get_letter_bounds(self, text: str, frame: 'np.ndarray') -> List[tuple]:
        import numpy as np
        
        if text in self._cached_letter_bounds:
            return self._cached_letter_bounds[text]
        
        h, w, _ = frame.shape
        bg_color = self._get_background_color(frame)

        mask = np.array([
            [not self._is_background(frame[y, x], bg_color) for x in range(w)]
            for y in range(h)
        ])
        
        column_activity = mask.sum(axis=0)
        bounds = []

        in_letter = False
        start = 0
        for x, is_letter_column in enumerate(column_activity > 0):
            if is_letter_column and not in_letter:
                in_letter = True
            elif not is_letter_column and in_letter:
                in_letter = False
                bounds.append((start, x))
                start = x
        
        if len(bounds) > 0:
            last_bound = bounds[-1]
            bounds[-1] = (last_bound[0], w)

        self._cached_letter_bounds[text] = bounds
        return bounds
