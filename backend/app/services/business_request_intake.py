import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.business_request import BusinessRequest
from ..repositories.business_request import (
    create_business_request,
    mark_business_request_failed,
    mark_business_request_queued,
)
from ..schemas.business_request import (
    BusinessRequestCreate,
)
from .task_dispatcher import (
    TaskDispatcher,
    TaskDispatchError,
)


class BusinessRequestDispatchError(
    RuntimeError
):
    def __init__(
            self,
            request_id: uuid.UUID,
    ) -> None:
        self.request_id = request_id

        super().__init__(
            "Background task dispatch failed"
        )


async def submit_business_request(
        *,
        db: AsyncSession,
        data: BusinessRequestCreate,
        task_dispatcher: TaskDispatcher,
) -> BusinessRequest:
    business_request = (
        await create_business_request(
            db,
            data,
        )
    )

    celery_task_id = str(
        uuid.uuid4()
    )

    business_request = (
        await mark_business_request_queued(
            db=db,
            business_request=(
                business_request
            ),
            celery_task_id=(
                celery_task_id
            ),
        )
    )

    try:
        await (
            task_dispatcher
            .enqueue_business_request(
                task_id=celery_task_id,
                request_id=str(
                    business_request.id
                ),
                source=(
                    business_request.source
                ),
                content=(
                    business_request.content
                ),
            )
        )

    except TaskDispatchError as exc:
        await (
            mark_business_request_failed(
                db=db,
                business_request=(
                    business_request
                ),
            )
        )

        raise BusinessRequestDispatchError(
            business_request.id
        ) from exc

    return business_request