from enum import Enum
from dataclasses import dataclass

class ElementType(Enum):
    WORD = "word"
    LINE = "line"
    SEGMENT = "segment"

class EventType(Enum):
    STARTS_NARRATION = "starts-narration"
    ENDS_NARRATION = "ends-narration"

@dataclass
class Event:
    type: EventType
    element: ElementType
    duration: float
    delay: float


