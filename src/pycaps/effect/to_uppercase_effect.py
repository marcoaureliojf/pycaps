from .effect import Effect
from pycaps.common import Document, Word
from pycaps.tag import TagCondition
from typing import Optional

class ToUppercaseEffect(Effect):
    def __init__(self, tag_condition: Optional[TagCondition] = None):
        self.tag_condition = tag_condition

    def run(self, document: Document) -> None:
        for word in document.get_words():
            if self.tag_condition and self.tag_condition.evaluate(word.tags):
                word.text = word.text.upper()
