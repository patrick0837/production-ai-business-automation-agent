import pytest
from pydantic import ValidationError

from backend.app.agent.registry import (
    execute_approved_tool,
    execute_registered_tool,
    get_tool_specs,
)


def test_tool_specs_include_protected_tools():
    tools = get_tool_specs()

    assert len(tools) == 2

    functions = {
        tool["function"]["name"]: tool["function"]
        for tool in tools
    }

    assert set(functions) == {
        "escalate_incident",
        "request_reimbursement",
    }

    incident_parameters = (
        functions["escalate_incident"]["parameters"]
    )

    assert (
            "reason"
            in incident_parameters["properties"]
    )
    assert (
            "severity"
            in incident_parameters["properties"]
    )

    reimbursement_parameters = (
        functions["request_reimbursement"]["parameters"]
    )

    assert (
            "reason"
            in reimbursement_parameters["properties"]
    )
    assert (
            "amount"
            in reimbursement_parameters["properties"]
    )
    assert (
            "currency"
            in reimbursement_parameters["properties"]
    )


def test_incident_escalation_requires_approval():
    result = execute_registered_tool(
        name="escalate_incident",
        arguments={
            "reason": (
                "Production payment system is down."
            ),
            "severity": "urgent",
        },
    )

    assert result.tool_name == "escalate_incident"
    assert result.status == "approval_required"

    assert (
            result.output["arguments"]["severity"]
            == "urgent"
    )


def test_reimbursement_requires_approval():
    result = execute_registered_tool(
        name="request_reimbursement",
        arguments={
            "reason": (
                "Customer requested reimbursement "
                "for a failed service."
            ),
            "amount": 80.0,
            "currency": "EUR",
        },
    )

    assert (
            result.tool_name
            == "request_reimbursement"
    )

    assert result.status == "approval_required"

    arguments = result.output["arguments"]

    assert arguments["reason"] == (
        "Customer requested reimbursement "
        "for a failed service."
    )

    assert arguments["amount"] == 80.0
    assert arguments["currency"] == "EUR"


def test_reimbursement_can_omit_amount():
    result = execute_registered_tool(
        name="request_reimbursement",
        arguments={
            "reason": (
                "Customer requested reimbursement "
                "for the failed service."
            ),
        },
    )

    assert result.status == "approval_required"

    arguments = result.output["arguments"]

    assert arguments["amount"] is None
    assert arguments["currency"] == "EUR"


def test_approved_reimbursement_is_simulated():
    result = execute_approved_tool(
        name="request_reimbursement",
        arguments={
            "reason": (
                "Approved customer reimbursement."
            ),
            "amount": 80.0,
            "currency": "eur",
        },
    )

    assert result.status == "completed"

    assert (
            result.tool_name
            == "request_reimbursement"
    )

    assert result.output["amount"] == 80.0
    assert result.output["currency"] == "EUR"
    assert result.output["simulated"] is True


def test_reimbursement_amount_is_validated():
    with pytest.raises(ValidationError):
        execute_registered_tool(
            name="request_reimbursement",
            arguments={
                "reason": (
                    "Refund the customer."
                ),
                "amount": -10,
                "currency": "EUR",
            },
        )


def test_incident_tool_arguments_are_validated():
    with pytest.raises(ValidationError):
        execute_registered_tool(
            name="escalate_incident",
            arguments={
                "reason": "Production outage",
                "severity": "invalid",
            },
        )