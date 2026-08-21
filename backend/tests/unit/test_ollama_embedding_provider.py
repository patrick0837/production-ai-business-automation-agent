import httpx
import pytest

from backend.app.embeddings.ollama import (
    OllamaEmbeddingProvider,
)
from backend.app.embeddings.provider import (
    InvalidEmbeddingResponseError,
    TransientEmbeddingProviderError,
)


class FakeResponse:
    def __init__(
            self,
            *,
            status_code: int = 200,
            payload=None,
    ):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request(
                "POST",
                "http://test/api/embed",
            )

            response = httpx.Response(
                self.status_code,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "HTTP error",
                request=request,
                response=response,
            )


class FakeAsyncClient:
    response = None

    def __init__(
            self,
            *args,
            **kwargs,
    ):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(
            self,
            exc_type,
            exc_value,
            traceback,
    ):
        return False

    async def post(
            self,
            *args,
            **kwargs,
    ):
        return self.response


async def test_embed_text_returns_vector(
        monkeypatch,
):
    FakeAsyncClient.response = FakeResponse(
        payload={
            "embeddings": [
                [
                    0.1,
                    0.2,
                    0.3,
                ]
            ]
        }
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    provider = OllamaEmbeddingProvider(
        base_url="http://test",
        model="test-model",
        dimensions=3,
    )

    embedding = await provider.embed_text(
        "refund policy"
    )

    assert embedding == [
        0.1,
        0.2,
        0.3,
    ]


async def test_embed_batch_returns_vectors(
        monkeypatch,
):
    FakeAsyncClient.response = FakeResponse(
        payload={
            "embeddings": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
            ]
        }
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    provider = OllamaEmbeddingProvider(
        base_url="http://test",
        model="test-model",
        dimensions=3,
    )

    embeddings = await provider.embed_batch(
        [
            "refund policy",
            "shipping policy",
        ]
    )

    assert embeddings == [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]


async def test_invalid_embedding_dimensions_raise(
        monkeypatch,
):
    FakeAsyncClient.response = FakeResponse(
        payload={
            "embeddings": [
                [
                    0.1,
                    0.2,
                ]
            ]
        }
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    provider = OllamaEmbeddingProvider(
        base_url="http://test",
        model="test-model",
        dimensions=3,
    )

    with pytest.raises(
            InvalidEmbeddingResponseError
    ):
        await provider.embed_text(
            "refund policy"
        )


async def test_transient_http_failure_raises(
        monkeypatch,
):
    FakeAsyncClient.response = FakeResponse(
        status_code=503,
        payload={},
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    provider = OllamaEmbeddingProvider(
        base_url="http://test",
        model="test-model",
        dimensions=3,
    )

    with pytest.raises(
            TransientEmbeddingProviderError
    ):
        await provider.embed_text(
            "refund policy"
        )