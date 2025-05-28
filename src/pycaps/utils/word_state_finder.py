from ..tagger.models import Document, WordState
from typing import List

class WordStateFinder:
    
    @staticmethod
    def find_word_states_matching_tag(document: Document, tag: str) -> List[WordState]:
        return [word_state for word_state in document.get_word_states() if word_state.match_tag(tag)]

    @staticmethod
    def find_word_states_matching_all_tags(document: Document, tags: List[str]) -> List[WordState]:
        return [word_state for word_state in document.get_word_states() if word_state.match_all_tags(tags)]
