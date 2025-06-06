from pycaps.common import Document, ElementState
from pycaps.renderer import CssSubtitleRenderer

class WordWidthCalculator:
    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer

    def calculate(self, document: Document) -> None:
        all_word_states = ElementState.get_all_valid_states_combinations()
        for word in document.get_words():
            max_width = 0
            max_height = 0
            for states in all_word_states:
                size = self._renderer.get_word_size(word, states)
                if not size:
                    continue
                max_width = max(max_width, size[0])
                max_height = max(max_height, size[1])
            word.max_layout.size.width = max_width
            word.max_layout.size.height = max_height
