"""Runtime binding for the nlp2dsl ConversationFields response contract."""

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
        _contract_file("conversation-fields.schema.json").read_text(encoding="utf-8")
    )


def validate_payload(payload: object) -> None:
    validator = Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        raise ValueError(
            f"live LLM response violates ConversationFields v1 at {location}: {first.message}"
        )


def response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "testql_conversation_fields_v1",
            "strict": True,
            "schema": load_schema(),
        },
    }


__all__ = ["CONTRACT_VERSION", "load_schema", "response_format", "validate_payload"]
