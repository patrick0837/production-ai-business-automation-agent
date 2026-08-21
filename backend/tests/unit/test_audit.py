import uuid

from backend.app.services.audit import (
    create_audit_event,
)


def test_create_audit_event():
    business_request_id = uuid.uuid4()
    agent_action_id = uuid.uuid4()

    event = create_audit_event(
        event_type="action_approved",
        actor_type="human",
        business_request_id=(
            business_request_id
        ),
        agent_action_id=agent_action_id,
        details={
            "tool_name": "escalate_incident",
        },
    )

    assert (
            event.business_request_id
            == business_request_id
    )

    assert (
            event.agent_action_id
            == agent_action_id
    )

    assert (
            event.event_type
            == "action_approved"
    )

    assert event.actor_type == "human"
    assert event.actor_id is None

    assert (
            event.details["tool_name"]
            == "escalate_incident"
    )


def test_create_audit_event_uses_empty_details():
    event = create_audit_event(
        event_type="approval_required",
        actor_type="system",
    )

    assert event.details == {}