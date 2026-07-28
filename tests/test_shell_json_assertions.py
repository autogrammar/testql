"""Tests for ASSERT_STDOUT_JSON (testql.interpreter._shell).

ASSERT_STDOUT_CONTAINS can only match a substring of a command's output, which
is not enough for tools that print a JSON report: it cannot compare numbers,
it is whitespace-sensitive, and it matches a nested occurrence of a key just as
happily as the intended one. These tests cover the JSON-aware assertion.
"""

from __future__ import annotations

import pytest

from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine
from testql.interpreter._shell import _extract_json


REPORT = '{"schema":"demo.audit.v1","ok":true,"summary":{"findings":0,"profiles":14},"findings":[]}'


def line(args: str) -> OqlLine:
    return OqlLine(number=1, command="ASSERT_STDOUT_JSON", args=args, raw=f"ASSERT_STDOUT_JSON {args}")


def shell(interpreter: OqlInterpreter, command: str) -> None:
    interpreter._cmd_shell(f'"{command}" 5000', OqlLine(number=1, command="SHELL", args="", raw=""))


def emit(interpreter: OqlInterpreter, tmp_path, payload: str) -> None:
    """Run a command whose stdout is `payload`.

    SHELL parses its argument with shlex, so a literal JSON document cannot be
    inlined into the command without fighting the quoting. Reading it back from
    a file is also closer to how the assertion is used in practice.
    """
    target = tmp_path / "report.json"
    target.write_text(payload, encoding="utf-8")
    shell(interpreter, f"cat {target}")


class TestExtractJson:
    """The parser must accept real CLI output, not only pristine JSON."""

    def test_plain_document(self):
        document, error = _extract_json(REPORT)
        assert error is None
        assert document["ok"] is True

    def test_leading_banner_is_tolerated(self):
        document, error = _extract_json(f"tool v1.2.3 starting\n{REPORT}")
        assert error is None
        assert document["summary"]["profiles"] == 14

    def test_empty_stdout_is_an_error(self):
        document, error = _extract_json("   ")
        assert document is None
        assert "empty" in error

    def test_non_json_stdout_is_an_error(self):
        document, error = _extract_json("everything is fine")
        assert document is None
        assert "no JSON document" in error

    def test_malformed_json_is_an_error(self):
        document, error = _extract_json('{"ok": tru')
        assert document is None
        assert "not valid JSON" in error


class TestAssertStdoutJson:
    @pytest.fixture
    def interpreter(self):
        return OqlInterpreter(api_url="http://localhost:8101", quiet=True)

    @pytest.fixture
    def reported(self, interpreter, tmp_path):
        emit(interpreter, tmp_path, REPORT)
        return interpreter

    def test_boolean_equality(self, reported):
        reported._cmd_assert_stdout_json("ok == true", line("ok == true"))
        assert reported.results[-1].status.value == "passed"

    def test_nested_numeric_equality(self, reported):
        reported._cmd_assert_stdout_json("summary.findings == 0", line("summary.findings == 0"))
        assert reported.results[-1].status.value == "passed"

    def test_numeric_comparison(self, reported):
        reported._cmd_assert_stdout_json("summary.profiles >= 14", line("summary.profiles >= 14"))
        assert reported.results[-1].status.value == "passed"

    def test_string_equality_ignores_quoting_style(self, reported):
        reported._cmd_assert_stdout_json('schema == "demo.audit.v1"', line('schema == "demo.audit.v1"'))
        assert reported.results[-1].status.value == "passed"

    def test_array_length(self, reported):
        reported._cmd_assert_stdout_json("findings.length == 0", line("findings.length == 0"))
        assert reported.results[-1].status.value == "passed"

    def test_whole_document_path(self, interpreter, tmp_path):
        emit(interpreter, tmp_path, "[1,2,3]")
        interpreter._cmd_assert_stdout_json(". length 3", line(". length 3"))
        # `length` is not a comparison operator; the unknown-operator path must fail.
        assert interpreter.results[-1].status.value == "failed"

    def test_failed_comparison_is_reported(self, reported):
        reported._cmd_assert_stdout_json("summary.findings == 3", line("summary.findings == 3"))
        assert reported.results[-1].status.value == "failed"
        assert reported.errors

    def test_missing_path_fails_rather_than_passes(self, reported):
        reported._cmd_assert_stdout_json("summary.missing >= 1", line("summary.missing >= 1"))
        assert reported.results[-1].status.value == "failed"
        assert "not found" in reported.results[-1].message

    def test_non_json_output_fails(self, interpreter):
        shell(interpreter, "echo not json at all")
        interpreter._cmd_assert_stdout_json("ok == true", line("ok == true"))
        assert interpreter.results[-1].status.value == "failed"

    def test_unknown_operator_fails(self, reported):
        reported._cmd_assert_stdout_json("ok ~= true", line("ok ~= true"))
        assert reported.results[-1].status.value == "failed"
        assert "unknown operator" in reported.results[-1].message

    def test_missing_arguments_fail(self, interpreter):
        interpreter._cmd_assert_stdout_json("ok", line("ok"))
        assert interpreter.results[-1].status.value == "failed"

    def test_without_previous_shell_command_warns(self, interpreter):
        interpreter._cmd_assert_stdout_json("ok == true", line("ok == true"))
        assert any("No previous" in entry for entry in interpreter.out.lines)

    def test_contains_operator(self, reported):
        reported._cmd_assert_stdout_json("schema CONTAINS audit", line("schema CONTAINS audit"))
        assert reported.results[-1].status.value == "passed"


class TestAssertStdoutJsonDryRun:
    @pytest.fixture
    def interpreter(self):
        return OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)

    def test_dry_run_skips_without_output(self, interpreter):
        shell(interpreter, "node scripts/audit.mjs --json")
        interpreter._cmd_assert_stdout_json("ok == true", line("ok == true"))
        assert interpreter.results[-1].status.value == "passed"
