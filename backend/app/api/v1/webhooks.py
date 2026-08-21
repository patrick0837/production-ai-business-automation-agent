import secrets
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from ...core.config import get_settings
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
    prefix="/webhooks",
    tags=["Webhooks"],
)


def verify_webhook_secret(
        x_webhook_secret: Annotated[
            str | None,
            Header(
                alias="X-Webhook-Secret"
            ),
        ] = None,
) -> None:
    settings = get_settings()

    configured_secret = (
        settings.webhook_secret
    )

    if not configured_secret:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Webhook authentication "
                "is not configured"
            ),
        )

    if (
            x_webhook_secret is None
            or not secrets.compare_digest(
        x_webhook_secret,
        configured_secret,
    )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid webhook secret"
            ),
        )


@router.post(
    "/business-requests",
    response_model=BusinessRequestRead,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[
        Depends(
            verify_webhook_secret
        )
    ],
)
async def receive_business_request_webhook(
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