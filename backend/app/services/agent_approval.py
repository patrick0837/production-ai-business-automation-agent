import asyncio
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.registry import execute_approved_tool
from ..models.agent_action import AgentAction
from ..models.business_request import BusinessRequest
from .audit import create_audit_event


class AgentActionNotFoundError(RuntimeError):
    pass


class InvalidAgentActionStateError(RuntimeError):
    pass


class AgentActionExecutionError(RuntimeError):
    pass


async def _lock_agent_action(
        db: AsyncSession,
        action_id: uuid.UUID,
) -> AgentAction:
    result = await db.execute(
        select(AgentAction)
        .where(
            AgentAction.id == action_id
        )
        .with_for_update()
    )

    action = result.scalar_one_or_none()

    if action is None:
        raise AgentActionNotFoundError(
            f"Agent action not found: {action_id}"
        )

    return action


async def _lock_business_request(
        db: AsyncSession,
        business_request_id: uuid.UUID,
) -> BusinessRequest:
    result = await db.execute(
        select(BusinessRequest)
        .where(
            BusinessRequest.id
            == business_request_id
        )
        .with_for_update()
    )

    business_request = result.scalar_one_or_none()

    if business_request is None:
        raise RuntimeError(
            "Business request for agent action "
            "was not found"
        )

    return business_request


async def _update_business_request_status(
        db: AsyncSession,
        business_request_id: uuid.UUID,
) -> None:
    business_request = await _lock_business_request(
        db=db,
        business_request_id=business_request_id,
    )

    pending_count = await db.scalar(
        select(
            func.count(AgentAction.id)
        ).where(
            AgentAction.business_request_id
            == business_request_id,
            AgentAction.status
            == "pending_approval",
            )
    )

    if pending_count:
        business_request.status = "awaiting_approval"
    else:
        business_request.status = "completed"


async def approve_agent_action(
        db: AsyncSession,
        action_id: uuid.UUID,
) -> AgentAction:
    action = await _lock_agent_action(
        db=db,
        action_id=action_id,
    )

    # Duplicate approve is idempotent.
    if action.status == "completed":
        return action

    if action.status == "rejected":
        raise InvalidAgentActionStateError(
            "Rejected action cannot be approved"
        )

    if action.status != "pending_approval":
        raise InvalidAgentActionStateError(
            "Only pending approval actions "
            "can be approved"
        )

    if not action.requires_approval:
        raise InvalidAgentActionStateError(
            "This action does not require "
            "human approval"
        )

    # Record the human approval first.
    approved_event = create_audit_event(
        event_type="action_approved",
        actor_type="human",
        business_request_id=(
            action.business_request_id
        ),
        agent_action_id=action.id,
        details={
            "tool_name": action.tool_name,
        },
    )

    db.add(approved_event)

    # Force PostgreSQL to INSERT this event now,
    # assigning its event_sequence before any
    # later audit event.
    await db.flush()

    try:
        execution_result = await asyncio.to_thread(
            execute_approved_tool,
            action.tool_name,
            action.arguments,
        )

    except Exception as exc:
        failed_event = create_audit_event(
            event_type="tool_failed",
            actor_type="system",
            business_request_id=(
                action.business_request_id
            ),
            agent_action_id=action.id,
            details={
                "tool_name": action.tool_name,
                "error_type": type(exc).__name__,
            },
        )

        db.add(failed_event)

        # Guarantees:
        # action_approved.sequence
        # <
        # tool_failed.sequence
        await db.flush()

        # Persist the failed execution audit trail.
        # AgentAction deliberately remains
        # pending_approval so it can be retried.
        await db.commit()

        raise AgentActionExecutionError(
            "Approved agent action "
            "could not be executed"
        ) from exc

    if execution_result.status != "completed":
        failed_event = create_audit_event(
            event_type="tool_failed",
            actor_type="system",
            business_request_id=(
                action.business_request_id
            ),
            agent_action_id=action.id,
            details={
                "tool_name": action.tool_name,
                "reason": (
                    "Tool did not return "
                    "completed status"
                ),
            },
        )

        db.add(failed_event)

        # Guarantees deterministic event ordering.
        await db.flush()

        await db.commit()

        raise AgentActionExecutionError(
            "Approved agent action did not "
            "complete successfully"
        )

    action.status = "completed"
    action.result = execution_result.output

    executed_event = create_audit_event(
        event_type="tool_executed",
        actor_type="system",
        business_request_id=(
            action.business_request_id
        ),
        agent_action_id=action.id,
        details={
            "tool_name": action.tool_name,
            "result": execution_result.output,
        },
    )

    db.add(executed_event)

    # Guarantees:
    # action_approved.sequence
    # <
    # tool_executed.sequence
    await db.flush()

    await _update_business_request_status(
        db=db,
        business_request_id=(
            action.business_request_id
        ),
    )

    await db.commit()
    await db.refresh(action)

    return action


async def reject_agent_action(
        db: AsyncSession,
        action_id: uuid.UUID,
        reason: str | None = None,
) -> AgentAction:
    action = await _lock_agent_action(
        db=db,
        action_id=action_id,
    )

    # Duplicate reject is idempotent.
    if action.status == "rejected":
        return action

    if action.status == "completed":
        raise InvalidAgentActionStateError(
            "Completed action cannot be rejected"
        )

    if action.status != "pending_approval":
        raise InvalidAgentActionStateError(
            "Only pending approval actions "
            "can be rejected"
        )

    action.status = "rejected"

    rejection_result = {
        "decision": "rejected",
    }

    if reason:
        rejection_result["reason"] = reason

    action.result = rejection_result

    audit_details = {
        "tool_name": action.tool_name,
    }

    if reason:
        audit_details["reason"] = reason

    rejected_event = create_audit_event(
        event_type="action_rejected",
        actor_type="human",
        business_request_id=(
            action.business_request_id
        ),
        agent_action_id=action.id,
        details=audit_details,
    )

    db.add(rejected_event)

    # Assign event_sequence before continuing.
    await db.flush()

    await _update_business_request_status(
        db=db,
        business_request_id=(
            action.business_request_id
        ),
    )

    await db.commit()
    await db.refresh(action)

    return action