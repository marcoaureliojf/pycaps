from ..tagger.models import Document
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from ..models import RenderedSubtitle

class WordWidthCalculator:
    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer

    def calculate(self, document: Document) -> None:
        for word in document.get_words():
            # we use the default word css class to get the width and height
            # it could cause a issue if the word is then rendered with a different css class that changes the size (font-size, etc)
            word_image: RenderedSubtitle = self._renderer.render(word)
            word.layout.size.width = word_image.width
            word.layout.size.height = word_image.height
