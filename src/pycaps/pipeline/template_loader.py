from .json_config_loader import JsonConfigLoader
import importlib.resources as resources
from typing import overload, Literal, Optional
from pycaps.pipeline import CapsPipeline, CapsPipelineBuilder

class TemplateLoader:
    DEFAULT_TEMPLATE_NAME = "default"
    TEMPLATE_FOLDER_NAME = "pycaps.templates"
    CONFIG_FILE_NAME = "config.json"

    def __init__(self, template_name: str = DEFAULT_TEMPLATE_NAME):
        self._template: str = template_name
        self._input_video_path: Optional[str] = None

    def with_input_video(self, input_video_path: str) -> "TemplateLoader":
        self._input_video_path = input_video_path
        return self

    @overload
    def load(self, should_build_pipeline: Literal[True] = True) -> CapsPipeline:
        ...
    @overload
    def load(self, should_build_pipeline: Literal[False]) -> CapsPipelineBuilder:
        ...
    def load(self, should_build_pipeline: bool = True) -> CapsPipeline | CapsPipelineBuilder:
        template_path = resources.files(self.TEMPLATE_FOLDER_NAME).joinpath(self._template)
        config_path = template_path.joinpath(self.CONFIG_FILE_NAME)
        json_config_loader = JsonConfigLoader(config_path.as_posix())
        builder = json_config_loader.load(False)
        if self._input_video_path:
            builder.with_input_video(self._input_video_path)
        if should_build_pipeline:
            return builder.build()
        return builder
    
    @staticmethod
    def list_templates() -> list[str]:
        template_path = resources.files(TemplateLoader.TEMPLATE_FOLDER_NAME)
        return [p.name for p in template_path.iterdir() if p.is_dir()]

