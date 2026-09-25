"""Hardware Scanner (QR / Barcode / RFID) commands mixin for OqlInterpreter."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class ScannerMixin:
    """Mixin providing SCANNER_SCAN and SCANNER_STATUS commands."""

    def _scanner_url(self) -> str:
        return (
            self.vars.get("scanner_url")
            or self.vars.get("base_url")
            or getattr(self, "api_url", "http://localhost:8100")
        )

    def _scanner_ingest_path(self) -> str:
        return self.vars.get("scanner_ingest_path", "/api/v3/identification/scanner/ingest")

    def _scanner_status_path(self) -> str:
        return self.vars.get("scanner_status_path", "/api/v3/identification/scanner/status")

    def _cmd_scanner_scan(self, args: str, line: OqlLine) -> None:
        """SCANNER_SCAN "code" [type] — Simulate scanner hardware event.

        Dual-mode execution:
        1. If active GUI page is open, dispatches in-page wedge CustomEvent
           ("barcodeScanned") and populates any active scanner input sink.
        2. Sends HTTP POST to scanner ingest API endpoint.
        """
        parts = args.strip().split(maxsplit=1)
        if not parts:
            self.out.fail(f"L{line.number}: SCANNER_SCAN requires code")
            self.results.append(StepResult(
                name="SCANNER_SCAN",
                status=StepStatus.FAILED,
                message="SCANNER_SCAN requires code",
            ))
            return

        raw_code = parts[0].strip()
        while len(raw_code) >= 2 and ((raw_code[0] == '"' and raw_code[-1] == '"') or (raw_code[0] == "'" and raw_code[-1] == "'")):
            raw_code = raw_code[1:-1].strip()

        code_type = parts[1].strip().lower() if len(parts) > 1 else "barcode"
        while len(code_type) >= 2 and ((code_type[0] == '"' and code_type[-1] == '"') or (code_type[0] == "'" and code_type[-1] == "'")):
            code_type = code_type[1:-1].strip()

        label = f'SCANNER_SCAN "{raw_code}" ({code_type})'

        if self.dry_run:
            self.out.step("📱", f"{label} (dry-run)")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return

        gui_success = False
        gui_details = None
        gui_page = getattr(self, "_gui_page", None)

        if gui_page:
            try:
                # Dispatch in-page event and attempt to fill scanner sink
                js_script = f"""
                (() => {{
                    const code = {json.dumps(raw_code)};
                    const type = {json.dumps(code_type)};
                    let sinkFound = false;

                    // 1. Dispatch custom events
                    window.dispatchEvent(new CustomEvent('barcodeScanned', {{
                        detail: {{ code: code, type: type, source: 'wedge' }}
                    }}));
                    window.dispatchEvent(new CustomEvent('io:scan', {{
                        detail: {{ code: code, type: type, source: 'wedge' }}
                    }}));

                    // 2. Check for scanner sink input
                    const sink = document.querySelector('#global-scanner-sink, [data-testid="scanner-sink"], input[placeholder*="scan" i], input[type="text"]');
                    if (sink) {{
                        sink.value = code;
                        sink.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        sink.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        sink.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', bubbles: true }}));
                        sinkFound = true;
                    }}
                    return {{ dispatched: true, code: code, type: type, sink_filled: sinkFound }};
                }})()
                """
                gui_details = gui_page.evaluate(js_script)
                gui_success = True
            except Exception as e:
                gui_details = {"gui_error": str(e)}

        # Also attempt HTTP API ingest
        http_success = False
        http_details = None
        url = f"{self._scanner_url().rstrip('/')}{self._scanner_ingest_path()}"
        body = {"code": raw_code, "type": code_type}
        try:
            req_body = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                text = resp.read().decode("utf-8")
                try:
                    http_details = json.loads(text)
                except Exception:
                    http_details = {"text": text[:200]}
                http_success = True
                self.vars.set("_scanner_status", http_details)
        except Exception as e:
            http_details = {"http_error": str(e)}

        combined_details = {
            "code": raw_code,
            "type": code_type,
            "gui": gui_details,
            "http": http_details,
        }
        self.vars.set("_last_scan", combined_details)

        if gui_success or http_success:
            source_tag = "GUI+API" if (gui_success and http_success) else ("GUI" if gui_success else "API")
            self.out.step("📱", f"{label} ({source_tag}) => PASSED")
            self.results.append(StepResult(
                name=label,
                status=StepStatus.PASSED,
                details=combined_details,
            ))
        else:
            err_msg = f"Scanner dispatch failed: GUI ({gui_details}), HTTP ({http_details})"
            self.out.fail(f"{label} => {err_msg}")
            self.results.append(StepResult(
                name=label,
                status=StepStatus.FAILED,
                message=err_msg,
                details=combined_details,
            ))

    def _cmd_scanner_status(self, args: str, line: OqlLine) -> None:
        """SCANNER_STATUS — Check scanner hardware status."""
        label = "SCANNER_STATUS"
        if self.dry_run:
            self.out.step("📱", f"{label} (dry-run)")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return

        url = f"{self._scanner_url().rstrip('/')}{self._scanner_status_path()}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                text = resp.read().decode("utf-8")
                try:
                    data = json.loads(text)
                except Exception:
                    data = {"text": text[:200]}
                self.vars.set("_scanner_status", data)
                self.out.step("📱", f"{label} => {json.dumps(data)[:120]}")
                self.results.append(StepResult(name=label, status=StepStatus.PASSED, details=data))
        except Exception as e:
            gui_page = getattr(self, "_gui_page", None)
            if gui_page:
                try:
                    res = gui_page.evaluate("() => window.__SCANNER_STATUS__ || { status: 'active_gui' }")
                    self.vars.set("_scanner_status", res)
                    self.out.step("📱", f"{label} (GUI) => {json.dumps(res)[:120]}")
                    self.results.append(StepResult(name=label, status=StepStatus.PASSED, details=res))
                    return
                except Exception:
                    pass
            self.out.fail(f"{label} => {e}")
            self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=str(e)))
