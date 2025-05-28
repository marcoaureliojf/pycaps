from ..transcriber.base_transcriber import AudioTranscriber
from typing import Optional
from ..transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from ..video.subtitle_clips_generator import SubtitleClipsGenerator
from ..video.video_generator import VideoGenerator
from ..layout.word_width_calculator import WordWidthCalculator
from ..layout.layout_calculator import LayoutCalculator
from ..tagger.semantic_tagger import get_default_tagger
from ..models import SubtitleLayoutOptions

class CapsPipeline:
    def __init__(self):
        self._transcriber: AudioTranscriber = WhisperAudioTranscriber()
        self._renderer: CssSubtitleRenderer = CssSubtitleRenderer()
        self._clips_generator: SubtitleClipsGenerator = SubtitleClipsGenerator(self._renderer)
        self._word_width_calculator: WordWidthCalculator = WordWidthCalculator(self._renderer)
        self._layout_calculator: LayoutCalculator = LayoutCalculator(SubtitleLayoutOptions())
        self._semantic_tagger = get_default_tagger()
        self._video_generator: VideoGenerator = VideoGenerator()

        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None

    def run(self) -> None:
        """
        Runs the pipeline to process a video.
        """
        try:
            print(f"Starting caps pipeline execution: {self._input_video_path}")
            self._video_generator.start(self._input_video_path, self._output_video_path)
            video_clip = self._video_generator.get_video_clip()

            print("Transcribing audio...")
            document = self._transcriber.transcribe(self._video_generator.get_audio_path())
            if len(document.segments) == 0:
                raise RuntimeError("Transcription returned no segments. Subtitles will not be added.")

            print(f"Opening renderer for video dimensions: {video_clip.w}x{video_clip.h}")
            self._renderer.open(video_width=video_clip.w, video_height=video_clip.h)

            print("Calculating word widths...")
            self._word_width_calculator.calculate(document)

            print("Calculating layout for each segment...")
            self._layout_calculator.calculate(document, video_clip.w, video_clip.h)

            print("Tagging words with semantic information...")
            self._semantic_tagger.tag(document)

            print("Generating subtitle clips...")
            self._clips_generator.generate(document)

            print("Generating final video...")
            self._video_generator.generate(document)

            print("Video processing successful!")
        except Exception as e:
            print(f"An error occurred during caps pipeline execution: {e}")
            raise e
        finally:
            print("Cleaning up resources...")
            self._video_generator.close()
            self._renderer.close()
            print("Cleanup finished.") 
