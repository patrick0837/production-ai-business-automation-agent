import uuid

from sqlalchemy.orm import Session

from ..agent.schemas import AgentRunResult
from ..db.worker_session import WorkerSessionLocal
from ..models.agent_action import AgentAction
from ..models.business_request import BusinessRequest
from .celery_app import celery_app
from .exceptions import TransientProcessingError
from .processing import (
    analyze_business_request,
    run_agent,
)


MAX_TASK_RETRIES = 3
MAX_RETRY_DELAY_SECONDS = 30


def get_business_request(
        db: Session,
        request_id: str,
) -> BusinessRequest:
    business_request = db.get(
        BusinessRequest,
        uuid.UUID(request_id),
    )

    if business_request is None:
        raise ValueError(
            f"Business request not found: {request_id}"
        )

    return business_request


def get_retry_countdown(retries: int) -> int:
    return min(
        2 ** retries,
        MAX_RETRY_DELAY_SECONDS,
        )


def persist_agent_actions(
        db: Session,
        business_request_id: uuid.UUID,
        agent_result: AgentRunResult,
) -> None:
    for execution in agent_result.tool_executions:
        approval_required = (
                execution.result.status
                == "approval_required"
        )

        action = AgentAction(
            business_request_id=business_request_id,
            tool_call_id=execution.tool_call.id,
            tool_name=execution.tool_call.name,
            arguments=execution.tool_call.arguments,
            status=(
                "pending_approval"
                if approval_required
                else "completed"
            ),
            requires_approval=approval_required,
            result=(
                None
                if approval_required
                else execution.result.output
            ),
        )

        db.add(action)


@celery_app.task(
    bind=True,
    name="process_business_request",
    max_retries=MAX_TASK_RETRIES,
    acks_late=True,
)
def process_business_request(
        self,
        request_id: str,
        source: str,
        content: str,
) -> dict:
    with WorkerSessionLocal() as db:
        try:
            business_request = get_business_request(
                db,
                request_id,
            )

            if (
                    business_request.celery_task_id
                    != self.request.id
            ):
                raise ValueError(
                    "Celery task ID does not match "
                    "the business request"
                )

            if business_request.status in {
                "completed",
                "awaiting_approval",
            }:
                return {
                    "request_id": request_id,
                    "source": source,
                    "status": (
                        business_request.status
                    ),
                    "idempotent_replay": True,
                }

            business_request.status = "processing"
            db.commit()

            self.update_state(
                state="PROCESSING",
                meta={
                    "request_id": request_id,
                },
            )

            analysis = analyze_business_request(
                source=source,
                content=content,
            )

            business_request.category = analysis.category
            business_request.priority = analysis.priority
            business_request.intent = analysis.intent
            business_request.requires_human_approval = (
                analysis.requires_human_approval
            )
            business_request.recommended_action = (
                analysis.recommended_action
            )

            agent_result = run_agent(
                source=source,
                content=content,
            )

            persist_agent_actions(
                db=db,
                business_request_id=uuid.UUID(
                    request_id
                ),
                agent_result=agent_result,
            )

            if (
                    agent_result.status
                    == "approval_required"
            ):
                business_request.status = (
                    "awaiting_approval"
                )

                db.commit()

                return {
                    "request_id": request_id,
                    "source": source,
                    "status": "awaiting_approval",
                    "category": analysis.category,
                    "priority": analysis.priority,
                    "intent": analysis.intent,
                    "requires_human_approval": (
                        analysis
                        .requires_human_approval
                    ),
                    "recommended_action": (
                        analysis.recommended_action
                    ),
                    "agent_status": (
                        agent_result.status
                    ),
                    "agent_action_count": len(
                        agent_result.tool_executions
                    ),
                }

            if (
                    agent_result.status
                    == "max_steps_exceeded"
            ):
                business_request.status = "failed"
                db.commit()

                raise RuntimeError(
                    "Agent exceeded maximum steps"
                )

            business_request.status = "completed"
            db.commit()

            return {
                "request_id": request_id,
                "source": source,
                "status": "completed",
                "category": analysis.category,
                "priority": analysis.priority,
                "intent": analysis.intent,
                "requires_human_approval": (
                    analysis.requires_human_approval
                ),
                "recommended_action": (
                    analysis.recommended_action
                ),
                "agent_status": agent_result.status,
                "agent_action_count": len(
                    agent_result.tool_executions
                ),
            }

        except TransientProcessingError as exc:
            db.rollback()

            business_request = get_business_request(
                db,
                request_id,
            )

            if self.request.retries >= MAX_TASK_RETRIES:
                business_request.status = "failed"
                db.commit()

                raise

            business_request.status = "retrying"
            db.commit()

            countdown = get_retry_countdown(
                self.request.retries
            )

            raise self.retry(
                exc=exc,
                countdown=countdown,
            )

        except Exception:
            db.rollback()

            try:
                business_request = get_business_request(
                    db,
                    request_id,
                )

                business_request.status = "failed"
                db.commit()

            except Exception:
                db.rollback()

            raise