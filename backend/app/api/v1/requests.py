import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from ...db.session import get_db
from ...models.business_request import (
    BusinessRequest,
)
from ...repositories.business_request import (
    get_business_request_by_id,
    list_business_requests,
)
from ...schemas.business_request import (
    BusinessRequestCreate,
    BusinessRequestRead,
)
from ...services.business_request_intake import (
    BusinessRequestDispatchError,
    submit_business_request,
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
        task_dispatcher: TaskDispatcher = Depends(
            get_task_dispatcher
        ),
) -> BusinessRequest:
    try:
        return await submit_business_request(
            db=db,
            data=data,
            task_dispatcher=task_dispatcher,
        )

    except BusinessRequestDispatchError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "status": "failed",
                "message": (
                    "Background task "
                    "dispatch failed"
                ),
                "request_id": str(
                    exc.request_id
                ),
            },
        ) from exc


@router.get(
    "",
    response_model=list[BusinessRequestRead],
)
async def get_requests(
        db: AsyncSession = Depends(get_db),
) -> list[BusinessRequest]:
    return await list_business_requests(
        db
    )


@router.get(
    "/{request_id}",
    response_model=BusinessRequestRead,
)
async def get_request(
        request_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
) -> BusinessRequest:
    business_request = (
        await get_business_request_by_id(
            db=db,
            request_id=request_id,
        )
    )

    if business_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business request not found",
        )

    return business_request