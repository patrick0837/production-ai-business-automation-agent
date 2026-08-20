import uuid

from sqlalchemy.orm import Session

from ..db.worker_session import WorkerSessionLocal
from ..models.business_request import BusinessRequest
from .celery_app import celery_app


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


@celery_app.task(
    bind=True,
    name="process_business_request",
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

            business_request.status = "processing"
            db.commit()

            self.update_state(
                state="PROCESSING",
                meta={
                    "request_id": request_id,
                },
            )

            priority = (
                "high"
                if "enterprise" in content.lower()
                else "normal"
            )

            business_request.status = "completed"
            db.commit()

            return {
                "request_id": request_id,
                "source": source,
                "status": "completed",
                "priority": priority,
            }

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