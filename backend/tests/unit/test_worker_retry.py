import uuid
from types import SimpleNamespace

from backend.app.schemas.ai_analysis import (
    BusinessRequestAnalysis,
)
from backend.app.worker import tasks as worker_tasks
from backend.app.worker.exceptions import (
    TransientProcessingError,
)


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
    ):
        return False

    def commit(self):
        pass

    def rollback(self):
        pass


def configure_fake_worker(
        monkeypatch,
        business_request,
):
    monkeypatch.setattr(
        worker_tasks,
        "WorkerSessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        worker_tasks,
        "get_business_request",
        lambda db, request_id: business_request,
    )

    monkeypatch.setattr(
        worker_tasks.process_business_request,
        "update_state",
        lambda *args, **kwargs: None,
    )


def test_transient_failure_retries_then_completes(
        monkeypatch,
):
    request_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    business_request = SimpleNamespace(
        celery_task_id=task_id,
        status="queued",
        category=None,
        priority=None,
        intent=None,
        requires_human_approval=None,
        recommended_action=None,
    )

    configure_fake_worker(
        monkeypatch,
        business_request,
    )

    attempts = {"count": 0}

    def flaky_analysis(
            source: str,
            content: str,
    ) -> BusinessRequestAnalysis:
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise TransientProcessingError(
                "Temporary dependency failure"
            )

        return BusinessRequestAnalysis(
            category="support",
            priority="high",
            intent="enterprise_support",
            requires_human_approval=True,
            recommended_action=(
                "Escalate to support team."
            ),
        )

    monkeypatch.setattr(
        worker_tasks,
        "analyze_business_request",
        flaky_analysis,
    )

    result = worker_tasks.process_business_request.apply(
        args=(
            request_id,
            "website",
            "Enterprise automation request",
        ),
        task_id=task_id,
    )

    assert result.successful()
    assert attempts["count"] == 3

    assert business_request.status == "completed"

    assert business_request.category == "support"
    assert business_request.priority == "high"
    assert (
            business_request.intent
            == "enterprise_support"
    )
    assert (
            business_request.requires_human_approval
            is True
    )
    assert (
            business_request.recommended_action
            == "Escalate to support team."
    )

    assert result.result["status"] == "completed"
    assert result.result["category"] == "support"
    assert result.result["priority"] == "high"
    assert (
            result.result["intent"]
            == "enterprise_support"
    )
    assert (
            result.result["requires_human_approval"]
            is True
    )
    assert (
            result.result["recommended_action"]
            == "Escalate to support team."
    )

    assert worker_tasks.get_retry_countdown(0) == 1
    assert worker_tasks.get_retry_countdown(1) == 2
    assert worker_tasks.get_retry_countdown(2) == 4


def test_transient_failure_becomes_failed_after_max_retries(
        monkeypatch,
):
    request_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    business_request = SimpleNamespace(
        celery_task_id=task_id,
        status="queued",
        category=None,
        priority=None,
        intent=None,
        requires_human_approval=None,
        recommended_action=None,
    )

    configure_fake_worker(
        monkeypatch,
        business_request,
    )

    attempts = {"count": 0}

    def always_fail(
            source: str,
            content: str,
    ):
        attempts["count"] += 1

        raise TransientProcessingError(
            "Dependency remains unavailable"
        )

    monkeypatch.setattr(
        worker_tasks,
        "analyze_business_request",
        always_fail,
    )

    result = worker_tasks.process_business_request.apply(
        args=(
            request_id,
            "website",
            "Enterprise automation request",
        ),
        task_id=task_id,
    )

    assert result.failed()
    assert attempts["count"] == 4
    assert business_request.status == "failed"

    assert isinstance(
        result.result,
        TransientProcessingError,
    )


def test_completed_request_skips_duplicate_processing(
        monkeypatch,
):
    request_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    business_request = SimpleNamespace(
        celery_task_id=task_id,
        status="completed",
        category="support",
        priority="high",
        intent="enterprise_support",
        requires_human_approval=True,
        recommended_action=(
            "Escalate to support team."
        ),
    )

    configure_fake_worker(
        monkeypatch,
        business_request,
    )

    def should_not_run(
            source: str,
            content: str,
    ):
        raise AssertionError(
            "Duplicate task must not run "
            "AI processing again"
        )

    monkeypatch.setattr(
        worker_tasks,
        "analyze_business_request",
        should_not_run,
    )

    result = worker_tasks.process_business_request.apply(
        args=(
            request_id,
            "website",
            "Enterprise automation request",
        ),
        task_id=task_id,
    )

    assert result.successful()
    assert business_request.status == "completed"
    assert result.result["status"] == "completed"
    assert result.result["idempotent_replay"] is True