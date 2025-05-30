from enum import Enum
from dataclasses import dataclass

class ElementType(Enum):
    WORD = "word"
    LINE = "line"
    SEGMENT = "segment"

class EventType(Enum):
    ON_NARRATION_STARTS = "starts-narration"
    ON_NARRATION_ENDS = "ends-narration"

@dataclass
class Event:
    type: EventType
    element: ElementType
    duration: float
    delay: float


