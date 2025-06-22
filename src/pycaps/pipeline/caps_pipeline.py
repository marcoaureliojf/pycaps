import time
import os
from pycaps.transcriber import AudioTranscriber, WhisperAudioTranscriber, BaseSegmentSplitter
from pycaps.renderer import CssSubtitleRenderer
from pycaps.video import SubtitleClipsGenerator, VideoGenerator
from pycaps.layout import WordWidthCalculator, PositionsCalculator, LineSplitter, LayoutUpdater
from pycaps.tag import SemanticTagger, StructureTagger
from pycaps.animation import ElementAnimator
from pycaps.layout import SubtitleLayoutOptions
from pycaps.effect import TextEffect, ClipEffect, SoundEffect
from pycaps.common import Document, CacheStrategy
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from .subtitle_data_service import SubtitleDataService
from pycaps.transcriber import TranscriptionEditor
from pycaps.logger import logger, ProcessLogger
from pycaps.utils import time_utils

class CapsPipeline:
    def __init__(self):
        self._transcriber: AudioTranscriber = WhisperAudioTranscriber()
        self._renderer: CssSubtitleRenderer = CssSubtitleRenderer()
        self._clips_generator: SubtitleClipsGenerator = SubtitleClipsGenerator(self._renderer)
        self._word_width_calculator: WordWidthCalculator = WordWidthCalculator(self._renderer)
        self._semantic_tagger: SemanticTagger = SemanticTagger()
        self._structure_tagger: StructureTagger = StructureTagger()
        self._video_generator: VideoGenerator = VideoGenerator()
        self._segment_splitters: list[BaseSegmentSplitter] = []
        self._animators: List[ElementAnimator] = []
        self._text_effects: List[TextEffect] = []
        self._clip_effects: List[ClipEffect] = []
        self._sound_effects: List[SoundEffect] = []
        self._should_save_subtitle_data: bool = True
        self._subtitle_data_path_for_loading: Optional[str] = None
        self._should_preview_transcription: bool = False

        self._layout_options = SubtitleLayoutOptions()
        self._positions_calculator: PositionsCalculator = PositionsCalculator(self._layout_options)
        self._line_splitter: LineSplitter = LineSplitter(self._layout_options)
        self._layout_updater: LayoutUpdater = LayoutUpdater(self._layout_options)

        self._preview_time: Optional[Tuple[float, float]] = None
        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None
        self._resources_dir: Optional[str] = None
        self._cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE
        self._process_logger: ProcessLogger

    def run(self) -> None:
        """
        Runs the pipeline to process a video.
        """
        start_time = time.time()
        try:
            self._process_logger: ProcessLogger = ProcessLogger(6 if self._subtitle_data_path_for_loading else 10)
            self._process_logger.step(f"Starting caps pipeline execution: {self._input_video_path}")
            video_extension = os.path.splitext(self._input_video_path)[1]
            self._output_video_path = f"output_{time.strftime('%Y%m%d_%H%M%S')}{video_extension}" if self._output_video_path is None else self._output_video_path
            if self._preview_time:
                self._video_generator.set_fragment_time(self._preview_time)
            self._video_generator.start(self._input_video_path, self._output_video_path)
            video_width, video_height = self._video_generator.get_video_size()
            document = self._generate_subtitle_data(video_width, video_height)
            
            if self._should_preview_transcription:
                document = TranscriptionEditor().run(document)

                # the transcription editor could have changed the structure, so we need to clear and add these tags again.
                self._structure_tagger.clear(document)
                self._structure_tagger.tag(document)

            if self._should_save_subtitle_data:
                logger().debug("Saving subtitle data...")
                subtitle_data_path = self._output_video_path.replace(os.path.splitext(self._input_video_path)[1], ".json")
                subtitle_data_service = SubtitleDataService(subtitle_data_path)
                subtitle_data_service.save(document)

            self._process_logger.step("Generating subtitle clips...")
            self._clips_generator.generate(document)

            logger().debug("Updating elements max sizes...")
            self._layout_updater.update_max_sizes(document)

            logger().debug("Calculating words positions...")
            self._positions_calculator.calculate(document, video_width, video_height)

            logger().debug("Updating elements max positions...")
            self._layout_updater.update_max_positions(document)

            self._process_logger.step("Applying clip effects...")
            for effect in self._clip_effects:
                effect.set_renderer(self._renderer)
                effect.run(document)

            self._process_logger.step("Applying sound effects...")
            for effect in self._sound_effects:
                effect.run(document)

            self._process_logger.step("Running animations...")
            for animator in self._animators:
                animator.run(document)

            self._process_logger.step("Generating final video...")
            self._video_generator.generate(document)

            logger().info("The video has been rendered successfully!")
        except Exception as e:
            logger().error(f"An error occurred during caps pipeline execution: {e}")
            raise e
        finally:
            logger().debug("Cleaning up resources...")
            self._video_generator.close()
            self._renderer.close()
            logger().debug("Cleanup finished.")
            logger().debug(f"Total time: {time.time() - start_time} seconds")

    def _generate_subtitle_data(self, video_width: int, video_height: int) -> Document:
        if self._subtitle_data_path_for_loading:
            logger().debug("Loading subtitle data...")
            subtitle_data_service = SubtitleDataService(self._subtitle_data_path_for_loading)
            document = subtitle_data_service.load()
            
            logger().debug(f"Opening renderer for video dimensions: {video_width}x{video_height}")
            resources_dir = Path(self._resources_dir) if self._resources_dir else None
            self._renderer.open(video_width, video_height, resources_dir, self._cache_strategy)

            self._cut_document_for_preview_time(document)
            return document
        
        self._process_logger.step("Transcribing audio...")
        document = self._transcriber.transcribe(self._video_generator.get_audio_path())
        if len(document.segments) == 0:
            raise RuntimeError("Transcription returned no segments. Subtitles will not be added.")
        
        logger().debug("Running segments splitters...")
        for splitter in self._segment_splitters:
            splitter.split(document)

        logger().debug(f"Opening renderer for video dimensions: {video_width}x{video_height}")
        resources_dir = Path(self._resources_dir) if self._resources_dir else None
        self._renderer.open(video_width, video_height, resources_dir, self._cache_strategy)

        self._process_logger.step("Calculating layout...")
        logger().debug("Calculating words widths...")
        # Keep in mind this is an approximation, since the words/lines do not have the tags yet
        # We use this to split into lines, but after adding the tags the words witdhs can change,
        # and therefore the max_width per line could be exceeded.
        self._word_width_calculator.calculate(document)

        logger().debug("Splitting segments into lines...")
        self._line_splitter.split_into_lines(document, video_width)

        self._process_logger.step("Running taggers...")
        self._structure_tagger.tag(document)
        self._semantic_tagger.tag(document)

        self._process_logger.step("Applying text effects...")
        for effect in self._text_effects:
            effect.run(document)

        return document

    def _cut_document_for_preview_time(self, document: Document):
        if not self._preview_time:
            return
        is_in_preview_time = lambda e: time_utils.times_intersect(self._preview_time[0], self._preview_time[1], e.time.start, e.time.end)
        for segment in document.segments[:]:
            if not is_in_preview_time(segment):
                document.segments.remove(segment)
                continue
            for line in segment.lines[:]:
                if not is_in_preview_time(line):
                    segment.lines.remove(line)
                    continue
                for word in line.words[:]:
                    if not is_in_preview_time(word):
                        line.words.remove(word)
