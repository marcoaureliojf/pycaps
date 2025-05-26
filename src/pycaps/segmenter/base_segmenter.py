from abc import ABC, abstractmethod
from typing import List
from ..models import TranscriptionSegment

class BaseSegmenter(ABC):
    @abstractmethod
    def map(self, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        '''
        Maps the segments to a new list of segments.
        '''
        pass
