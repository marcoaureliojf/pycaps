from typing import List, Callable
from ..tagger.models import Document, WordState
from ..tag.tag_condition import TagCondition
from .models import ElementType, EventType
from .tag_based_selector import TagBasedSelector
from .time_event_selector import TimeEventSelector

class WordStateSelector:
    """
    A flexible and composable selector for WordStates, allowing filters
    by tag, time, or any other property.
    """
    def __init__(self):
        self._filters: List[Callable[[List[WordState]], List[WordState]]] = []

    def filter_by_tag(self, tag_condition: TagCondition) -> 'WordStateSelector':
        def filter_fn(word_states: List[WordState]) -> List[WordState]:
            return TagBasedSelector(tag_condition).select(word_states)
        self._filters.append(filter_fn)
        return self

    def filter_by_time(self, when: EventType, what: ElementType, duration: float, delay: float) -> 'WordStateSelector':
        def filter_fn(word_states: List[WordState]) -> List[WordState]:
            return TimeEventSelector(when, what, duration, delay).select(word_states)
        self._filters.append(filter_fn)
        return self

    def select(self, document: Document) -> List[WordState]:
        result = document.get_word_states()
        for f in self._filters:
            result = f(result)
        return result
