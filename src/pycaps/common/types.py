from enum import Enum
from typing import List

class ElementType(str, Enum):
    WORD = "word"
    LINE = "line"
    SEGMENT = "segment"

class EventType(str, Enum):
    ON_NARRATION_STARTS = "narration-starts"
    ON_NARRATION_ENDS = "narration-ends"

class ElementState(Enum):
    WORD_BEING_NARRATED = "word-being-narrated"
    WORD_NOT_NARRATED_YET = "word-not-narrated-yet"
    WORD_ALREADY_NARRATED = "word-already-narrated"

    LINE_BEING_NARRATED = "line-being-narrated"
    LINE_NOT_NARRATED_YET = "line-not-narrated-yet"
    LINE_ALREADY_NARRATED = "line-already-narrated"

    @staticmethod
    def get_all_valid_states_combinations() -> List[List['ElementState']]:
        return [
            [ElementState.LINE_NOT_NARRATED_YET, ElementState.WORD_NOT_NARRATED_YET],
            [ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET],
            [ElementState.LINE_BEING_NARRATED, ElementState.WORD_BEING_NARRATED],
            [ElementState.LINE_BEING_NARRATED, ElementState.WORD_ALREADY_NARRATED],
            [ElementState.LINE_ALREADY_NARRATED, ElementState.WORD_ALREADY_NARRATED],
        ]
    
    @staticmethod
    def get_all_line_states() -> List['ElementState']:
        return [
            ElementState.LINE_NOT_NARRATED_YET,
            ElementState.LINE_BEING_NARRATED,
            ElementState.LINE_ALREADY_NARRATED,
        ]
