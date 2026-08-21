import httpx

from ..core.config import get_settings
from .provider import (
    EmbeddingProviderError,
    InvalidEmbeddingResponseError,
    TransientEmbeddingProviderError,
)


TRANSIENT_HTTP_STATUSES = {
    429,
    500,
    502,
    503,
    504,
}


class OllamaEmbeddingProvider:
    def __init__(
            self,
            base_url: str | None = None,
            model: str | None = None,
            dimensions: int | None = None,
    ):
        settings = get_settings()

        self.base_url = (
                base_url
                or settings.ollama_base_url
        ).rstrip("/")

        self.model = (
                model
                or settings.ollama_embedding_model
        )

        self.dimensions = (
                dimensions
                or settings.embedding_dimensions
        )

    async def _embed(
            self,
            texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        if any(
                not text.strip()
                for text in texts
        ):
            raise ValueError(
                "Embedding input must not be empty"
            )

        try:
            async with httpx.AsyncClient(
                    timeout=120.0,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.model,
                        "input": texts,
                    },
                )

        except (
                httpx.TimeoutException,
                httpx.NetworkError,
        ) as exc:
            raise TransientEmbeddingProviderError(
                "Ollama embedding service "
                "is temporarily unavailable"
            ) from exc

        if (
                response.status_code
                in TRANSIENT_HTTP_STATUSES
        ):
            raise TransientEmbeddingProviderError(
                "Ollama embedding service "
                f"returned HTTP "
                f"{response.status_code}"
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EmbeddingProviderError(
                "Ollama embedding request failed"
            ) from exc

        try:
            payload = response.json()
            embeddings = payload["embeddings"]
        except (
                ValueError,
                KeyError,
                TypeError,
        ) as exc:
            raise InvalidEmbeddingResponseError(
                "Ollama returned an invalid "
                "embedding response"
            ) from exc

        if (
                not isinstance(embeddings, list)
                or len(embeddings) != len(texts)
        ):
            raise InvalidEmbeddingResponseError(
                "Ollama returned an unexpected "
                "number of embeddings"
            )

        validated_embeddings = []

        for embedding in embeddings:
            if (
                    not isinstance(embedding, list)
                    or len(embedding)
                    != self.dimensions
            ):
                raise InvalidEmbeddingResponseError(
                    "Embedding dimension does not "
                    f"match expected "
                    f"{self.dimensions}"
                )

            if not all(
                    isinstance(value, (int, float))
                    for value in embedding
            ):
                raise InvalidEmbeddingResponseError(
                    "Embedding contains "
                    "non-numeric values"
                )

            validated_embeddings.append(
                [
                    float(value)
                    for value in embedding
                ]
            )

        return validated_embeddings

    async def embed_text(
            self,
            text: str,
    ) -> list[float]:
        embeddings = await self._embed(
            [text]
        )

        return embeddings[0]

    async def embed_batch(
            self,
            texts: list[str],
    ) -> list[list[float]]:
        return await self._embed(texts)