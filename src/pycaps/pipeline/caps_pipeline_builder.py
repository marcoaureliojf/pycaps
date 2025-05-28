from .caps_pipeline import CapsPipeline
from ..models import SubtitleLayoutOptions
from ..layout.layout_calculator import LayoutCalculator
from ..transcriber.base_transcriber import AudioTranscriber
from typing import Dict, Any
from ..segment import BaseSegmentRewritter
import os
from ..animator.element_animator import ElementAnimator

class CapsPipelineBuilder:

    def __init__(self):
        self._caps_pipeline: CapsPipeline = CapsPipeline()
    
    def with_input_video(self, input_video_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._input_video_path = input_video_path
        return self
    
    def with_output_video(self, output_video_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._output_video_path = output_video_path
        return self
    
    def with_custom_audio_file(self, audio_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._audio_path = audio_path
        return self
    
    def with_moviepy_write_options(self, moviepy_write_options: Dict[str, Any]) -> "CapsPipelineBuilder":
        self._caps_pipeline._moviepy_write_options = moviepy_write_options
        return self
    
    def with_layout_options(self, layout_options: SubtitleLayoutOptions) -> "CapsPipelineBuilder":
        self._caps_pipeline._layout_calculator = LayoutCalculator(layout_options)
        return self
    
    def with_css(self, css_file_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(css_file_path):
            raise ValueError(f"CSS file not found: {css_file_path}")
        css_content = open(css_file_path, "r").read()
        self._caps_pipeline._renderer.set_custom_css(css_content)
        return self
    
    def with_audio_transcriber(self, audio_transcriber: AudioTranscriber) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = audio_transcriber
        return self
    
    def add_segment_rewritter(self, segment_rewritter: BaseSegmentRewritter) -> "CapsPipelineBuilder":
        self._caps_pipeline._segment_rewritters.append(segment_rewritter)
        return self
    
    def add_animator(self, animator: ElementAnimator) -> "CapsPipelineBuilder":
        self._caps_pipeline._animators.append(animator)
        return self

    def build(self) -> CapsPipeline:
        if not self._caps_pipeline._input_video_path:
            raise ValueError("Input video path is required")
        if not self._caps_pipeline._output_video_path:
            raise ValueError("Output video path is required")
        return self._caps_pipeline
