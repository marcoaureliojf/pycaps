from ..tagger.models import Document
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from ..models import RenderedSubtitle
from ..tagger.models import ElementState

class WordWidthCalculator:
    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer

    def calculate(self, document: Document) -> None:
        all_word_states = ElementState.get_all_valid_states_combinations()
        for word in document.get_words():
            max_width = 0
            max_height = 0
            for states in all_word_states:
                word_image: RenderedSubtitle = self._renderer.render(word, states)
                max_width = max(max_width, word_image.width)
                max_height = max(max_height, word_image.height)
            word.max_layout.size.width = max_width
            word.max_layout.size.height = max_height
