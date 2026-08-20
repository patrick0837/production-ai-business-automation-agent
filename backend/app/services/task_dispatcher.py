import asyncio
from typing import Protocol

from ..worker.tasks import process_business_request


class TaskDispatcher(Protocol):
    async def enqueue_business_request(
            self,
            task_id: str,
            request_id: str,
            source: str,
            content: str,
    ) -> None:
        ...


class CeleryTaskDispatcher:
    async def enqueue_business_request(
            self,
            task_id: str,
            request_id: str,
            source: str,
            content: str,
    ) -> None:
        await asyncio.to_thread(
            process_business_request.apply_async,
            args=[
                request_id,
                source,
                content,
            ],
            task_id=task_id,
        )


def get_task_dispatcher() -> TaskDispatcher:
    return CeleryTaskDispatcher()