from typing import Optional
from pycaps.ai.gpt import Gpt
from pycaps.ai.llm_apis import TogetherLlm, GroqLlm, OpenRouterLlm
from pycaps.ai.llm import Llm

class LlmProvider:
    _llm: Optional[Llm] = None

    @staticmethod
    def get() -> Llm:
        if LlmProvider._llm is None:
            raise RuntimeError("No LLM provider has been set.")
        return LlmProvider._llm

    @staticmethod
    def set(provider: str, api_key: str):
        if provider == "openai":
            LlmProvider._llm = Gpt()
        elif provider == "together":
            LlmProvider._llm = TogetherLlm(api_key)
        elif provider == "groq":
            LlmProvider._llm = GroqLlm(api_key)
        elif provider == "openrouter":
            LlmProvider._llm = OpenRouterLlm(api_key)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
