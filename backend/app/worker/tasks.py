import uuid

from sqlalchemy.orm import Session

from ..db.worker_session import WorkerSessionLocal
from ..models.business_request import BusinessRequest
from .celery_app import celery_app
from .exceptions import TransientProcessingError
from .processing import determine_priority


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
            if business_request.status == "completed":
               return {
                        "request_id": request_id,
                        "source": source,
                        "status": "completed",
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

            priority = determine_priority(content)

            business_request.status = "completed"
            db.commit()

            return {
                "request_id": request_id,
                "source": source,
                "status": "completed",
                "priority": priority,
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