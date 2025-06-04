import os
from .caps_pipeline import CapsPipeline
from pycaps.layout import SubtitleLayoutOptions, LineSplitter, LayoutUpdater, PositionsCalculator
from pycaps.transcriber import AudioTranscriber, BaseSegmentRewriter, WhisperAudioTranscriber
from typing import Dict, Any, Optional
from pycaps.animation import Animation, ElementAnimator
from pycaps.common import ElementType, EventType, VideoResolution
from pycaps.tag import TagCondition, SemanticTagger
from pycaps.effect import Effect

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
    
    def with_css(self, css_file_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(css_file_path):
            raise ValueError(f"CSS file not found: {css_file_path}")
        css_content = open(css_file_path, "r").read()
        self._caps_pipeline._renderer.set_custom_css(css_content)
        return self
    
    def with_whisper_config(self, language: Optional[str] = None, model_size: str = "base") -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = WhisperAudioTranscriber(model_size=model_size, language=language)
        return self
    
    def with_custom_audio_transcriber(self, audio_transcriber: AudioTranscriber) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = audio_transcriber
        return self
    
    def add_segment_rewriter(self, segment_rewriter: BaseSegmentRewriter) -> "CapsPipelineBuilder":
        self._caps_pipeline._segment_rewriters.append(segment_rewriter)
        return self
    
    def with_semantic_tagger(self, semantic_tagger: SemanticTagger) -> "CapsPipelineBuilder":
        self._caps_pipeline._semantic_tagger = semantic_tagger
        return self
    
    def add_animation(self, animation: Animation, when: EventType, what: ElementType, tag_condition: Optional[TagCondition] = None) -> "CapsPipelineBuilder":
        self._caps_pipeline._animators.append(ElementAnimator(animation, when, what, tag_condition)) 
        return self
    
    def add_effect(self, effect: Effect) -> "CapsPipelineBuilder":
        self._caps_pipeline._effects.append(effect)
        return self

    def build(self) -> CapsPipeline:
        if not self._caps_pipeline._input_video_path:
            raise ValueError("Input video path is required")
        pipeline = self._caps_pipeline
        self._caps_pipeline = CapsPipeline()
        return pipeline