import time
import os
from pycaps.transcriber import AudioTranscriber, WhisperAudioTranscriber, BaseSegmentRewriter
from pycaps.renderer import CssSubtitleRenderer
from pycaps.video import SubtitleClipsGenerator, VideoGenerator
from pycaps.layout import WordWidthCalculator, PositionsCalculator, LineSplitter, LayoutUpdater
from pycaps.tag import SemanticTagger
from pycaps.animation import ElementAnimator
from pycaps.layout import SubtitleLayoutOptions
from pycaps.effect import Effect
from typing import Optional, List

class CapsPipeline:
    def __init__(self):
        self._transcriber: AudioTranscriber = WhisperAudioTranscriber()
        self._renderer: CssSubtitleRenderer = CssSubtitleRenderer()
        self._clips_generator: SubtitleClipsGenerator = SubtitleClipsGenerator(self._renderer)
        self._word_width_calculator: WordWidthCalculator = WordWidthCalculator(self._renderer)
        self._semantic_tagger: SemanticTagger = SemanticTagger()
        self._video_generator: VideoGenerator = VideoGenerator()
        self._segment_rewriters: list[BaseSegmentRewriter] = []
        self._animators: List[ElementAnimator] = []
        self._effects: List[Effect] = []

        layout_options = SubtitleLayoutOptions()
        self._positions_calculator: PositionsCalculator = PositionsCalculator(layout_options)
        self._line_splitter: LineSplitter = LineSplitter(layout_options)
        self._layout_updater: LayoutUpdater = LayoutUpdater(layout_options)

        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None

    def run(self) -> None:
        """
        Runs the pipeline to process a video.
        """
        try:
            print(f"Starting caps pipeline execution: {self._input_video_path}")
            video_extension = os.path.splitext(self._input_video_path)[1]
            self._output_video_path = f"output_{time.strftime('%Y%m%d_%H%M%S')}{video_extension}" if self._output_video_path is None else self._output_video_path
            self._video_generator.start(self._input_video_path, self._output_video_path)
            video_clip = self._video_generator.get_video_clip()

            print("Transcribing audio...")
            document = self._transcriber.transcribe(self._video_generator.get_audio_path())
            if len(document.segments) == 0:
                raise RuntimeError("Transcription returned no segments. Subtitles will not be added.")
            
            print("Running segments rewriters...")
            for rewriter in self._segment_rewriters:
                rewriter.rewrite(document)

            print(f"Opening renderer for video dimensions: {video_clip.w}x{video_clip.h}")
            self._renderer.open(video_width=video_clip.w, video_height=video_clip.h)

            print("Calculating words widths...")
            self._word_width_calculator.calculate(document)

            print("Splitting segments into lines...")
            self._line_splitter.split_into_lines(document, video_clip.w)

            print("Tagging words with semantic information...")
            self._semantic_tagger.tag(document)

            print("Applying effects...")
            for effect in self._effects:
                effect.run(document)

            print("Generating subtitle clips...")
            self._clips_generator.generate(document)

            print("Updating elements max sizes...")
            self._layout_updater.update_max_sizes(document)

            print("Calculating words positions...")
            self._positions_calculator.calculate(document, video_clip.w, video_clip.h)

            print("Updating elements max positions...")
            self._layout_updater.update_max_positions(document)

            print("Running animations...")
            for animator in self._animators:
                animator.run(document)

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

    # TODO: improve preview: we should register all the existing css classes (and keys),
    # and then allow viewing a word example with any of those classes
    # for that, we could generate a simple preview page with a dropdown and a container for the word.
    def preview(self) -> None:
        self._renderer.preview()
        input("Press [ENTER] to finish preview...")