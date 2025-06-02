from ..element import ElementType
from ..tagger.models import WordClip
from abc import ABC, abstractmethod

class Animation(ABC):
    def __init__(self, duration: float, delay: float = 0.0) -> None:
        self._duration: float = duration
        self._delay: float = delay

    @abstractmethod
    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        pass
