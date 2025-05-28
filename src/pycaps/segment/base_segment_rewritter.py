from abc import ABC, abstractmethod
from ..tagger.models import Document

class BaseSegmentRewritter(ABC):

    @abstractmethod
    def rewrite(self, document: Document) -> None:
        '''
        Transforms the segments of a document, reducing or increasing the amount of words per segment.
        It assumes that the segments have not been splitted into lines yet.
        '''
        pass
