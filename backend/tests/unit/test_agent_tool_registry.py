import pytest
from pydantic import ValidationError

from backend.app.agent.registry import (
    execute_registered_tool,
    get_tool_specs,
)


def test_tool_specs_include_incident_escalation():
    tools = get_tool_specs()

    assert len(tools) == 1

    tool = tools[0]

    assert tool["type"] == "function"

    function = tool["function"]

    assert function["name"] == "escalate_incident"

    parameters = function["parameters"]

    assert "reason" in parameters["properties"]
    assert "severity" in parameters["properties"]


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


def test_tool_arguments_are_validated():
    with pytest.raises(ValidationError):
        execute_registered_tool(
            name="escalate_incident",
            arguments={
                "reason": "Production outage",
                "severity": "invalid",
            },
        )