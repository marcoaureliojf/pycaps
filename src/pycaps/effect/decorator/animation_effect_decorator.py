from typing import Tuple
from ...layout.models import ElementLayout
from .base_animation_effect_decorator import BaseAnimationEffectDecorator
import numpy as np
from ..base_effect_generator import BaseEffectGenerator
from ...renderer.base_subtitle_renderer import BaseSubtitleRenderer

class BounceInAnimationEffect(BaseAnimationEffectDecorator):
    def _get_position_in_time(self, layout: ElementLayout, t: float) -> Tuple[float, float]:
        if t < 0:
            return layout.x, layout.y + 50
        elif t < 0.3:
            y = layout.y + 50 * (1 - t / 0.3)**2
        else:
            y = layout.y
        return layout.x, y

class SlideInFromLeftAnimationEffect(BaseAnimationEffectDecorator):
    def _get_position_in_time(self, layout: ElementLayout, t: float) -> Tuple[float, float]:
        if t < 0:
            return layout.x - 100, layout.y
        elif t < 0.3:
            x = layout.x - 100 + (t / 0.3) * 100
        else:
            x = layout.x
        return x, layout.y

class WaveAnimationEffect(BaseAnimationEffectDecorator):
    def _get_position_in_time(self, layout: ElementLayout, t: float) -> Tuple[float, float]:
        wave_amplitude = 7
        wave_period = 3
        y_offset = wave_amplitude * np.sin(2 * np.pi * t / wave_period)
        return layout.x, layout.y + y_offset
