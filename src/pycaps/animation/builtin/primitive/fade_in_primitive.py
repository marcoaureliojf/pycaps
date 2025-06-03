from ...basic_animation import BasicAnimation
from pycaps.common import WordClip

class FadeInPrimitive(BasicAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        self._apply_opacity(clip, offset, lambda t: t)
