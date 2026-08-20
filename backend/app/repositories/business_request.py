from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.business_request import BusinessRequest
from ..schemas.business_request import BusinessRequestCreate


async def create_business_request(
        db: AsyncSession,
        data: BusinessRequestCreate,
) -> BusinessRequest:
    business_request = BusinessRequest(
        source=data.source,
        content=data.content,
    )

    db.add(business_request)
    await db.commit()
    await db.refresh(business_request)

    return business_request


async def mark_business_request_queued(
        db: AsyncSession,
        business_request: BusinessRequest,
        celery_task_id: str,
) -> BusinessRequest:
    business_request.status = "queued"
    business_request.celery_task_id = celery_task_id

    await db.commit()
    await db.refresh(business_request)

    return business_request


async def list_business_requests(
        db: AsyncSession,
) -> list[BusinessRequest]:
    result = await db.scalars(
        select(BusinessRequest).order_by(
            BusinessRequest.created_at.desc()
        )
    )

    return list(result.all())