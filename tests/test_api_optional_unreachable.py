"""Unreachable hosts are status 0; optional rows skip instead of failing the suite."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from testql.base import StepStatus
from testql.interpreter import OqlInterpreter
from testql.interpreter._api_runner import _is_optional_flag, _split_optional_api_args
from testql.interpreter._testtoon_parser import testtoon_to_oql as _testtoon_to_oql


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/ok":
            body = b'{"ok": true, "service": "fixture"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/denied":
            body = b'{"ok": false, "schema": "subactor.problem.v1", "status": 401}'
            self.send_response(401)
            self.send_header("Content-Type", "application/problem+json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def _serve() -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, f"http://{host}:{port}"


class TestOptionalFlagParsing:
    def test_split_optional_token(self):
        args, optional = _split_optional_api_args('GET "http://x/" optional')
        assert optional is True
        assert args == 'GET "http://x/"'

    def test_json_body_is_not_optional(self):
        args, optional = _split_optional_api_args('POST "/x" {"optional": true}')
        assert optional is False
        assert "optional" in args

    def test_toon_true_is_optional(self):
        assert _is_optional_flag("true")
        assert _is_optional_flag("optional")
        assert not _is_optional_flag(None)
        assert not _is_optional_flag("-")


class TestToonExpansion:
    def test_optional_and_contains_columns(self):
        source = (
            "API[1]{method, endpoint, status, contains, optional}:\n"
            "  GET,  https://example.invalid/health,  200,  ok,  true\n"
        )
        script = _testtoon_to_oql(source, "opt.testql.toon.yaml")
        assert script.lines[0].command == "API"
        assert script.lines[0].args.endswith(" optional")
        assert script.lines[1].command == "ASSERT_STATUS"
        assert script.lines[1].args == "200"
        assert script.lines[2].command == "ASSERT_CONTAINS"
        assert "ok" in script.lines[2].args


class TestLiveHttp:
    def test_401_is_captured_then_asserted(self):
        server, base = _serve()
        try:
            interp = OqlInterpreter(quiet=True, timeout_ms=3000)
            result = interp.run(
                f'API GET "{base}/denied"\nASSERT_STATUS 401\nASSERT_JSON schema == "subactor.problem.v1"\n',
                "denied.tql",
            )
            assert result.ok, result.errors
        finally:
            server.shutdown()

    def test_required_unreachable_is_status_zero(self):
        interp = OqlInterpreter(quiet=True, timeout_ms=2000)
        result = interp.run(
            'API GET "http://127.0.0.1:1/"\nASSERT_STATUS 0\nASSERT_JSON error == "unreachable"\n',
            "down.tql",
        )
        assert result.ok, result.errors
        assert interp.last_status == 0

    def test_optional_unreachable_skips_asserts(self):
        interp = OqlInterpreter(quiet=True, timeout_ms=2000)
        result = interp.run(
            'API GET "http://127.0.0.1:1/" optional\nASSERT_STATUS 200\nASSERT_CONTAINS "ok"\n',
            "opt.tql",
        )
        assert result.ok, result.errors
        skipped = [s for s in result.steps if s.status == StepStatus.SKIPPED]
        assert len(skipped) >= 2
        assert any("optional" in (s.message or "") for s in skipped)

    def test_optional_up_target_still_asserts(self):
        server, base = _serve()
        try:
            interp = OqlInterpreter(quiet=True, timeout_ms=3000)
            result = interp.run(
                f'API GET "{base}/ok" optional\nASSERT_STATUS 200\nASSERT_CONTAINS "fixture"\n',
                "opt-up.tql",
            )
            assert result.ok, result.errors
            assert all(s.status != StepStatus.SKIPPED for s in result.steps)
        finally:
            server.shutdown()

    def test_dry_run_accepts_non_200_status_asserts(self):
        interp = OqlInterpreter(quiet=True, dry_run=True)
        result = interp.run(
            'API GET "http://127.0.0.1:18081/api/me"\nASSERT_STATUS 401\nASSERT_CONTAINS "authentication-required"\n',
            "dry.tql",
        )
        assert result.ok, result.errors
