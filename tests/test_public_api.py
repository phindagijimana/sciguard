"""Public import, agent tool, optional MCP. No model API."""

from __future__ import annotations

import os
from pathlib import Path

from sciguard import validate
from sciguard.agent import TOOLS, call_tool
from sciguard.mcp import handle_message

ROOT = Path(__file__).resolve().parents[1]
FAIL_WF = ROOT / "fixtures/invalid/labels_t1w_to_dwi_no_transform.yaml"
UNKNOWN_WF = ROOT / "fixtures/unknown/space_omitted.yaml"


def test_public_validate_fail_and_unknown() -> None:
    os.environ.pop("OPENAI_API_KEY", None)
    failed = validate(FAIL_WF)
    assert failed["certificate_of_scientific_correctness"] is False
    assert any(edge["status"] == "FAIL" for edge in failed["edges"])
    unknown = validate(UNKNOWN_WF)
    assert any(edge["status"] == "UNKNOWN" for edge in unknown["edges"])


def test_agent_tool_matches_validate() -> None:
    via = call_tool("validate", {"workflow": str(FAIL_WF)})
    assert any(edge["status"] == "FAIL" for edge in via["edges"])
    assert {tool["name"] for tool in TOOLS} == {"validate"}


def test_mcp_tools_call_validate() -> None:
    listed = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert [tool["name"] for tool in listed["result"]["tools"]] == ["validate"]
    called = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "validate", "arguments": {"workflow": str(FAIL_WF)}},
        }
    )
    assert called["result"]["isError"] is False
    assert "FAIL" in called["result"]["content"][0]["text"]
