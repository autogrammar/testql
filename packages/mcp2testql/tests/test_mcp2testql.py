"""Safety tests for mcp2testql."""

import pytest

from mcp2testql.server import _require_mutation


def test_mcp_mutations_require_operator_capability(monkeypatch) -> None:
    monkeypatch.delenv("TESTQL_MCP_ALLOW_MUTATION", raising=False)
    with pytest.raises(PermissionError, match="TESTQL_MCP_ALLOW_MUTATION"):
        _require_mutation("testql_patch")

    monkeypatch.setenv("TESTQL_MCP_ALLOW_MUTATION", "true")
    _require_mutation("testql_patch")
