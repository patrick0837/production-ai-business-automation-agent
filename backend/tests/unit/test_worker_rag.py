import pytest

from backend.app.agent.schemas import (
    AgentRunResult,
)
from backend.app.embeddings.provider import (
    TransientEmbeddingProviderError,
)
from backend.app.worker import (
    processing as worker_processing,
)
from backend.app.worker.exceptions import (
    TransientProcessingError,
)


class FakeKnowledgeSearcher:
    pass


class FakeAgentService:
    captured_context = None
    captured_source = None
    captured_content = None

    async def run(
            self,
            *,
            source,
            content,
            context=None,
    ):
        self.__class__.captured_context = context
        self.__class__.captured_source = source
        self.__class__.captured_content = content

        return AgentRunResult(
            status="completed",
            content="Processed with RAG context.",
        )


def test_worker_agent_receives_rag_context(
        monkeypatch,
):
    searcher = FakeKnowledgeSearcher()

    monkeypatch.setattr(
        worker_processing,
        "AgentService",
        FakeAgentService,
    )

    monkeypatch.setattr(
        worker_processing,
        "WorkerKnowledgeSearcher",
        lambda: searcher,
    )

    result = worker_processing.run_agent(
        source="worker-test",
        content="Use internal policy.",
    )

    assert result.status == "completed"

    context = (
        FakeAgentService.captured_context
    )

    assert context is not None

    assert (
            context.knowledge_searcher
            is searcher
    )

    assert (
            FakeAgentService.captured_source
            == "worker-test"
    )

    assert (
            FakeAgentService.captured_content
            == "Use internal policy."
    )


class FailingEmbeddingAgentService:
    async def run(
            self,
            *,
            source,
            content,
            context=None,
    ):
        raise TransientEmbeddingProviderError(
            "Embedding service unavailable"
        )


def test_worker_retries_transient_embedding_failure(
        monkeypatch,
):
    monkeypatch.setattr(
        worker_processing,
        "AgentService",
        FailingEmbeddingAgentService,
    )

    monkeypatch.setattr(
        worker_processing,
        "WorkerKnowledgeSearcher",
        lambda: FakeKnowledgeSearcher(),
    )

    with pytest.raises(
            TransientProcessingError,
            match="temporarily unavailable",
    ):
        worker_processing.run_agent(
            source="worker-test",
            content="Search company policy.",
        )