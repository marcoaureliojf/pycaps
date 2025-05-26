from .base_transcriber import AudioTranscriber
from typing import List, Optional
from ..models import TranscriptionSegment, WordData
import whisper

class WhisperAudioTranscriber(AudioTranscriber):
    def __init__(self, model_size: str = "base", language: Optional[str] = None):
        """
        Transcribes audio using OpenAI's Whisper model.

        Args:
            model_size: Size of the Whisper model to use (e.g., "tiny", "base", "small", "medium", "large").
            language: Language of the audio for transcription (e.g., "en", "es").
        """
        self.model_size = model_size
        self.language = language
        try:
            self.model = whisper.load_model(self.model_size)
        except Exception as e:
            raise RuntimeError(
                f"Error loading Whisper model (size: {model_size}): {e}\n" 
                f"Ensure Whisper is installed and models are available (or can be downloaded)."
            )

    def transcribe(self, audio_path: str) -> List[TranscriptionSegment]:
        """
        Transcribes the audio file and returns segments with timestamps.
        """
        print(f"Transcribing audio with Whisper (model: {self.model_size}, language: {self.language}): {audio_path}")
        try:
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                language=self.language
            )
        except Exception as e:
            print(f"Error during Whisper transcription: {e}")
            return [] # Return empty list on transcription error

        processed_segments: List[TranscriptionSegment] = []
        if "segments" not in result or not result["segments"]:
            print("Warning: Whisper returned no segments in the transcription.")
            return []

        for segment_info in result["segments"]:
            word_timings: List[WordData] = []
            if not "words" in segment_info or not isinstance(segment_info["words"], list):
                print(f"Segment '{segment_info['text']}' has no detailed word data.")
                continue

            for word_entry in segment_info["words"]:
                # Ensure 'word' is a string, sometimes Whisper might return non-string for certain symbols.
                word_text = str(word_entry["word"]).strip()
                if not word_text: # Skip empty words if any
                    continue
                word_timings.append(WordData(
                    text=word_text,
                    start=float(word_entry["start"]),
                    end=float(word_entry["end"])
                ))
            
            processed_segments.append(TranscriptionSegment(
                text=str(segment_info["text"]).strip(),
                start=float(segment_info["start"]),
                end=float(segment_info["end"]),
                words=word_timings
            ))
        
        if not processed_segments:
            print("Warning: No valid segments were processed from Whisper's transcription.")

        return processed_segments 
