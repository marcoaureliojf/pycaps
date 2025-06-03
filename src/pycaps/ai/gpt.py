from openai import OpenAI
from pycaps.ai.llm import Llm
import os

class Gpt(Llm):
    def __init__(self):
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # TODO: allow inject key

    def send_message(self, prompt: str, model: str = "gpt-4.1-mini") -> str:
        return self._client.responses.create(model=model, input=prompt).output_text
