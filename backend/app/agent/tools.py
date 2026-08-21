from typing import Literal

from pydantic import BaseModel, Field

from .context import AgentExecutionContext
from .schemas import ToolExecutionResult


class EscalateIncidentInput(BaseModel):
    reason: str = Field(
        min_length=1,
        max_length=1000,
    )

    severity: Literal[
        "high",
        "urgent",
    ]


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
    )


def escalate_incident(
        arguments: EscalateIncidentInput,
) -> ToolExecutionResult:
    return ToolExecutionResult(
        tool_name="escalate_incident",
        status="completed",
        output={
            "severity": arguments.severity,
            "reason": arguments.reason,
            "message": (
                "Incident escalation has been "
                "prepared for the human "
                "operations team."
            ),
        },
    )


async def search_knowledge_base(
        arguments: SearchKnowledgeBaseInput,
        context: AgentExecutionContext,
) -> ToolExecutionResult:
    if context.knowledge_searcher is None:
        raise RuntimeError(
            "Knowledge search is not "
            "available in this agent context"
        )

    results = await context.knowledge_searcher(
        query=arguments.query,
        top_k=arguments.top_k,
    )

    return ToolExecutionResult(
        tool_name="search_knowledge_base",
        status="completed",
        output={
            "query": arguments.query,
            "count": len(results),
            "results": [
                {
                    "chunk_id": str(
                        result.chunk_id
                    ),
                    "document_id": str(
                        result.document_id
                    ),
                    "document_title": (
                        result.document_title
                    ),
                    "source": result.source,
                    "chunk_index": (
                        result.chunk_index
                    ),
                    "content": result.content,
                    "similarity": (
                        result.similarity
                    ),
                    "distance": (
                        result.distance
                    ),
                    "document_metadata": (
                        result.document_metadata
                    ),
                    "chunk_metadata": (
                        result.chunk_metadata
                    ),
                }
                for result in results
            ],
        },
    )