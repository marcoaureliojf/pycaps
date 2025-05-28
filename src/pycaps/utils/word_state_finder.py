from ..tagger.models import Document, WordState
from ..tag.tag_condition import TagCondition
from typing import List

class WordStateFinder:

    @staticmethod
    def find_word_states_matching_tag_condition(document: Document, tag_condition: TagCondition) -> List[WordState]:
        return [state for state in document.get_word_states() if tag_condition.evaluate([state.tag] + list(state.get_word().tags))]
