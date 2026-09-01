"""API runner mixin — HTTP calls and response capture for OqlInterpreter."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

from testql.base import StepResult, StepStatus
from testql.http_response import parse_http_body

from ._parser import OqlLine

_OPTIONAL_TOKENS = frozenset({"optional", "true", "yes", "1"})


def _is_optional_flag(value: object) -> bool:
    """Return True for TestTOON/OQL optional markers (true/yes/1/optional)."""
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in _OPTIONAL_TOKENS


def _split_optional_api_args(args: str) -> tuple[str, bool]:
    """Strip a trailing ``optional`` token from API args without eating JSON bodies."""
    stripped = args.strip()
    if stripped.lower().endswith(" optional"):
        return stripped[: -len(" optional")].rstrip(), True
    return stripped, False


def _is_unreachable_error(exc: BaseException) -> bool:
    """True when the target never produced an HTTP status (down, TLS, DNS, timeout)."""
    if isinstance(exc, urllib.error.HTTPError):
        return False
    if isinstance(exc, (TimeoutError, ConnectionError, ssl.SSLError, OSError)):
        return True
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, urllib.error.HTTPError):
            return False
        return True
    text = str(exc).lower()
    needles = (
        "timed out",
        "timeout",
        "connection refused",
        "name or service not known",
        "temporary failure in name resolution",
        "ssl",
        "tlsv1",
        "certificate",
        "network is unreachable",
    )
    return any(needle in text for needle in needles)


class ApiRunnerMixin:
    """Mixin providing HTTP API execution commands: API, CAPTURE."""

    # These attributes are provided by the host OqlInterpreter
    api_url: str
    dry_run: bool
    last_response: dict[str, Any] | None
    last_status: int
    _skip_response_asserts: bool = False
    _skip_response_reason: str = ""

    # Retry configuration
    retry_max_attempts: int = 3
    retry_backoff_ms: int = 1000
    retry_status_codes: set[int] = {429, 500, 502, 503, 504}

    def _http_timeout_s(self) -> float:
        configured = getattr(self, "timeout_ms", None)
        if configured:
            return max(1.0, float(configured) / 1000.0)
        return 8.0

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _do_http_request(
        self, method: str, url: str, body_data: dict | None
    ) -> tuple[int, dict, dict, dict]:
        """Return status, compatibility payload, headers and body evidence."""
        req_body = json.dumps(body_data).encode("utf-8") if body_data else None
        req = urllib.request.Request(
            url, data=req_body, method=method,
            headers={"Content-Type": "application/json", "Accept": "*/*"},
        )
        with urllib.request.urlopen(req, timeout=self._http_timeout_s()) as resp:
            status = resp.status
            headers = dict(resp.headers)
            parsed = parse_http_body(resp.read(), headers)
            return status, parsed.data, headers, parsed.evidence

    def _do_http_request_with_retry(
        self, method: str, url: str, body_data: dict | None
    ) -> tuple[int, dict, dict, dict]:
        """Execute HTTP request with retry logic for transient failures."""
        last_exception = None

        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                result = self._do_http_request(method, url, body_data)
                status = result[0]

                # Check if status code warrants retry
                if status in self.retry_status_codes and attempt < self.retry_max_attempts:
                    backoff = self.retry_backoff_ms * attempt
                    self.out.warn(f"Retry {attempt}/{self.retry_max_attempts} for {status} (wait {backoff}ms)")
                    time.sleep(backoff / 1000)
                    continue

                return result

            except urllib.error.HTTPError as e:
                last_exception = e
                if e.code in self.retry_status_codes and attempt < self.retry_max_attempts:
                    backoff = self.retry_backoff_ms * attempt
                    self.out.warn(f"Retry {attempt}/{self.retry_max_attempts} for {e.code} (wait {backoff}ms)")
                    time.sleep(backoff / 1000)
                    continue
                raise
            except Exception as e:
                last_exception = e
                if _is_unreachable_error(e):
                    raise
                raise

        # All retries exhausted, raise last exception
        if last_exception:
            raise last_exception
        raise RuntimeError("Max retries exceeded")

    def _store_api_response(
        self,
        status: int,
        response: dict,
        headers: dict | None = None,
        body_evidence: dict | None = None,
    ) -> None:
        """Persist last API response into interpreter state and variables."""
        self.last_status = status
        self.last_response = response
        self.vars.set("_status", status)
        self.vars.set("_response", response)
        self.vars.set("_headers", headers or {})
        self.vars.set("_body", body_evidence or {})
        if isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, list):
                self.vars.set("_count", len(data))

    # ── Commands ─────────────────────────────────────────────────────────────

    def _record_api_success(
        self,
        label: str,
        status: int,
        response: dict,
        headers: dict | None = None,
        body_evidence: dict | None = None,
    ) -> None:
        """Store successful API response and append a PASSED step."""
        self._store_api_response(status, response, headers, body_evidence)
        icon = "✅" if status < 400 else "❌"
        self.out.step(icon, f"{label} → {status}")
        self.results.append(StepResult(
            name=label, status=StepStatus.PASSED, details={"status": status},
        ))

    def _record_api_http_error(self, label: str, e: urllib.error.HTTPError) -> None:
        self.last_status = e.code
        self.last_response = {}
        self.out.fail(f"{label} → {e.code}")
        self.results.append(StepResult(
            name=label, status=StepStatus.FAILED, message=f"HTTP {e.code}",
        ))

    def _record_api_error(self, label: str, e: Exception) -> None:
        self.last_status = 0
        self.last_response = {}
        self.out.fail(f"{label} → {e}")
        self.results.append(StepResult(
            name=label, status=StepStatus.ERROR, message=str(e),
        ))

    def _clear_response_assert_skip(self) -> None:
        self._skip_response_asserts = False
        self._skip_response_reason = ""

    def _record_unreachable(
        self,
        label: str,
        exc: BaseException,
        *,
        optional: bool,
    ) -> None:
        """Store status 0 for a down/TLS/DNS target. Optional rows skip instead of fail later."""
        reason = str(exc)
        payload = {"ok": False, "error": "unreachable", "reason": reason[:500]}
        self._store_api_response(0, payload)
        if optional:
            message = f"skipped: unreachable (optional): {reason[:180]}"
            self._skip_response_asserts = True
            self._skip_response_reason = message
            self.out.step("⏭️", f"{label} → unreachable (optional)")
            self.results.append(StepResult(
                name=label,
                status=StepStatus.SKIPPED,
                message=message,
                details={"status": 0, "body": payload},
            ))
            return
        self._clear_response_assert_skip()
        self.out.step("🔌", f"{label} → 0 unreachable")
        self.results.append(StepResult(
            name=label,
            status=StepStatus.PASSED,
            message=f"unreachable: {reason[:180]}",
            details={"status": 0, "body": payload},
        ))

    def _cmd_api(self, args: str, line: OqlLine) -> None:
        """API METHOD /path [json-body] [optional]"""
        args, optional = _split_optional_api_args(args)
        parts = args.strip().split(None, 2)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: API requires METHOD URL [body]")
            return

        method = parts[0].upper()
        url = self.vars.interpolate(parts[1].strip("\"'"))
        body_str = parts[2] if len(parts) > 2 else ""

        if url.startswith("/"):
            url = f"{self.api_url}{url}"

        body_data = None
        if body_str:
            body_str = self.vars.interpolate(body_str)
            try:
                body_data = json.loads(body_str)
            except json.JSONDecodeError:
                body_data = {"raw": body_str}

        label = f"API {method} {url}"
        self._clear_response_assert_skip()

        if self.dry_run:
            self.out.step("🌐", f"{label} (dry-run)")
            self.last_status = 200
            self.last_response = {"data": [], "_dry_run": True}
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return

        try:
            result = self._do_http_request_with_retry(method, url, body_data)
            status, response, headers = result[:3]
            body_evidence = result[3] if len(result) > 3 else {}
            self._record_api_success(
                label, status, response, headers, body_evidence
            )
        except urllib.error.HTTPError as e:
            error_body: dict[str, Any] = {}
            error_evidence: dict[str, Any] = {}
            error_headers = dict(e.headers or {})
            try:
                parsed = parse_http_body(e.read(), error_headers)
                error_body = parsed.data
                error_evidence = parsed.evidence
            except Exception:
                error_body = {}
            self._store_api_response(
                e.code, error_body, error_headers, error_evidence
            )
            icon = "✅" if e.code < 500 else "⚠️"
            self.out.step(icon, f"{label} → {e.code}")
            self.results.append(StepResult(
                name=label,
                status=StepStatus.PASSED,
                details={"status": e.code, "body": error_body},
            ))
        except Exception as e:
            if _is_unreachable_error(e):
                self._record_unreachable(label, e, optional=optional)
                return
            self._record_api_error(label, e)

    def _cmd_capture(self, args: str, line: OqlLine) -> None:
        """CAPTURE var_name FROM "json.path"

        Extracts a value from the last API response via dotted JSON path
        and stores it as a variable for use in subsequent commands.

        Example:
            API POST /api/devices {"name": "Test"}
            ASSERT_STATUS 201
            CAPTURE device_id FROM "data.id"
            API GET /api/devices/${device_id}
        """
        import re
        m = re.match(r'(\w+)\s+FROM\s+"([^"]+)"', args.strip(), re.IGNORECASE)
        if not m:
            self.out.warn(f'L{line.number}: CAPTURE syntax: CAPTURE var FROM "json.path"')
            return

        var_name, json_path = m.group(1), m.group(2)
        value = _navigate_json_path(self.last_response, json_path)

        if value is None:
            self.out.warn(f"L{line.number}: CAPTURE {var_name}: path '{json_path}' not found in last response")
            self.results.append(StepResult(
                name=f"CAPTURE {var_name}", status=StepStatus.WARNING,
                message=f"Path '{json_path}' returned None",
            ))
            return

        self.vars.set(var_name, value)
        self.out.step("🔗", f"CAPTURE {var_name} = {value!r}")
        self.results.append(StepResult(
            name=f"CAPTURE {var_name}",
            status=StepStatus.PASSED,
            details={var_name: value},
        ))


def _resolve_length(root: Any, path: str) -> int | None:
    """Return len() of the list at *path* (without the trailing .length)."""
    parent: Any = root
    for key in path.rsplit(".", 1)[0].split("."):
        parent = parent.get(key) if isinstance(parent, dict) else None
    return len(parent) if isinstance(parent, list) else None


def _navigate_step(obj: Any, key: str) -> Any:
    """Descend one level into a JSON object by key (or integer index)."""
    if isinstance(obj, dict):
        return obj.get(key)
    if isinstance(obj, list):
        try:
            return obj[int(key)]
        except (ValueError, IndexError):
            return None
    return None


def _navigate_json_path(root: Any, path: str) -> Any:
    """Navigate a JSON path supporting both bracket ['key'] and dot notation.
    
    Examples:
        ['transport']['http']['method']  - bracket notation
        transport.http.method            - dot notation  
        devices[0].id                    - mixed notation
        data.length                      - virtual length field
    """
    if root is None:
        return None
        
    if path.startswith('[') and path.endswith(']'):
        return _navigate_bracket_notation(root, path)
    else:
        return _navigate_dot_notation(root, path)

def _navigate_bracket_notation(root: Any, path: str) -> Any:
    """Navigate pure bracket notation: ['key1']['key2'][0]['key3']"""
    obj = root
    inner = path[1:-1]  # Remove outer [ and ]
    parts = inner.split('][')
    
    for part in parts:
        part = part.strip('"\'')  # Remove quotes
        obj = _navigate_step(obj, part)
        if obj is None:
            return None
    
    return obj

def _navigate_dot_notation(root: Any, path: str) -> Any:
    """Navigate dot notation and mixed notation."""
    obj = root
    
    for part in path.split("."):
        obj = _navigate_dot_part(obj, part)
        if obj is None:
            return None
    
    return obj

def _navigate_dot_part(obj: Any, part: str) -> Any:
    """Navigate a single part of a dot-notation path."""
    if part == "length":
        return _handle_length_virtual(obj)
    elif '[' in part and part.endswith(']'):
        return _handle_mixed_notation(obj, part)
    else:
        return _navigate_step(obj, part)

def _handle_length_virtual(obj: Any) -> Any:
    """Handle .length virtual field."""
    if isinstance(obj, (list, dict)):
        return len(obj)
    return None

def _handle_mixed_notation(obj: Any, part: str) -> Any:
    """Handle mixed notation: devices[0]"""
    key, index_part = part.split('[', 1)
    index = index_part[:-1]  # Remove trailing ]
    
    if key:
        obj = _navigate_step(obj, key)
    
    if index.isdigit():
        return _navigate_step(obj, index)
    else:
        return _navigate_step(obj, index.strip('"\''))
