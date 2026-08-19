from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.business_request import BusinessRequest
from ...repositories.business_request import (
    create_business_request,
    list_business_requests,
)
from ...schemas.business_request import (
    BusinessRequestCreate,
    BusinessRequestRead,
)

router = APIRouter(
    prefix="/requests",
    tags=["Business Requests"],
)


@router.post(
    "",
    response_model=BusinessRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
        data: BusinessRequestCreate,
        db: AsyncSession = Depends(get_db),
) -> BusinessRequest:
    return await create_business_request(db, data)


@router.get(
    "",
    response_model=list[BusinessRequestRead],
)
async def get_requests(
        db: AsyncSession = Depends(get_db),
) -> list[BusinessRequest]:
    return await list_business_requests(db)