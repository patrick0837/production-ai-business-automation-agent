import uuid

from backend.app.agent.context import (
    AgentExecutionContext,
)
from backend.app.agent.registry import (
    execute_registered_tool_async,
    get_tool_specs,
)
from backend.app.agent.schemas import (
    AgentModelResponse,
    AgentToolCall,
)
from backend.app.agent.service import (
    AgentService,
)
from backend.app.rag.retrieval import (
    KnowledgeSearchResult,
)


def make_search_result(
) -> KnowledgeSearchResult:
    return KnowledgeSearchResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title=(
            "Support Policy"
        ),
        source="support",
        chunk_index=0,
        content=(
            "Security incidents must be "
            "escalated to the operations "
            "team."
        ),
        distance=0.2,
        similarity=0.8,
        document_metadata={
            "department": "support",
        },
        chunk_metadata={},
    )


class FakeKnowledgeSearcher:
    def __init__(self):
        self.queries: list[str] = []

    async def __call__(
            self,
            *,
            query: str,
            top_k: int = 5,
            source: str | None = None,
            min_similarity: float | None = None,
    ) -> list[
        KnowledgeSearchResult
    ]:
        self.queries.append(query)

        return [
            make_search_result()
        ]


class FakeAgentProvider:
    def __init__(self):
        self.calls = 0
        self.messages = []

    async def generate_agent_response(
            self,
            *,
            messages,
            tools,
    ):
        self.messages.append(
            messages.copy()
        )

        self.calls += 1

        if self.calls == 1:
            return AgentModelResponse(
                content="",
                tool_calls=[
                    AgentToolCall(
                        id="tool-call-1",
                        name=(
                            "search_knowledge_base"
                        ),
                        arguments={
                            "query": (
                                "security incident"
                            ),
                            "top_k": 1,
                        },
                    )
                ],
            )

        return AgentModelResponse(
            content=(
                "The internal policy says "
                "the security incident must "
                "be escalated to the "
                "operations team."
            )
        )


def tool_names(
        specs,
) -> set[str]:
    return {
        spec["function"]["name"]
        for spec in specs
    }


def test_rag_tool_hidden_without_context():
    names = tool_names(
        get_tool_specs()
    )

    assert (
            "escalate_incident"
            in names
    )

    assert (
            "search_knowledge_base"
            not in names
    )


def test_rag_tool_available_with_context():
    context = AgentExecutionContext(
        knowledge_searcher=(
            FakeKnowledgeSearcher()
        )
    )

    names = tool_names(
        get_tool_specs(
            context=context
        )
    )

    assert (
            "search_knowledge_base"
            in names
    )


async def test_execute_rag_tool():
    searcher = (
        FakeKnowledgeSearcher()
    )

    context = AgentExecutionContext(
        knowledge_searcher=searcher
    )

    result = await (
        execute_registered_tool_async(
            name="search_knowledge_base",
            arguments={
                "query": (
                    "security incident"
                ),
                "top_k": 1,
            },
            context=context,
        )
    )

    assert result.status == "completed"

    assert (
            result.tool_name
            == "search_knowledge_base"
    )

    assert result.output["count"] == 1

    assert (
            result.output["results"][0][
                "similarity"
            ]
            == 0.8
    )

    assert searcher.queries == [
        "security incident"
    ]


async def test_agent_uses_rag_tool_and_continues():
    provider = FakeAgentProvider()

    searcher = (
        FakeKnowledgeSearcher()
    )

    context = AgentExecutionContext(
        knowledge_searcher=searcher
    )

    service = AgentService(
        provider=provider,
        max_steps=3,
    )

    result = await service.run(
        source="customer-support",
        content=(
            "What should we do with a "
            "security incident?"
        ),
        context=context,
    )

    assert result.status == "completed"

    assert len(
        result.tool_executions
    ) == 1

    execution = (
        result.tool_executions[0]
    )

    assert (
            execution.tool_call.name
            == "search_knowledge_base"
    )

    assert (
            execution.result.status
            == "completed"
    )

    assert (
            "escalated"
            in result.content
    )

    assert provider.calls == 2