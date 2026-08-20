import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.business_request import BusinessRequest
from ...repositories.business_request import (
    create_business_request,
    list_business_requests,
    mark_business_request_queued,
)
from ...schemas.business_request import (
    BusinessRequestCreate,
    BusinessRequestRead,
)
from ...services.task_dispatcher import (
    TaskDispatcher,
    get_task_dispatcher,
)

router = APIRouter(
    prefix="/requests",
    tags=["Business Requests"],
)


@router.post(
    "",
    response_model=BusinessRequestRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_request(
        data: BusinessRequestCreate,
        db: AsyncSession = Depends(get_db),
        task_dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
) -> BusinessRequest:
    business_request = await create_business_request(
        db,
        data,
    )

    celery_task_id = str(uuid.uuid4())

    business_request = await mark_business_request_queued(
        db=db,
        business_request=business_request,
        celery_task_id=celery_task_id,
    )

    await task_dispatcher.enqueue_business_request(
        task_id=celery_task_id,
        request_id=str(business_request.id),
        source=business_request.source,
        content=business_request.content,
    )

    return business_request


@router.get(
    "",
    response_model=list[BusinessRequestRead],
)
async def get_requests(
        db: AsyncSession = Depends(get_db),
) -> list[BusinessRequest]:
    return await list_business_requests(db)