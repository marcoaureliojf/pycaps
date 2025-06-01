from ..base_animation import BaseAnimation
from ...tagger.models import WordClip

class FadeIn(BaseAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        self._apply_opacity(clip, offset, lambda t: t)
