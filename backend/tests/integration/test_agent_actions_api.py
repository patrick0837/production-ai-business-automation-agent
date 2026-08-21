import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.agent.schemas import ToolExecutionResult
from backend.app.main import app
from backend.app.models.agent_action import AgentAction
from backend.app.models.audit_event import AuditEvent
from backend.app.models.business_request import BusinessRequest
from backend.app.services import (
    agent_approval as agent_approval_service,
)


async def create_agent_action(
        db_session,
        action_status: str = "pending_approval",
        requires_approval: bool = True,
):
    business_request = BusinessRequest(
        source="integration-test",
        content="Production payment system is down.",
        status=(
            "awaiting_approval"
            if action_status == "pending_approval"
            else "completed"
        ),
        celery_task_id=str(uuid.uuid4()),
        category="support",
        priority="urgent",
        intent="service_outage",
        requires_human_approval=True,
        recommended_action="Escalate the incident.",
    )

    db_session.add(business_request)
    await db_session.flush()

    action = AgentAction(
        business_request_id=business_request.id,
        tool_call_id=str(uuid.uuid4()),
        tool_name="escalate_incident",
        arguments={
            "reason": (
                "Production payment system is down."
            ),
            "severity": "urgent",
        },
        status=action_status,
        requires_approval=requires_approval,
        result=(
            None
            if action_status == "pending_approval"
            else {
                "existing": True,
            }
        ),
    )

    db_session.add(action)

    # Commit setup so API rollback tests
    # do not erase fixture data.
    await db_session.commit()

    await db_session.refresh(business_request)
    await db_session.refresh(action)

    return business_request, action


async def test_list_pending_agent_actions(
        override_database,
        db_session,
):
    _, pending_action = await create_agent_action(
        db_session,
        action_status="pending_approval",
    )

    await create_agent_action(
        db_session,
        action_status="completed",
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/agent-actions",
            params={
                "status": "pending_approval",
            },
        )

    assert response.status_code == 200

    actions = response.json()

    assert len(actions) == 1

    assert (
            actions[0]["id"]
            == str(pending_action.id)
    )

    assert (
            actions[0]["status"]
            == "pending_approval"
    )

    assert (
            actions[0]["tool_name"]
            == "escalate_incident"
    )


async def test_approve_agent_action_executes_once(
        override_database,
        db_session,
        monkeypatch,
):
    business_request, action = (
        await create_agent_action(
            db_session,
        )
    )

    calls = {
        "count": 0,
    }

    def fake_execute_approved_tool(
            name,
            arguments,
    ):
        calls["count"] += 1

        return ToolExecutionResult(
            tool_name=name,
            status="completed",
            output={
                "message": (
                    "Incident escalation completed."
                ),
                "severity": arguments["severity"],
            },
        )

    monkeypatch.setattr(
        agent_approval_service,
        "execute_approved_tool",
        fake_execute_approved_tool,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        first_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/approve"
        )

        assert first_response.status_code == 200

        approved = first_response.json()

        assert approved["status"] == "completed"

        assert (
                approved["result"]["severity"]
                == "urgent"
        )

        assert calls["count"] == 1

        # Duplicate approve must not execute
        # the tool a second time.
        second_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/approve"
        )

        assert second_response.status_code == 200
        assert calls["count"] == 1

        # Completed actions cannot later be rejected.
        reject_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/reject",
            json={
                "reason": "Too late",
            },
        )

        assert reject_response.status_code == 409

    await db_session.refresh(
        business_request
    )

    await db_session.refresh(action)

    assert action.status == "completed"

    assert (
            business_request.status
            == "completed"
    )

    audit_result = await db_session.execute(
        select(AuditEvent)
        .where(
            AuditEvent.agent_action_id
            == action.id
        )
        .order_by(
            AuditEvent.event_sequence
        )
    )

    audit_events = list(
        audit_result.scalars().all()
    )

    # Duplicate approve must not create
    # duplicate audit events.
    assert len(audit_events) == 2

    assert [
               event.event_type
               for event in audit_events
           ] == [
               "action_approved",
               "tool_executed",
           ]

    approved_event = audit_events[0]
    executed_event = audit_events[1]

    assert (
            approved_event.event_sequence
            is not None
    )

    assert (
            executed_event.event_sequence
            is not None
    )

    assert (
            approved_event.event_sequence
            < executed_event.event_sequence
    )

    assert approved_event.actor_type == "human"
    assert executed_event.actor_type == "system"

    assert (
            approved_event.business_request_id
            == business_request.id
    )

    assert (
            approved_event.agent_action_id
            == action.id
    )

    assert (
            approved_event.details["tool_name"]
            == "escalate_incident"
    )

    assert (
            executed_event.details["tool_name"]
            == "escalate_incident"
    )

    assert (
            executed_event.details["result"][
                "severity"
            ]
            == "urgent"
    )


