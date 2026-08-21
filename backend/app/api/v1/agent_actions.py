import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.agent_action import AgentAction
from ...schemas.agent_action import (
    AgentActionRead,
    AgentActionReject,
)
from ...services.agent_approval import (
    AgentActionExecutionError,
    AgentActionNotFoundError,
    InvalidAgentActionStateError,
    approve_agent_action,
    reject_agent_action,
)


router = APIRouter(
    prefix="/agent-actions",
    tags=["Agent Actions"],
)


@router.get(
    "",
    response_model=list[AgentActionRead],
)
async def get_agent_actions(
        action_status: str | None = Query(
            default=None,
            alias="status",
        ),
        db: AsyncSession = Depends(get_db),
) -> list[AgentAction]:
    statement = (
        select(AgentAction)
        .order_by(
            AgentAction.created_at.desc()
        )
    )

    if action_status is not None:
        statement = statement.where(
            AgentAction.status
            == action_status
        )

    result = await db.execute(statement)

    return list(
        result.scalars().all()
    )


@router.post(
    "/{action_id}/approve",
    response_model=AgentActionRead,
)
async def approve_action(
        action_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
) -> AgentAction:
    try:
        return await approve_agent_action(
            db=db,
            action_id=action_id,
        )

    except AgentActionNotFoundError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent action not found",
        ) from exc

    except InvalidAgentActionStateError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except AgentActionExecutionError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Agent action execution failed"
            ),
        ) from exc


@router.post(
    "/{action_id}/reject",
    response_model=AgentActionRead,
)
async def reject_action(
        action_id: uuid.UUID,
        data: AgentActionReject | None = None,
        db: AsyncSession = Depends(get_db),
) -> AgentAction:
    try:
        return await reject_agent_action(
            db=db,
            action_id=action_id,
            reason=(
                data.reason
                if data is not None
                else None
            ),
        )

    except AgentActionNotFoundError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent action not found",
        ) from exc

    except InvalidAgentActionStateError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc