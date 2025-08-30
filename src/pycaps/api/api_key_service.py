from pycaps.common import ConfigService
from typing import Optional

class ApiKeyService:
    _keys = {
        "pycaps": None,
        "openai": None,
        "together": None,
        "groq": None,
        "openrouter": None,
    }

    @staticmethod
    def set_key(provider: str, key: str):
        if provider not in ApiKeyService._keys:
            raise ValueError(f"Unknown provider: {provider}")
        ApiKeyService._keys[provider] = key

    @staticmethod
    def get_key(provider: str) -> Optional[str]:
        return ApiKeyService._keys.get(provider)

    API_KEY_CONFIG_KEY = "api_key"

    @staticmethod
    def get() -> str:
        return ConfigService.get(ApiKeyService.API_KEY_CONFIG_KEY)
    
    @staticmethod
    def set(api_key: str) -> None:
        ConfigService.set(ApiKeyService.API_KEY_CONFIG_KEY, api_key)

    @staticmethod
    def has() -> bool:
        return ConfigService.has(ApiKeyService.API_KEY_CONFIG_KEY)

    @staticmethod
    def remove() -> bool:
        ConfigService.remove(ApiKeyService.API_KEY_CONFIG_KEY)
