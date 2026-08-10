"""Offline contract tests for the live nlp2dsl conversation provider."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from testql.adapters.nlp2dsl.live_llm import LiveLLMProvider
from testql.contracts.nlp2dsl_conversation import (
    CONTRACT_VERSION,
    load_schema,
    validate_payload,
)

FIXTURES = (
    Path(__file__).parent / "fixtures" / "contracts" / "nlp2dsl-conversation" / "v1"
)
CONTRACTS = (
    Path(__file__).parents[1] / "testql" / "contracts" / "nlp2dsl_conversation" / "v1"
)


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_fixture_passes_runtime_contract() -> None:
    payload = _fixture("valid-conversation-fields.json")
    validate_payload(payload)
    assert LiveLLMProvider._parse_json_object(json.dumps(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        _fixture("invalid-conversation-fields.json"),
        {"contractVersion": "2.0.0", "fields": {"recipient": "a@b.c"}},
        {"contractVersion": "1.0.0", "fields": {}},
        {"contractVersion": "1.0.0", "fields": {"bad key": "value"}},
    ],
)
def test_invalid_payloads_fail_closed(payload: dict) -> None:
    with pytest.raises(ValueError, match="violates ConversationFields v1"):
        validate_payload(payload)


def test_parser_rejects_markdown_fence() -> None:
    with pytest.raises(ValueError, match="single JSON object"):
        LiveLLMProvider._parse_json_object('```json\n{"contractVersion":"1.0.0"}\n```')


def test_reply_rejects_fields_not_requested(monkeypatch) -> None:
    provider = LiveLLMProvider(api_key="test")
    monkeypatch.setattr(
        provider,
        "_chat",
        lambda prompt: json.dumps(
            {"contractVersion": "1.0.0", "fields": {"admin": "true"}}
        ),
    )
    with pytest.raises(ValueError, match="outside missing set: admin"):
        provider.reply_for("conv", missing=["recipient"])


def test_openrouter_request_uses_schema_app_name_and_normalized_model(
    monkeypatch, tmp_path: Path
) -> None:
    project = tmp_path / "dialog-app"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("OPENROUTER_APP_URL", "https://example.test/dialog")
    monkeypatch.delenv("OPENROUTER_APP_NAME", raising=False)
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["payload"] = json.loads(request.content)
        content = json.dumps(
            {"contractVersion": "1.0.0", "fields": {"recipient": "a@b.c"}}
        )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": content}}]}
        )

    provider = LiveLLMProvider(
        api_key="test",
        model="openrouter/z-ai/glm-5.2",
        extra_headers={},
    )
    real_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler)),
    )
    assert provider.reply_for("conv", missing=["recipient"]) == {"recipient": "a@b.c"}
    assert captured["headers"]["x-title"] == "dialog-app"
    assert captured["headers"]["http-referer"] == "https://example.test/dialog"
    assert captured["payload"]["model"] == "z-ai/glm-5.2"
    assert (
        captured["payload"]["response_format"]["json_schema"]["schema"] == load_schema()
    )


def test_manifest_binds_artifacts_to_live_provider() -> None:
    manifest = json.loads((CONTRACTS / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == CONTRACT_VERSION
    assert manifest["boundary"].endswith("LiveLLMProvider.reply_for")
    for artifact in manifest["artifacts"].values():
        assert (CONTRACTS / artifact).is_file()
    proto = (CONTRACTS / "conversation-fields.proto").read_text(encoding="utf-8")
    grammar = (CONTRACTS / "conversation-fields.gbnf").read_text(encoding="utf-8")
    assert "map<string, string> fields = 2;" in proto
    assert f'\\"{CONTRACT_VERSION}\\"' in grammar
