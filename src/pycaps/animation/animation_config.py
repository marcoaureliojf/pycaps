from dataclasses import dataclass
from enum import Enum
from typing import Callable, Union, Literal

class Easing:
    LINEAR = lambda t: t
    EASE_IN = lambda t: t**2
    EASE_OUT = lambda t: 1 - (1 - t)**2
    EASE_IN_OUT = lambda t: t**2 * (3 - 2 * t)

@dataclass(frozen=True)
class AnimationConfig:
    duration: float = 0.5
    delay: float = 0.0
    easing: Callable[[float], float] = Easing.LINEAR

@dataclass(frozen=True)
class SlideInConfig(AnimationConfig):
    direction: Literal["left", "right", "up", "down"] = "left"