async def test_reject_agent_action_without_execution(
        override_database,
        db_session,
        monkeypatch,
):
    business_request, action = (
        await create_agent_action(
            db_session,
        )
    )

    def should_not_execute(
            name,
            arguments,
    ):
        raise AssertionError(
            "Rejected action must not execute "
            "the tool"
        )

    monkeypatch.setattr(
        agent_approval_service,
        "execute_approved_tool",
        should_not_execute,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/reject",
            json={
                "reason": (
                    "Human operator rejected "
                    "the escalation."
                ),
            },
        )

        assert response.status_code == 200

        rejected = response.json()

        assert rejected["status"] == "rejected"

        assert (
                rejected["result"]["decision"]
                == "rejected"
        )

        assert (
                rejected["result"]["reason"]
                == (
                    "Human operator rejected "
                    "the escalation."
                )
        )

        # Duplicate rejection is idempotent.
        duplicate_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/reject",
            json={
                "reason": (
                    "Human operator rejected "
                    "the escalation."
                ),
            },
        )

        assert (
                duplicate_response.status_code
                == 200
        )

        # Rejected actions cannot later be approved.
        approve_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/approve"
        )

        assert approve_response.status_code == 409

    await db_session.refresh(
        business_request
    )

    await db_session.refresh(action)

    assert action.status == "rejected"

    assert (
            business_request.status
            == "completed"
    )

    audit_result = await db_session.execute(
        select(AuditEvent)
        .where(
            AuditEvent.agent_action_id
            == action.id
        )
        .order_by(
            AuditEvent.event_sequence
        )
    )

    audit_events = list(
        audit_result.scalars().all()
    )

    # Duplicate reject must not create
    # another audit event.
    assert len(audit_events) == 1

    audit_event = audit_events[0]

    assert (
            audit_event.event_type
            == "action_rejected"
    )

    assert audit_event.event_sequence is not None
    assert audit_event.actor_type == "human"

    assert (
            audit_event.business_request_id
            == business_request.id
    )

    assert (
            audit_event.agent_action_id
            == action.id
    )

    assert (
            audit_event.details["tool_name"]
            == "escalate_incident"
    )

    assert (
            audit_event.details["reason"]
            == (
                "Human operator rejected "
                "the escalation."
            )
    )


async def test_approve_execution_failure_keeps_action_pending(
        override_database,
        db_session,
        monkeypatch,
):
    business_request, action = (
        await create_agent_action(
            db_session,
        )
    )

    def failing_tool(
            name,
            arguments,
    ):
        raise RuntimeError(
            "External dependency failed"
        )

    monkeypatch.setattr(
        agent_approval_service,
        "execute_approved_tool",
        failing_tool,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/agent-actions/"
            f"{action.id}/approve"
        )

    assert response.status_code == 500

    await db_session.refresh(action)

    await db_session.refresh(
        business_request
    )

    assert (
            action.status
            == "pending_approval"
    )

    assert (
            business_request.status
            == "awaiting_approval"
    )

    audit_result = await db_session.execute(
        select(AuditEvent)
        .where(
            AuditEvent.agent_action_id
            == action.id
        )
        .order_by(
            AuditEvent.event_sequence
        )
    )

    audit_events = list(
        audit_result.scalars().all()
    )

    assert len(audit_events) == 2

    assert [
               event.event_type
               for event in audit_events
           ] == [
               "action_approved",
               "tool_failed",
           ]

    approved_event = audit_events[0]
    failed_event = audit_events[1]

    assert (
            approved_event.event_sequence
            is not None
    )

    assert (
            failed_event.event_sequence
            is not None
    )

    assert (
            approved_event.event_sequence
            < failed_event.event_sequence
    )

    assert approved_event.actor_type == "human"
    assert failed_event.actor_type == "system"

    assert (
            failed_event.details["tool_name"]
            == "escalate_incident"
    )

    assert (
            failed_event.details["error_type"]
            == "RuntimeError"
    )


async def test_agent_action_not_found(
        override_database,
):
    missing_id = uuid.uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        approve_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{missing_id}/approve"
        )

        assert (
                approve_response.status_code
                == 404
        )

        reject_response = await client.post(
            f"/api/v1/agent-actions/"
            f"{missing_id}/reject"
        )

        assert (
                reject_response.status_code
                == 404
        )