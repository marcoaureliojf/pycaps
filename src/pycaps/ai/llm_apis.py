from pycaps.ai.llm import Llm
import requests

class TogetherLlm(Llm):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_message(self, message: str, model: str = "together-default") -> str:
        url = "https://api.together.ai/v1/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "prompt": message}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("output", "")

    def is_enabled(self) -> bool:
        return self.api_key is not None

class GroqLlm(Llm):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_message(self, message: str, model: str = "groq-default") -> str:
        url = "https://api.groq.com/v1/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "prompt": message}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("output", "")

    def is_enabled(self) -> bool:
        return self.api_key is not None

class OpenRouterLlm(Llm):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_message(self, message: str, model: str = "openrouter-default") -> str:
        url = "https://api.openrouter.ai/v1/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "prompt": message}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("output", "")

    def is_enabled(self) -> bool:
        return self.api_key is not None