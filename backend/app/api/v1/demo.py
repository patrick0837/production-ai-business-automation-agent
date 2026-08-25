from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.business_request import (
    BusinessRequest,
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
    prefix="/demo",
    tags=["Public Demo"],
)


class DemoRequestCreate(BaseModel):
    content: str = Field(
        min_length=10,
        max_length=1000,
    )


@router.post(
    "/requests",
    response_model=BusinessRequestRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_demo_request(
        data: DemoRequestCreate,
        db: AsyncSession = Depends(get_db),
        task_dispatcher: TaskDispatcher = Depends(
            get_task_dispatcher
        ),
) -> BusinessRequest:
    business_request_data = (
        BusinessRequestCreate(
            source="public-live-demo",
            content=data.content,
        )
    )

    try:
        return await submit_business_request(
            db=db,
            data=business_request_data,
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
                    "Demo request dispatch failed"
                ),
                "request_id": str(
                    exc.request_id
                ),
            },
        ) from exc