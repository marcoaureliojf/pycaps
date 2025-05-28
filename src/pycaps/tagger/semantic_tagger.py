import re
from typing import Callable, Dict
from .models import Word, Document
from .llm_tagger import LlmTagger

class _SemanticTagger:
    '''
    Register of semantic rules for the word-level tagger.
    The matching words are tagged with the class name of the rule that matched.

    This class implements three types of rules:
     - Regex rules: Use regular expressions to find and tag matching words
     - LLM rules: Use a language model to identify and tag relevant words/phrases
     - Function rules: Use custom functions that analyze each word and its context
       to determine if it should be tagged
    '''

    def __init__(self):
        self._regex_rules: Dict[str, str] = {}
        self._llm_rules: Dict[str, str] = {}
        self._function_rules: Dict[str, Callable[[Document], list[Word]]] = {}
        self._llm_tagger = LlmTagger()

    def add_regex_rule(self, tag: str, pattern: str) -> None:
        """Register a new regex-based rule."""
        self._regex_rules[tag] = pattern

    def add_llm_rule(self, tag: str, topic: str) -> None:
        """Register a new LLM-based rule."""
        self._llm_rules[tag] = topic

    def add_function_rule(self, tag: str, get_words_to_tag: Callable[[Document], list[Word]]) -> None:
        """Register a new function-based rule. The function receives the document and returns a list of words that should be tagged."""
        self._function_rules[tag] = get_words_to_tag

    def tag(self, document: Document) -> None:
        """Apply all registered rules to the document."""
        self._apply_regex_rules(document)
        self._apply_llm_rules(document)
        self._apply_function_rules(document)

    def _apply_regex_rules(self, document: Document) -> None:
        """Apply regex rules to the document."""
        words = document.get_words()
        text = document.get_text()

        for class_name, pattern in self._regex_rules.items():
            matches = re.finditer(pattern, text)
            self._tag_matching_words(words, matches, class_name)

    def _apply_llm_rules(self, document: Document) -> None:
        """
        Apply LLM rules to the document.
        Makes a single call to the LLM with all rules to optimize performance.
        The LLM is expected to return the text with all matching terms tagged using
        XML-like tags for each class name.
        
        Example:
        If we have rules for "emotion" and "finance", the LLM might return:
        "I feel <emotion>happy</emotion> about my <finance>investment</finance>"
        """
        if not self._llm_rules:
            return

        words = document.get_words()
        text = document.get_text()
        
        tagged_text = self._llm_tagger.process(text, self._llm_rules)
        
        for class_name in self._llm_rules.keys():
            pattern = f'<{class_name}>(.*?)</{class_name}>'
            matches = re.finditer(pattern, tagged_text)
            self._tag_matching_words(words, matches, class_name)

    def _apply_function_rules(self, document: Document) -> None:
        """Apply function-based rules to the document."""

        for class_name, get_words_to_tag in self._function_rules.items():
            for word in get_words_to_tag(document):
                word.tags.append(class_name)

    def _tag_matching_words(self, words: list[Word], matches, class_name: str) -> None:
        """Tag words that match the found patterns."""
        for match in matches:
            start_pos = match.start()
            end_pos = match.end()
            
            current_pos = 0
            for word in words:
                word_start = current_pos
                word_end = current_pos + len(word.text) + 1  # +1 for space
                
                if self._word_overlaps_with_match(word_start, word_end, start_pos, end_pos):
                    word.tags.append(class_name)
                
                current_pos = word_end

    def _word_overlaps_with_match(self, word_start: int, word_end: int, 
                                 match_start: int, match_end: int) -> bool:
        """Determine if a word overlaps with a found match."""
        return (word_start <= match_start < word_end) or \
               (word_start < match_end <= word_end) or \
               (match_start <= word_start and match_end >= word_end)

_default_tagger = _SemanticTagger()
_default_tagger.add_function_rule("first-word-in-document", lambda document: [document.segments[0].lines[0].words[0]])
_default_tagger.add_function_rule("first-word-in-segment", lambda document: [segment.lines[0].words[0] for segment in document.segments])
_default_tagger.add_function_rule("first-word-in-line", lambda document: [line.words[0] for line in document.get_lines()])
_default_tagger.add_function_rule("last-word-in-document", lambda document: [document.segments[-1].lines[-1].words[-1]])
_default_tagger.add_function_rule("last-word-in-segment", lambda document: [segment.lines[-1].words[-1] for segment in document.segments])
_default_tagger.add_function_rule("last-word-in-line", lambda document: [line.words[-1] for line in document.get_lines()])

_default_tagger.add_function_rule("first-line-in-document", lambda document: document.segments[0].lines[0].words)
_default_tagger.add_function_rule("first-line-in-segment", lambda document: [word for segment in document.segments for word in segment.lines[0].words])
_default_tagger.add_function_rule("last-line-in-document", lambda document: document.segments[-1].lines[-1].words)
_default_tagger.add_function_rule("last-line-in-segment", lambda document: [word for segment in document.segments for word in segment.lines[-1].words])

_default_tagger.add_function_rule("first-segment-in-document", lambda document: document.segments[0].get_words())
_default_tagger.add_function_rule("last-segment-in-document", lambda document: document.segments[-1].get_words())

def get_default_tagger() -> _SemanticTagger:
    return _default_tagger
