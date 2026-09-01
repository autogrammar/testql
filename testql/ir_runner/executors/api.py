"""Executor for `ApiStep` — HTTP request + assertion evaluation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from testql.base import StepResult, StepStatus
from testql.http_response import parse_http_body
from testql.ir import ApiStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, step_label


def _resolve_url(path: str, ctx: ExecutionContext) -> str:
    if path.startswith(("http://", "https://")):
        return path
    return f"{ctx.api_url}{path}"


def _do_request(
    method: str, url: str, body: dict | None, headers: dict
) -> tuple[int, dict, dict, dict]:
    req_body = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=req_body, method=method,
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response_headers = dict(resp.headers)
            parsed = parse_http_body(resp.read(), response_headers)
            return resp.status, parsed.data, response_headers, parsed.evidence
    except urllib.error.HTTPError as e:
        response_headers = dict(e.headers or {})
        parsed = parse_http_body(e.read() if e.fp else b"", response_headers)
        return e.code, parsed.data, response_headers, parsed.evidence


def _payload(status: int, data: object, headers: dict, body: dict) -> dict:
    return {"status": status, "data": data, "headers": headers, "body": body}


def execute(step: ApiStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "API")
    url = _resolve_url(interp_value(step.path, ctx.vars), ctx)
    body = interp_value(step.body, ctx.vars)
    headers = interp_value(step.headers, ctx.vars) or {}
    if ctx.dry_run:
        ctx.last_status, ctx.last_response = 200, {}
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "url": url})
    try:
        result = _do_request(step.method, url, body, headers)
        status, data = result[:2]
        response_headers = result[2] if len(result) > 2 else {}
        body_evidence = result[3] if len(result) > 3 else {}
    except Exception as e:
        return error_result(label, e)
    ctx.last_status, ctx.last_response = status, data
    ctx.vars.set("_body", body_evidence)
    return assemble_result(
        label,
        _payload(status, data, response_headers, body_evidence),
        step.asserts,
        ctx.dry_run,
    )


__all__ = ["execute"]
