from .celery_app import celery_app


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
    self.update_state(
        state="PROCESSING",
        meta={"request_id": request_id},
    )

    priority = (
        "high"
        if "enterprise" in content.lower()
        else "normal"
    )

    return {
        "request_id": request_id,
        "source": source,
        "status": "processed",
        "priority": priority,
    }