from typing import List, Union
from ..utils.time_utils import times_intersect
from .models import ElementType, EventType
from ..tagger.models import Word, Line, Segment, WordState

class TimeEventSelector:
    """
    Selects WordStates whose clips intersect a time window relative to a narration event
    (start or end) of a given element (word, line, or segment).

    Parameters:
        event_type: EventType.STARTS_NARRATION or EventType.ENDS_NARRATION
        element_type: the scope of the event (ElementType.WORD, LINE or SEGMENT)
        duration: duration of the time window
        delay: offset from the event before the window starts

    Example:
        TimeEventSelector(EventType.STARTS_NARRATION, ElementType.SEGMENT, duration=10, delay=2)
        → selects all WordStates whose clip intersects [segment.start + 2, segment.start + 12]
    """

    def __init__(self, event_type: EventType, element_type: ElementType, duration: float, delay: float) -> None:
        self._event_type = event_type
        self._element_type = element_type
        self._duration = duration
        self._delay = delay

    def select(self, word_states: List[WordState]) -> List[WordState]:
        match self._element_type:
            case ElementType.WORD:
                return self.__filter_by_words(word_states)
            case ElementType.LINE:
                return self.__filter_by_lines(word_states)
            case ElementType.SEGMENT:
                return self.__filter_by_segments(word_states)

    def __get_event_time_range(self, element: Union[Word, Line, Segment]) -> tuple[float, float]:
        if self._event_type == EventType.STARTS_NARRATION:
            start = element.time.start + self._delay
        else:  # ENDS_NARRATION
            start = element.time.end - self._delay - self._duration
        end = start + self._duration
        return start, end

    def __filter_by_words(self, word_states: List[WordState]) -> List[WordState]:
        return [
            state for state in word_states
            if times_intersect(
                *self.__get_event_time_range(state.get_word()),
                state.clip.start,
                state.clip.end
            )
        ]

    def __filter_by_lines(self, word_states: List[WordState]) -> List[WordState]:
        return [
            state for state in word_states
            if times_intersect(
                *self.__get_event_time_range(state.get_line()),
                state.clip.start,
                state.clip.end
            )
        ]

    def __filter_by_segments(self, word_states: List[WordState]) -> List[WordState]:
        return [
            state for state in word_states
            if times_intersect(
                *self.__get_event_time_range(state.get_segment()),
                state.clip.start,
                state.clip.end
            )
        ]
