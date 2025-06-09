import time
import os
from pycaps.transcriber import AudioTranscriber, WhisperAudioTranscriber, BaseSegmentSplitter
from pycaps.renderer import CssSubtitleRenderer
from pycaps.video import SubtitleClipsGenerator, VideoGenerator
from pycaps.layout import WordWidthCalculator, PositionsCalculator, LineSplitter, LayoutUpdater
from pycaps.tag import SemanticTagger
from pycaps.animation import ElementAnimator
from pycaps.layout import SubtitleLayoutOptions
from pycaps.effect import TextEffect, ClipEffect, SoundEffect
from pycaps.common import Document
from typing import Optional, List, Dict, Any
from pathlib import Path
from .subtitle_data_service import SubtitleDataService
from moviepy.editor import VideoClip

class CapsPipeline:
    def __init__(self):
        self._transcriber: AudioTranscriber = WhisperAudioTranscriber()
        self._renderer: CssSubtitleRenderer = CssSubtitleRenderer()
        self._clips_generator: SubtitleClipsGenerator = SubtitleClipsGenerator(self._renderer)
        self._word_width_calculator: WordWidthCalculator = WordWidthCalculator(self._renderer)
        self._semantic_tagger: SemanticTagger = SemanticTagger()
        self._video_generator: VideoGenerator = VideoGenerator()
        self._segment_splitters: list[BaseSegmentSplitter] = []
        self._animators: List[ElementAnimator] = []
        self._text_effects: List[TextEffect] = []
        self._clip_effects: List[ClipEffect] = []
        self._sound_effects: List[SoundEffect] = []
        self._should_save_subtitle_data: bool = True
        self._subtitle_data_path_for_loading: Optional[str] = None

        layout_options = SubtitleLayoutOptions()
        self._positions_calculator: PositionsCalculator = PositionsCalculator(layout_options)
        self._line_splitter: LineSplitter = LineSplitter(layout_options)
        self._layout_updater: LayoutUpdater = LayoutUpdater(layout_options)

        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None
        self._resources_dir: Optional[str] = None
        self._moviepy_write_options: Dict[str, Any] = {}

    def run(self) -> None:
        """
        Runs the pipeline to process a video.
        """
        start_time = time.time()
        try:
            print(f"Starting caps pipeline execution: {self._input_video_path}")
            video_extension = os.path.splitext(self._input_video_path)[1]
            self._output_video_path = f"output_{time.strftime('%Y%m%d_%H%M%S')}{video_extension}" if self._output_video_path is None else self._output_video_path
            self._video_generator.set_moviepy_write_options(self._moviepy_write_options)
            self._video_generator.start(self._input_video_path, self._output_video_path)
            video_clip = self._video_generator.get_video_clip()
            document = self._generate_subtitle_data(video_clip)

            if self._should_save_subtitle_data and self._subtitle_data_path_for_loading is None:
                print("Saving subtitle data...")
                subtitle_data_path = self._output_video_path.replace(os.path.splitext(self._input_video_path)[1], ".json")
                subtitle_data_service = SubtitleDataService(subtitle_data_path)
                subtitle_data_service.save(document)

            print("Generating subtitle clips...")
            self._clips_generator.generate(document)

            print("Updating elements max sizes...")
            self._layout_updater.update_max_sizes(document)

            print("Calculating words positions...")
            self._positions_calculator.calculate(document, video_clip.w, video_clip.h)

            print("Updating elements max positions...")
            self._layout_updater.update_max_positions(document)

            print("Applying clip effects...")
            clip_effects_start_time = time.time()
            for effect in self._clip_effects:
                effect.set_renderer(self._renderer)
                effect.run(document)
            print(f"Clip effects time: {time.time() - clip_effects_start_time} seconds")

            print("Applying sound effects...")
            for effect in self._sound_effects:
                effect.run(document)

            print("Running animations...")
            animations_start_time = time.time()
            for animator in self._animators:
                animator.run(document)
            print(f"Animations time: {time.time() - animations_start_time} seconds")

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
            print(f"Total time: {time.time() - start_time} seconds")

    # TODO: improve preview: we should register all the existing css classes (and keys),
    # and then allow viewing a word example with any of those classes
    # for that, we could generate a simple preview page with a dropdown and a container for the word.
    def preview(self) -> None:
        self._renderer.preview()
        input("Press [ENTER] to finish preview...")

    def _generate_subtitle_data(self, video_clip: VideoClip) -> Document:
        if self._subtitle_data_path_for_loading:
            print("Loading subtitle data...")
            subtitle_data_service = SubtitleDataService(self._subtitle_data_path_for_loading)
            document = subtitle_data_service.load()
            
            print(f"Opening renderer for video dimensions: {video_clip.w}x{video_clip.h}")
            resources_dir = Path(self._resources_dir) if self._resources_dir else None
            self._renderer.open(video_width=video_clip.w, video_height=video_clip.h, resources_dir=resources_dir)
            return document
        
        print("Transcribing audio...")
        document = self._transcriber.transcribe(self._video_generator.get_audio_path())
        if len(document.segments) == 0:
            raise RuntimeError("Transcription returned no segments. Subtitles will not be added.")
        
        print("Running segments splitters...")
        for splitter in self._segment_splitters:
            splitter.split(document)

        print(f"Opening renderer for video dimensions: {video_clip.w}x{video_clip.h}")
        resources_dir = Path(self._resources_dir) if self._resources_dir else None
        self._renderer.open(video_width=video_clip.w, video_height=video_clip.h, resources_dir=resources_dir)

        print("Calculating words widths...")
        # Keep in mind this is an approximation, since the words/lines do not have the tags yet
        # We use this to split into lines, but after adding the tags the words witdhs can change,
        # and therefore the max_width per line could be exceeded.
        self._word_width_calculator.calculate(document)

        print("Splitting segments into lines...")
        self._line_splitter.split_into_lines(document, video_clip.w)

        print("Tagging words with semantic information...")
        self._semantic_tagger.tag(document)

        print("Applying text effects...")
        for effect in self._text_effects:
            effect.run(document)

        return document