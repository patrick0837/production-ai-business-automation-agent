from typing import Protocol


class EmbeddingProviderError(RuntimeError):
    pass


class TransientEmbeddingProviderError(
    EmbeddingProviderError
):
    pass


class InvalidEmbeddingResponseError(
    EmbeddingProviderError
):
    pass


class EmbeddingProvider(Protocol):
    async def embed_text(
            self,
            text: str,
    ) -> list[float]:
        ...

    async def embed_batch(
            self,
            texts: list[str],
    ) -> list[list[float]]:
        ...