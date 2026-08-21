import uuid

from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.models.agent_action import AgentAction
from backend.app.models.audit_event import AuditEvent
from backend.app.models.business_request import BusinessRequest


async def create_audit_test_data(
        db_session,
):
    business_request = BusinessRequest(
        source="integration-test",
        content="Production checkout service is down.",
        status="completed",
        celery_task_id=str(uuid.uuid4()),
        category="support",
        priority="urgent",
        intent="service_outage",
        requires_human_approval=True,
        recommended_action="Escalate incident.",
    )

    db_session.add(business_request)
    await db_session.flush()

    action = AgentAction(
        business_request_id=business_request.id,
        tool_call_id=str(uuid.uuid4()),
        tool_name="escalate_incident",
        arguments={
            "reason": (
                "Production checkout service is down."
            ),
            "severity": "urgent",
        },
        status="completed",
        requires_approval=True,
        result={
            "message": "Incident escalation completed.",
        },
    )

    db_session.add(action)
    await db_session.flush()

    event_types = [
        (
            "agent_tool_requested",
            "agent",
        ),
        (
            "approval_required",
            "system",
        ),
        (
            "action_approved",
            "human",
        ),
        (
            "tool_executed",
            "system",
        ),
    ]

    primary_events = []

    for event_type, actor_type in event_types:
        event = AuditEvent(
            business_request_id=business_request.id,
            agent_action_id=action.id,
            event_type=event_type,
            actor_type=actor_type,
            details={
                "tool_name": "escalate_incident",
            },
        )

        db_session.add(event)

        # Assign event_sequence immediately so
        # deterministic ordering can be tested.
        await db_session.flush()

        primary_events.append(event)

    unrelated_request = BusinessRequest(
        source="integration-test",
        content="Unrelated request.",
        status="completed",
        celery_task_id=str(uuid.uuid4()),
    )

    db_session.add(unrelated_request)
    await db_session.flush()

    unrelated_action = AgentAction(
        business_request_id=unrelated_request.id,
        tool_call_id=str(uuid.uuid4()),
        tool_name="escalate_incident",
        arguments={
            "reason": "Unrelated request.",
            "severity": "high",
        },
        status="rejected",
        requires_approval=True,
        result={
            "decision": "rejected",
        },
    )

    db_session.add(unrelated_action)
    await db_session.flush()

    unrelated_event = AuditEvent(
        business_request_id=unrelated_request.id,
        agent_action_id=unrelated_action.id,
        event_type="action_rejected",
        actor_type="human",
        details={
            "tool_name": "escalate_incident",
        },
    )

    db_session.add(unrelated_event)
    await db_session.flush()

    await db_session.commit()

    return (
        business_request,
        action,
        primary_events,
        unrelated_event,
    )


async def test_list_audit_events_in_sequence_order(
        override_database,
        db_session,
):
    (
        _,
        _,
        primary_events,
        unrelated_event,
    ) = await create_audit_test_data(
        db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/audit-events"
        )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 5

    sequences = [
        event["event_sequence"]
        for event in events
    ]

    assert sequences == sorted(sequences)

    assert [
               event["event_type"]
               for event in events
           ] == [
               "agent_tool_requested",
               "approval_required",
               "action_approved",
               "tool_executed",
               "action_rejected",
           ]

    assert (
            primary_events[0].event_sequence
            < primary_events[1].event_sequence
            < primary_events[2].event_sequence
            < primary_events[3].event_sequence
            < unrelated_event.event_sequence
    )


async def test_filter_audit_events_by_business_request(
        override_database,
        db_session,
):
    (
        business_request,
        _,
        _,
        _,
    ) = await create_audit_test_data(
        db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/audit-events",
            params={
                "business_request_id": (
                    str(business_request.id)
                ),
            },
        )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 4

    assert all(
        event["business_request_id"]
        == str(business_request.id)
        for event in events
    )

    assert [
               event["event_type"]
               for event in events
           ] == [
               "agent_tool_requested",
               "approval_required",
               "action_approved",
               "tool_executed",
           ]


async def test_filter_audit_events_by_agent_action(
        override_database,
        db_session,
):
    (
        _,
        action,
        _,
        _,
    ) = await create_audit_test_data(
        db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/audit-events",
            params={
                "agent_action_id": str(action.id),
            },
        )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 4

    assert all(
        event["agent_action_id"]
        == str(action.id)
        for event in events
    )


async def test_filter_audit_events_by_event_type(
        override_database,
        db_session,
):
    await create_audit_test_data(
        db_session,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/audit-events",
            params={
                "event_type": "action_approved",
            },
        )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1

    assert (
            events[0]["event_type"]
            == "action_approved"
    )

    assert (
            events[0]["actor_type"]
            == "human"
    )