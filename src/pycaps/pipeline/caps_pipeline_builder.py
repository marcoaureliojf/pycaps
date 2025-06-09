import os
from .caps_pipeline import CapsPipeline
from pycaps.layout import SubtitleLayoutOptions, LineSplitter, LayoutUpdater, PositionsCalculator
from pycaps.transcriber import AudioTranscriber, BaseSegmentSplitter, WhisperAudioTranscriber
from typing import Dict, Any, Optional
from pycaps.animation import Animation, ElementAnimator
from pycaps.common import ElementType, EventType, VideoResolution
from pycaps.tag import TagCondition, SemanticTagger
from pycaps.effect import TextEffect, ClipEffect, SoundEffect

class CapsPipelineBuilder:

    def __init__(self):
        self._caps_pipeline: CapsPipeline = CapsPipeline()
    
    def with_input_video(self, input_video_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._input_video_path = input_video_path
        return self
    
    def with_output_video(self, output_video_path: str) -> "CapsPipelineBuilder":
        if os.path.exists(output_video_path):
            raise ValueError(f"Output video path already exists: {output_video_path}")
        self._caps_pipeline._output_video_path = output_video_path
        return self

    def with_resources(self, resources_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(resources_path):
            raise ValueError(f"Resources path does not exist: {resources_path}")
        if not os.path.isdir(resources_path):
            raise ValueError(f"Resources path is not a directory: {resources_path}")
        self._caps_pipeline._resources_dir = resources_path
        return self
    
    def with_custom_audio_file(self, audio_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._video_generator.set_audio_path(audio_path)
        return self
    
    def with_moviepy_write_options(self, moviepy_write_options: Dict[str, Any]) -> "CapsPipelineBuilder":
        self._caps_pipeline._moviepy_write_options = moviepy_write_options
        return self
    
    def with_fps(self, fps: int) -> "CapsPipelineBuilder":
        if fps < 12 or fps > 60:
            raise ValueError("FPS must be between 12 and 60")
        self._caps_pipeline._moviepy_write_options["fps"] = fps
        return self
    
    def with_video_resolution(self, resolution: VideoResolution) -> "CapsPipelineBuilder":
        self._caps_pipeline._video_generator.set_video_resolution(resolution)
        return self
    
    def with_layout_options(self, layout_options: SubtitleLayoutOptions) -> "CapsPipelineBuilder":
        self._caps_pipeline._line_splitter = LineSplitter(layout_options)
        self._caps_pipeline._layout_updater = LayoutUpdater(layout_options)
        self._caps_pipeline._positions_calculator = PositionsCalculator(layout_options)
        return self
    
    def add_css(self, css_file_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(css_file_path):
            raise ValueError(f"CSS file not found: {css_file_path}")
        css_content = open(css_file_path, "r", encoding="utf-8").read()
        self._caps_pipeline._renderer.append_css(css_content)
        return self
    
    def add_css_content(self, css_content: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._renderer.append_css(css_content)
        return self
    
    def with_whisper_config(self, language: Optional[str] = None, model_size: str = "base") -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = WhisperAudioTranscriber(model_size=model_size, language=language)
        return self
    
    def with_custom_audio_transcriber(self, audio_transcriber: AudioTranscriber) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = audio_transcriber
        return self

    def with_subtitle_data_path(self, subtitle_data_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._subtitle_data_path_for_loading = subtitle_data_path
        return self
    
    def should_save_subtitle_data(self, should_save: bool) -> "CapsPipelineBuilder":
        self._caps_pipeline._should_save_subtitle_data = should_save
        return self
    
    def should_preview_transcription(self, should_preview: bool) -> "CapsPipelineBuilder":
        self._caps_pipeline._should_preview_transcription = should_preview
        return self
    
    def add_segment_splitter(self, segment_splitter: BaseSegmentSplitter) -> "CapsPipelineBuilder":
        self._caps_pipeline._segment_splitters.append(segment_splitter)
        return self
    
    def with_semantic_tagger(self, semantic_tagger: SemanticTagger) -> "CapsPipelineBuilder":
        self._caps_pipeline._semantic_tagger = semantic_tagger
        return self
    
    def add_animation(self, animation: Animation, when: EventType, what: ElementType, tag_condition: Optional[TagCondition] = None) -> "CapsPipelineBuilder":
        self._caps_pipeline._animators.append(ElementAnimator(animation, when, what, tag_condition)) 
        return self
    
    def add_text_effect(self, effect: TextEffect) -> "CapsPipelineBuilder":
        self._caps_pipeline._text_effects.append(effect)
        return self
    
    def add_clip_effect(self, effect: ClipEffect) -> "CapsPipelineBuilder":
        self._caps_pipeline._clip_effects.append(effect)
        return self

    def add_sound_effect(self, effect: SoundEffect) -> "CapsPipelineBuilder":
        self._caps_pipeline._sound_effects.append(effect)
        return self

    def build(self, preview_time: Optional[tuple[float, float]] = None) -> CapsPipeline:
        if not self._caps_pipeline._input_video_path:
            raise ValueError("Input video path is required")
        if preview_time:
            self.with_video_resolution(VideoResolution._360P)
            self.with_fps(20)
            self.should_save_subtitle_data(False)
            self._caps_pipeline._video_generator.set_fragment_time(preview_time)
        
        pipeline = self._caps_pipeline
        self._caps_pipeline = CapsPipeline()
        return pipeline