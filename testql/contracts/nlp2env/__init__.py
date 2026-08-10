"""Runtime binding for the nlp2env LLM-to-MCP ToolCall contract."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

CONTRACT_VERSION = "1.0.0"


def _contract_file(name: str):
    return files(__package__).joinpath("v1", name)


def load_schema() -> dict[str, Any]:
    return json.loads(
        _contract_file("tool-call.schema.json").read_text(encoding="utf-8")
    )


def validate_tool_call(payload: object) -> None:
    validator = Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        raise ValueError(
            f"LLM response violates nlp2env ToolCall v1 at {location}: {first.message}"
        )


def openai_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "nlp2env_tool_call_v1",
            "strict": True,
            "schema": load_schema(),
        },
    }


__all__ = [
    "CONTRACT_VERSION",
    "load_schema",
    "openai_response_format",
    "validate_tool_call",
]
