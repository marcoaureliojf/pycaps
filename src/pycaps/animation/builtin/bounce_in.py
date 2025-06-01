from ..base_animation import BaseAnimation
from ...tagger.models import WordClip
from typing import Tuple

class BounceIn(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            pos = clip.layout.position
            return pos.x, pos.y + 50 * (1 - t)**2
        
        self._apply_position(clip, offset, get_position)
