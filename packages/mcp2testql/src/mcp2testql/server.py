"""FastMCP server exposing TestQL control tools."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

_MUTATION_ENV = "TESTQL_MCP_ALLOW_MUTATION"


def _require_mutation(action: str) -> None:
    enabled = os.getenv(_MUTATION_ENV, "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        raise PermissionError(
            f"MCP mutation '{action}' is disabled; start the server with {_MUTATION_ENV}=1"
        )


def _require_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP

        return FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "MCP support requires optional dependency 'mcp'. Install with: pip install mcp",
        ) from exc


@dataclass
class TestqlMCPServer:
    """Expose TestQL query/patch/validate/generate via MCP tools."""

    name: str = "testql"

    def __post_init__(self) -> None:
        FastMCP = _require_fastmcp()
        self.app = FastMCP(self.name)
        self._register_tools()

    def _register_tools(self) -> None:
        from dsl2testql import dispatch, execute_dsl, execute_dsl_line
        from dsl2testql.pb_codec import encode_result_protobuf
        from uri2testql.materialize import materialize_uri
        from uri2testql.patch import apply_uri, patch_uri, update_uri
        from uri2testql.query import query_uri

        @self.app.tool()
        def testql_query(uri: str, file: str = "", fmt: str = "json") -> dict[str, Any]:
            """Query a testql:// URI or block selector."""
            result = query_uri(uri, file=file or None, fmt=fmt)
            return result.to_dict()

        @self.app.tool()
        def testql_materialize(uri: str, dest: str = "") -> dict[str, Any]:
            """Materialize addressed TestQL content to a file."""
            _require_mutation("testql_materialize")
            result = materialize_uri(uri, dest=dest or None)
            return result.to_dict()

        @self.app.tool()
        def testql_validate(path: str) -> dict[str, Any]:
            """Validate a .testql.less manifest."""
            from nlp2testql.validate import validate_testql_file

            return validate_testql_file(path)

        @self.app.tool()
        def testql_run_dsl(script: str, default_file: str = "") -> list[dict[str, Any]]:
            """Execute TestQL control DSL commands (one per line)."""
            _require_mutation("testql_run_dsl")
            results = execute_dsl(script, default_file=default_file or None)
            return [r.to_dict() for r in results]

        @self.app.tool()
        def testql_run_command(command: str, default_file: str = "") -> dict[str, Any]:
            """Execute a single TestQL control DSL command."""
            _require_mutation("testql_run_command")
            result = execute_dsl_line(command, default_file=default_file or None)
            return result.to_dict()

        @self.app.tool()
        def testql_run_command_pb(envelope_bytes: bytes, default_file: str = "") -> bytes:
            """Execute protobuf DslEnvelope; returns DslResult protobuf."""
            _require_mutation("testql_run_command_pb")
            result = dispatch(envelope_bytes, default_file=default_file or None)
            return encode_result_protobuf(result)

        @self.app.tool()
        def testql_patch(uri: str, content: str, file: str = "") -> dict[str, Any]:
            """Replace a TestQL block referenced by URI."""
            _require_mutation("testql_patch")
            result = patch_uri(uri, content=content, file=file or None)
            return result.to_dict()

        @self.app.tool()
        def testql_update(uri: str, content: str, file: str = "") -> dict[str, Any]:
            """Update a TestQL block referenced by URI."""
            _require_mutation("testql_update")
            result = update_uri(uri, content=content, file=file or None)
            return result.to_dict()

        @self.app.tool()
        def testql_apply(
            uri: str,
            mode: str = "materialize",
            dest: str = "",
            content: str = "",
            file: str = "",
        ) -> dict[str, Any]:
            """Apply URI action: materialize, patch, append, update."""
            _require_mutation("testql_apply")
            result = apply_uri(
                uri,
                dest=dest or None,
                content=content or None,
                file=file or None,
                mode=mode,
            )
            return result.to_dict()

    def run(self) -> None:
        self.app.run()


def create_server(name: str = "testql") -> TestqlMCPServer:
    return TestqlMCPServer(name=name)


def run_server() -> None:
    create_server().run()


if __name__ == "__main__":
    run_server()
