from ..core.config import get_settings
from .ollama import OllamaEmbeddingProvider
from .provider import EmbeddingProvider


def get_embedding_provider(
) -> EmbeddingProvider:
    settings = get_settings()

    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider()

    raise ValueError(
        "Unsupported embedding provider: "
        f"{settings.embedding_provider}"
    )