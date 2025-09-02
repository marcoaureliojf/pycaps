from pycaps.ai.llm import Llm
import requests

class TogetherLlm(Llm):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_message(self, message: str, model: str = "together-default") -> str:
        url = "https://api.together.xyz/v1"
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

    def send_message(self, message: str, model: str = "meta-llama/llama-guard-4-12b") -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": 1,
            "max_completion_tokens": 1024,
            "top_p": 1,
            "stream": False
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def is_enabled(self) -> bool:
        return self.api_key is not None

class OpenRouterLlm(Llm):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_message(self, message: str, model: str = "openrouter-default") -> str:
        url = "https://openrouter.ai/api/v1"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "prompt": message}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("output", "")

    def is_enabled(self) -> bool:
        return self.api_key is not None