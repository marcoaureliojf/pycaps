from .json_config_loader import JsonConfigLoader
import importlib.resources as resources
from typing import overload, Literal
from pycaps.pipeline import CapsPipeline, CapsPipelineBuilder

class TemplateLoader:
    DEFAULT_TEMPLATE_NAME = "default"
    TEMPLATE_FOLDER_NAME = "pycaps.templates"
    CONFIG_FILE_NAME = "config.json"

    def __init__(self, input_video_path: str, template_name: str = DEFAULT_TEMPLATE_NAME):
        self._input_video_path = input_video_path
        self._template = template_name

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
        builder.with_input_video(self._input_video_path)
        if should_build_pipeline:
            return builder.build()
        return builder

