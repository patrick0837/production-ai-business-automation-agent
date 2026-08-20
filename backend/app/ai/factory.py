from .ollama_provider import OllamaProvider
from .provider import AIProvider
from ..core.config import get_settings


def get_ai_provider() -> AIProvider:
    settings = get_settings()

    if settings.ai_provider == "ollama":
        return OllamaProvider()

    raise ValueError(
        f"Unsupported AI provider: {settings.ai_provider}"
    )