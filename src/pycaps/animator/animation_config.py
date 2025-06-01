from dataclasses import dataclass
from enum import Enum
from typing import Callable, Union

class Easing:
    LINEAR = lambda t: t
    EASE_IN = lambda t: t**2
    EASE_OUT = lambda t: 1 - (1 - t)**2
    EASE_IN_OUT = lambda t: t**2 * (3 - 2 * t)

class AnimationType(Enum):
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    BOUNCE_IN = "bounce_in"
    BOUNCE_OUT = "bounce_out"
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    GROW_IN = "grow_in"
    GROW_OUT = "grow_out"
    SHRINK_IN = "shrink_in"
    SHRINK_OUT = "shrink_out"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    WAVE = "wave"
    CENTERED_POP_IN = "centered_pop_in"
    BLOCK_SCALE_IN = "block_scale_in"

@dataclass(frozen=True)
class AnimationConfig:
    type: AnimationType
    duration: float = 0.5
    delay: float = 0.0
    easing: Callable[[float], float] = Easing.LINEAR
