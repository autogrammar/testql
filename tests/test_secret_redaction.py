"""Secrets imported with GETENV_SECRET must not survive into results.

Redacting the printed step label is not enough. A driver that fails mid-action
echoes back the value it was handed -- Playwright's `fill` timeout reports
`fill("<value>")` in its call log -- and that message is written verbatim into
the JSON artifact a CI job keeps. These tests cover the whole result payload.
"""

from __future__ import annotations

import json

import pytest

from testql.base import StepResult, StepStatus
from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


SECRET = "s3cr3t-admin-token-value"


@pytest.fixture
def interpreter(monkeypatch):
    monkeypatch.setenv("SUBACTOR_ADMIN_TOKEN", SECRET)
    instance = OqlInterpreter(api_url="http://localhost:8101", quiet=True)
    instance._cmd_getenv_secret(
        "SUBACTOR_ADMIN_TOKEN admin_token",
        OqlLine(number=1, command="GETENV_SECRET", args="", raw=""),
    )
    return instance


class TestRedact:
    def test_registered_secret_is_replaced(self, interpreter):
        assert interpreter.redact(f'fill("{SECRET}")') == 'fill("***REDACTED***")'

    def test_untracked_text_is_untouched(self, interpreter):
        assert interpreter.redact("nothing sensitive here") == "nothing sensitive here"

    def test_nested_structures_are_walked(self, interpreter):
        payload = {"log": [f"got {SECRET}"], "meta": {"body": SECRET}, "count": 3}
        assert interpreter.redact(payload) == {
            "log": ["got ***REDACTED***"],
            "meta": {"body": "***REDACTED***"},
            "count": 3,
        }

    def test_non_string_scalars_survive(self, interpreter):
        assert interpreter.redact(7) == 7
        assert interpreter.redact(None) is None
        assert interpreter.redact(True) is True

    def test_interpreter_without_secrets_is_a_passthrough(self):
        plain = OqlInterpreter(api_url="http://localhost:8101", quiet=True)
        assert plain.redact(f'fill("{SECRET}")') == f'fill("{SECRET}")'


class TestResultScrubbing:
    def test_step_message_name_and_details_are_scrubbed(self, interpreter):
        interpreter.results.append(StepResult(
            name=f'GUI_INPUT "#adminToken" "{SECRET}"',
            status=StepStatus.FAILED,
            message=f'Page.fill: Timeout 5000ms exceeded.\n  - fill("{SECRET}")',
            value=SECRET,
            details={"stdout": f"token={SECRET}", "returncode": 1},
        ))
        interpreter.errors.append(f"L14: fill failed with {SECRET}")
        interpreter.warnings.append(f"retrying with {SECRET}")

        interpreter._redact_results()

        step = interpreter.results[-1]
        assert SECRET not in step.name
        assert SECRET not in step.message
        assert SECRET not in str(step.value)
        assert SECRET not in json.dumps(step.details)
        assert "Timeout 5000ms exceeded" in step.message, "context must survive"
        assert step.details["returncode"] == 1, "non-string fields must survive"
        assert SECRET not in interpreter.errors[-1]
        assert SECRET not in interpreter.warnings[-1]

    def test_a_full_run_emits_no_secret(self, interpreter, tmp_path):
        # The whole serialized result is the artifact CI keeps; scan all of it.
        scenario = tmp_path / "leak.testql"
        scenario.write_text(
            "GETENV_SECRET SUBACTOR_ADMIN_TOKEN admin_token\n"
            'SHELL "echo ${admin_token}" 5000\n',
            encoding="utf-8",
        )
        result = interpreter.run(scenario.read_text(encoding="utf-8"), scenario.name)
        serialized = json.dumps({
            "steps": [
                {"name": s.name, "message": s.message, "details": s.details}
                for s in result.steps
            ],
            "variables": result.variables,
            "errors": result.errors,
            "warnings": result.warnings,
        }, default=str)
        assert SECRET not in serialized
