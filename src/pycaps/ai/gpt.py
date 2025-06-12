from pycaps.ai.llm import Llm
import os

class Gpt(Llm):

    def __init__(self):
        self._client = None

    def send_message(self, prompt: str, model: str = "gpt-4.1-mini") -> str:
        return self._get_client().responses.create(model=model, input=prompt).output_text

    def _get_client(self):
        from openai import OpenAI

        if self._client:
            return self._client

        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # TODO: allow inject key
        return self._client
