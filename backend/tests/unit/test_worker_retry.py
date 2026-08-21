import uuid
from types import SimpleNamespace

from backend.app.agent.schemas import (
    AgentRunResult,
    AgentToolCall,
    AgentToolExecution,
    ToolExecutionResult,
)
from backend.app.models.agent_action import AgentAction
from backend.app.models.audit_event import AuditEvent
from backend.app.schemas.ai_analysis import (
    BusinessRequestAnalysis,
)
from backend.app.worker import tasks as worker_tasks
from backend.app.worker.exceptions import (
    TransientProcessingError,
)


class FakeSession:
    def __init__(self):
        self.added = []

    def __enter__(self):
        return self

    def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
    ):
        return False

    def add(self, value):
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if (
                    isinstance(value, AgentAction)
                    and value.id is None
            ):
                value.id = uuid.uuid4()

    def commit(self):
        pass

    def rollback(self):
        pass


def configure_fake_worker(
        monkeypatch,
        business_request,
):
    session = FakeSession()

    monkeypatch.setattr(
        worker_tasks,
        "WorkerSessionLocal",
        lambda: session,
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

    monkeypatch.setattr(
        worker_tasks,
        "run_agent",
        lambda source, content: AgentRunResult(
            status="completed",
            content="No automated action required.",
        ),
    )

    return session


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
    assert result.result["priority"] == "high"

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


def test_agent_approval_is_persisted_and_pauses_request(
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

    session = configure_fake_worker(
        monkeypatch,
        business_request,
    )

    monkeypatch.setattr(
        worker_tasks,
        "analyze_business_request",
        lambda source, content: (
            BusinessRequestAnalysis(
                category="support",
                priority="urgent",
                intent="service_outage",
                requires_human_approval=True,
                recommended_action=(
                    "Escalate the incident."
                ),
            )
        ),
    )

    monkeypatch.setattr(
        worker_tasks,
        "run_agent",
        lambda source, content: AgentRunResult(
            status="approval_required",
            tool_executions=[
                AgentToolExecution(
                    tool_call=AgentToolCall(
                        id="call-123",
                        name="escalate_incident",
                        arguments={
                            "reason": (
                                "Production payment "
                                "system is down."
                            ),
                            "severity": "urgent",
                        },
                    ),
                    result=ToolExecutionResult(
                        tool_name=(
                            "escalate_incident"
                        ),
                        status=(
                            "approval_required"
                        ),
                        output={
                            "arguments": {
                                "reason": (
                                    "Production payment "
                                    "system is down."
                                ),
                                "severity": "urgent",
                            }
                        },
                    ),
                )
            ],
        ),
    )

    result = worker_tasks.process_business_request.apply(
        args=(
            request_id,
            "website",
            "Production payment system is down.",
        ),
        task_id=task_id,
    )

    assert result.successful()

    assert (
            business_request.status
            == "awaiting_approval"
    )

    assert (
            result.result["status"]
            == "awaiting_approval"
    )

    assert (
            result.result["agent_status"]
            == "approval_required"
    )

    assert result.result["agent_action_count"] == 1

    actions = [
        value
        for value in session.added
        if isinstance(value, AgentAction)
    ]

    audit_events = [
        value
        for value in session.added
        if isinstance(value, AuditEvent)
    ]

    assert len(actions) == 1
    assert len(audit_events) == 2

    action = actions[0]

    assert isinstance(
        action,
        AgentAction,
    )

    assert action.id is not None

    assert (
            action.business_request_id
            == uuid.UUID(request_id)
    )

    assert action.tool_call_id == "call-123"

    assert (
            action.tool_name
            == "escalate_incident"
    )

    assert action.status == "pending_approval"
    assert action.requires_approval is True

    assert (
            action.arguments["severity"]
            == "urgent"
    )

    assert action.result is None

    event_types = {
        event.event_type
        for event in audit_events
    }

    assert event_types == {
        "agent_tool_requested",
        "approval_required",
    }

    for event in audit_events:
        assert (
                event.business_request_id
                == uuid.UUID(request_id)
        )

        assert event.agent_action_id is not None

        assert (
                event.agent_action_id
                == action.id
        )