"""Dry-run distinguishes syntax validation from physical execution."""
import json
from unittest.mock import patch

from click.testing import CliRunner
import pytest

from testql.cli import cli
from testql.interpreter import OqlInterpreter


def test_dry_run_validates_response_assertions_without_http(tmp_path):
    path = tmp_path / "readiness.testql.toon.yaml"
    path.write_text('''API GET http://127.0.0.1:1/readiness
ASSERT_STATUS 200
ASSERT_JSON ready == true
ASSERT_JSON devices.length >= 2
ASSERT_CONTAINS "ready"
ASSERT_HEADERS Content-Type == "application/json"
ASSERT_COOKIES session exists
ASSERT_SCHEMA '{"type": "object", "required": ["ready"]}'
''')
    with patch.object(OqlInterpreter, "_do_http_request_with_retry", side_effect=AssertionError("network contacted")) as http:
        result = CliRunner().invoke(cli, ["run", str(path), "--dry-run", "--quiet", "--output", "json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["executed"] == 0
    assert data["validated"] == 8
    assert data["passed"] == 0
    http.assert_not_called()


@pytest.mark.parametrize("command", [
    "ASSERT_JSON ready",
    "ASSERT_JSON ready UNKNOWN true",
    "ASSERT_STATUS invalid",
    "ASSERT_HEADERS Content-Type",
    "ASSERT_HEADERS Content-Type UNKNOWN json",
    "ASSERT_COOKIES session ==",
    "ASSERT_COOKIES session UNKNOWN value",
    "NOT_A_TESTQL_COMMAND",
])
def test_dry_run_rejects_invalid_assertions_and_unknown_commands(tmp_path, command):
    path = tmp_path / "invalid.oql"
    path.write_text(command)
    result = CliRunner().invoke(cli, ["run", str(path), "--dry-run", "--quiet", "--output", "json"])

    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["ok"] is False


def test_live_assertions_still_require_real_response_values():
    result = OqlInterpreter(quiet=True).run("ASSERT_JSON ready == true")
    assert result.ok is False
    assert result.failed == 1


def test_live_header_cookie_and_schema_assertions_still_evaluate_response():
    pytest.importorskip("jsonschema")
    interp = OqlInterpreter(quiet=True)
    interp.last_response = {"ready": True}
    interp.vars.set("_headers", {"Content-Type": "application/json", "Set-Cookie": "session=active"})
    result = interp.run('''ASSERT_HEADERS Content-Type == "application/json"
ASSERT_COOKIES session exists
ASSERT_SCHEMA '{"type": "object", "required": ["ready"]}'
ASSERT_COOKIES missing exists
ASSERT_SCHEMA '{"type": "object", "required": ["absent"]}'
''')
    assert result.ok is False
    assert result.passed == 3
    assert result.failed == 2
