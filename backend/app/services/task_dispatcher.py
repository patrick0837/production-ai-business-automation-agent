import asyncio
from typing import Protocol

from ..worker.tasks import process_business_request


class TaskDispatchError(RuntimeError):
    pass


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
        try:
            await asyncio.to_thread(
                process_business_request.apply_async,
                args=[
                    request_id,
                    source,
                    content,
                ],
                task_id=task_id,
                retry=True,
                retry_policy={
                    "max_retries": 3,
                    "interval_start": 0,
                    "interval_step": 0.5,
                    "interval_max": 1.0,
                },
            )
        except Exception as exc:
            raise TaskDispatchError(
                f"Failed to dispatch task {task_id}"
            ) from exc


def get_task_dispatcher() -> TaskDispatcher:
    return CeleryTaskDispatcher()