from typing import Dict
from pycaps.common import Tag
from pycaps.api import ApiKeyService, PycapsTaggerApi
from .external_llm_tagger import ExternalLlmTagger
from pycaps.ai import LlmProvider
from pycaps.logger import logger

class AiTagger:
    def process(self, text: str, rules: Dict[Tag, str]) -> str:
        llm = LlmProvider.get()
        if not llm.is_enabled():
            logger().warning("LLM is not enabled. Ignoring AI tagging rules.")
            return text

        return llm.send_message(self._build_prompt(text, rules))
