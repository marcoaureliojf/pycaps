from dataclasses import dataclass
from enum import Enum

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

@dataclass(frozen=True)
class AnimationConfig:
    type: AnimationType
    duration: float = 0.5
    delay: float = 0.0
    easing: str = "ease-in-out"
