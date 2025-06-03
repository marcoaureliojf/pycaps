from .base_transcriber import AudioTranscriber
from typing import Optional
from pycaps.common import Document, Segment, Line, Word, TimeFragment
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

    def transcribe(self, audio_path: str) -> Document:
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
            return Document()

        if "segments" not in result or not result["segments"]:
            print("Warning: Whisper returned no segments in the transcription.")
            return Document()

        document = Document()
        for segment_info in result["segments"]:
            segment_time = TimeFragment(start=float(segment_info["start"]), end=float(segment_info["end"]))
            segment = Segment(time=segment_time)
            line = Line(time=segment_time)
            segment.lines.add(line)

            if not "words" in segment_info or not isinstance(segment_info["words"], list):
                print(f"Segment '{segment_info['text']}' has no detailed word data.")
                continue

            for word_entry in segment_info["words"]:
                # Ensure 'word' is a string, sometimes Whisper might return non-string for certain symbols.
                word_text = str(word_entry["word"]).strip()
                if not word_text:
                    continue

                word_time = TimeFragment(start=float(word_entry["start"]), end=float(word_entry["end"]))
                word = Word(text=word_text, time=word_time)
                line.words.add(word) # so far is everything in one single line (we split it in next steps of the pipeline)

            document.segments.add(segment)
        
        if not document.segments:
            print("Warning: No valid segments were processed from Whisper's transcription.")

        return document 
