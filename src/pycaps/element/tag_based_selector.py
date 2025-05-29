from typing import List
from ..tagger.models import WordState
from ..tag.tag_condition import TagCondition

class TagBasedSelector:
    def __init__(self, tag_condition: TagCondition):
        """
        Filters WordStates based on the tags of their associated Word.
        Keeps only WordStates where the parent Word matches the tag condition.
        """
        self._tag_condition = tag_condition

    def select(self, word_states: List[WordState]) -> List[WordState]:
        return [
            state for state in word_states
            if self._tag_condition.evaluate(state.get_word().tags)
        ]
