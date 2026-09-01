"""Contract tests for shared JSON, text and binary HTTP response handling."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pytest

from testql.base import StepStatus
from testql.http_response import parse_http_body
from testql.interpreter import OqlInterpreter
from testql.ir import ApiStep, Assertion
from testql.ir_runner.context import ExecutionContext
from testql.ir_runner.executors import api as ir_api


@dataclass
class _Response:
    body: bytes
    content_type: str
    status: int = 200

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": self.content_type,
            "Content-Length": str(len(self.body)),
        }

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _serve(monkeypatch: pytest.MonkeyPatch, response: _Response) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: response,
    )


def test_json_and_text_keep_their_compatibility_payloads() -> None:
    json_body = b'{"ok":true,"items":[1,2]}'
    json_result = parse_http_body(
        json_body, {"content-type": "application/problem+json; charset=utf-8"}
    )
    text_result = parse_http_body(
        b"service ready", {"Content-Type": "text/plain; charset=utf-8"}
    )
    list_result = parse_http_body(b'[1, 2]', {})

    assert json_result.data == {"ok": True, "items": [1, 2]}
    assert json_result.evidence == {
        "kind": "json",
        "content_type": "application/problem+json",
        "byte_length": len(json_body),
        "sha256": hashlib.sha256(json_body).hexdigest(),
        "magic": "json",
    }
    assert text_result.data == {"text": "service ready"}
    assert text_result.evidence["kind"] == "text"
    assert text_result.evidence["magic"] == "text"
    assert list_result.data == {"data": [1, 2]}
    assert list_result.evidence["kind"] == "json"


@pytest.mark.parametrize(
    ("content_type", "body", "magic"),
    [
        ("image/png", b"\x89PNG\r\n\x1a\n" + b"x" * 32, "png"),
        ("application/pdf", b"%PDF-1.7\n" + b"x" * 32, "pdf"),
    ],
)
def test_binary_body_has_hash_size_and_magic_without_replacement_text(
    content_type: str,
    body: bytes,
    magic: str,
) -> None:
    result = parse_http_body(body, {"Content-Type": content_type})

    assert result.data == {}
    assert result.evidence == {
        "kind": "binary",
        "content_type": content_type,
        "byte_length": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "magic": magic,
    }


def test_binary_signature_wins_over_a_misleading_text_content_type() -> None:
    body = b"%PDF-1.7\n" + b"printable document bytes"

    result = parse_http_body(body, {"Content-Type": "text/plain"})

    assert result.data == {}
    assert result.evidence["kind"] == "binary"
    assert result.evidence["magic"] == "pdf"


def test_svg_is_bounded_text_with_svg_magic() -> None:
    body = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"/>'

    result = parse_http_body(body, {"Content-Type": "image/svg+xml"})

    assert result.data == {"text": body.decode("utf-8")}
    assert result.evidence["kind"] == "text"
    assert result.evidence["magic"] == "svg"


def test_classic_runner_exposes_binary_evidence_to_existing_assertions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"\x89PNG\r\n\x1a\n" + b"render" * 32
    _serve(monkeypatch, _Response(body, "image/png"))
    scenario = f'''
API GET "/render.png"
ASSERT_STATUS 200
ASSERT_HEADERS Content-Type == "image/png"
ASSERT_JSON _body.kind == binary
ASSERT_JSON _body.magic == png
ASSERT_JSON _body.byte_length == {len(body)}
ASSERT_JSON _body.sha256 == "{hashlib.sha256(body).hexdigest()}"
'''

    result = OqlInterpreter(
        quiet=True, api_url="http://example.invalid"
    ).run(scenario, "binary-response.testql")

    assert result.ok, result.errors
    assert result.variables["_response"] == {}
    assert result.variables["_body"]["kind"] == "binary"


def test_unified_ir_uses_the_same_binary_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"%PDF-1.7\n" + b"document" * 32
    _serve(monkeypatch, _Response(body, "application/pdf"))
    step = ApiStep(
        method="GET",
        path="/render.pdf",
        asserts=[
            Assertion(field="status", op="==", expected=200),
            Assertion(field="body.kind", op="==", expected="binary"),
            Assertion(field="body.magic", op="==", expected="pdf"),
            Assertion(field="body.byte_length", op="==", expected=len(body)),
            Assertion(
                field="body.sha256",
                op="==",
                expected=hashlib.sha256(body).hexdigest(),
            ),
        ],
    )

    result = ir_api.execute(
        step, ExecutionContext(api_url="http://example.invalid")
    )

    assert result.status == StepStatus.PASSED, result.message
    assert result.details["payload"]["data"] == {}
    assert result.details["payload"]["headers"]["Content-Type"] == "application/pdf"
    assert result.details["payload"]["body"]["magic"] == "pdf"
