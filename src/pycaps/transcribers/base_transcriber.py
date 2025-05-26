from abc import ABC, abstractmethod
from typing import List, Any
from ..models import TranscriptionSegment

class AudioTranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> List[TranscriptionSegment]:
        """
        Transcribes an audio file and returns a list of segments.

        Each segment contains information about the text, start/end times,
        and optionally, word-by-word timing information.

        Args:
            audio_path: Path to the audio file to be transcribed.

        Returns:
            A list of TranscriptionSegment objects.
        """
        pass 