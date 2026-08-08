"""Offline contract tests for the nlp2env LLM-to-MCP boundary."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from testql.contracts.nlp2env import CONTRACT_VERSION, load_schema, validate_tool_call
from testql.nlp2env import llm

FIXTURES = Path(__file__).parent / "fixtures" / "contracts" / "nlp2env" / "v1"
CONTRACTS = Path(llm.__file__).parents[1] / "contracts" / "nlp2env" / "v1"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_fixture_passes_runtime_validation() -> None:
    payload = _fixture("valid-tool-call.json")
    validate_tool_call(payload)
    assert llm._extract_json_object(json.dumps(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        _fixture("invalid-tool-call.json"),
        {"contractVersion": "2.0.0", "tool": "nlp2env_list", "arguments": {}},
        {"contractVersion": "1.0.0", "tool": "shell", "arguments": {}},
        {"contractVersion": "1.0.0", "tool": "nlp2env_list", "arguments": {"x": "y"}},
    ],
)
def test_invalid_or_unsafe_calls_fail_closed(payload: dict) -> None:
    with pytest.raises(ValueError, match="violates nlp2env ToolCall v1"):
        validate_tool_call(payload)


def test_parser_rejects_markdown_or_surrounding_prose() -> None:
    with pytest.raises(ValueError, match="single JSON object"):
        llm._extract_json_object('```json\n{"tool":"nlp2env_list"}\n```')


def test_openrouter_request_uses_schema_and_project_app_name(
    monkeypatch, tmp_path: Path
) -> None:
    project = tmp_path / "customer-project"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_APP_NAME", raising=False)
    captured: dict = {}

    def fake_post(url, payload, headers=None):
        captured.update(url=url, payload=payload, headers=headers)
        content = json.dumps(
            {"contractVersion": "1.0.0", "tool": "nlp2env_list", "arguments": {}}
        )
        return {"choices": [{"message": {"content": content}}]}

    monkeypatch.setattr(llm, "_http_post_json", fake_post)
    assert llm.translate_nl_to_mcp("list", "openrouter", "openrouter/z-ai/glm-5.2") == (
        "nlp2env_list",
        {},
    )
    assert captured["headers"]["X-Title"] == "customer-project"
    assert (
        captured["payload"]["response_format"]["json_schema"]["schema"] == load_schema()
    )


def test_ollama_request_uses_the_same_schema(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url, payload, headers=None):
        captured.update(url=url, payload=payload, headers=headers)
        content = json.dumps(
            {
                "contractVersion": "1.0.0",
                "tool": "nlp2env_email_status",
                "arguments": {},
            }
        )
        return {"message": {"content": content}}

    monkeypatch.setattr(llm, "_http_post_json", fake_post)
    assert llm.translate_nl_to_mcp("status", "ollama", "ollama/glm") == (
        "nlp2env_email_status",
        {},
    )
    assert captured["payload"]["format"] == load_schema()


def test_manifest_and_artifacts_bind_the_runtime_boundary() -> None:
    manifest = json.loads((CONTRACTS / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == CONTRACT_VERSION
    assert manifest["boundary"] == "testql.nlp2env.llm.translate_nl_to_mcp"
    for name in manifest["artifacts"].values():
        assert (CONTRACTS / name).is_file()
    grammar = (CONTRACTS / "tool-call.gbnf").read_text(encoding="utf-8")
    proto = (CONTRACTS / "tool-call.proto").read_text(encoding="utf-8")
    assert f'\\"{CONTRACT_VERSION}\\"' in grammar
    assert '\\"SMTP_PASSWORD\\"' in grammar
    schema_tools = set(load_schema()["properties"]["tool"]["enum"])
    proto_tools = set(re.findall(r"^  (nlp2env_\w+) = \d+;", proto, re.MULTILINE))
    assert proto_tools == schema_tools
    assert 'json_name = "contractVersion"' in proto
