import asyncio
from typing import Protocol

from ..worker.tasks import process_business_request


class TaskDispatcher(Protocol):
    async def enqueue_business_request(
            self,
            request_id: str,
            source: str,
            content: str,
    ) -> str:
        ...


class CeleryTaskDispatcher:
    async def enqueue_business_request(
            self,
            request_id: str,
            source: str,
            content: str,
    ) -> str:
        result = await asyncio.to_thread(
            process_business_request.apply_async,
            args=[
                request_id,
                source,
                content,
            ],
        )

        return result.id


def get_task_dispatcher() -> TaskDispatcher:
    return CeleryTaskDispatcher()