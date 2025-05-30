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
            for state in all_word_states:
                word_image: RenderedSubtitle = self._renderer.render(word, state)
                max_width = max(max_width, word_image.width)
                max_height = max(max_height, word_image.height)
            word.layout.size.width = max_width
            word.layout.size.height = max_height

    def update_widths_using_moviepy_clips(self, document: Document) -> None:
        for word in document.get_words():
            max_width = 0
            max_height = 0
            for clip in word.clips:
                max_width = max(max_width, clip.image_clip.size[0])
                max_height = max(max_height, clip.image_clip.size[1])
            word.layout.size.width = max_width
            word.layout.size.height = max_height
