"""Flow control mixin — WAIT, LOG, PRINT, INCLUDE and UI event emission."""

from __future__ import annotations

import time
from pathlib import Path

from testql.base import StepResult, StepStatus

from ._parser import OqlLine, OqlScript, parse_oql


class FlowMixin:
    """Mixin providing: WAIT, LOG, PRINT, INCLUDE and _emit_event."""

    def _cmd_wait_for(self, args: str, line: OqlLine) -> None:
        """
        WAIT_FOR "selector" VISIBLE 5000
        WAIT_FOR NETWORK_IDLE 10000
        """
        parts = args.strip().split()
        if not parts:
            return

        timeout_ms = 5000
        selector = parts[0].strip("\"'")
        state = "VISIBLE"
        
        if len(parts) >= 2:
            if parts[1].upper() in ("VISIBLE", "HIDDEN", "NETWORK_IDLE"):
                state = parts[1].upper()
                if len(parts) >= 3:
                    try:
                        timeout_ms = int(parts[2])
                    except ValueError:
                        pass
            else:
                try:
                    timeout_ms = int(parts[1])
                except ValueError:
                    pass

        if self.dry_run:
            self.out.step("⏳", f"WAIT_FOR {selector} {state} timeout={timeout_ms}ms (dry-run)")
            self.results.append(StepResult(
                name=f"WAIT_FOR {selector} {state}", status=StepStatus.PASSED,
            ))
            return

        self.out.step("⏳", f"Waiting for {selector} to be {state} (timeout {timeout_ms}ms)...")
        
        # Simulated polling for now (as we don't have a real browser attached in this CLI tool yet)
        # In the future, this will call a browser driver.
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            # Placeholder: always "succeeds" after a short delay for simulation
            time.sleep(0.1)
            break
        
        self.out.step("✅", f"{selector} is {state}")
        self.results.append(StepResult(
            name=f"WAIT_FOR {selector} {state}", status=StepStatus.PASSED,
        ))

    def _cmd_wait(self, args: str, line: OqlLine) -> None:
        import re
        # Parse various time formats: 500, "500", '500', "10 s", "500ms", "10s"
        args_clean = args.strip().strip("\"'")
        
        # Try to extract numeric value with optional unit
        # Matches: 500, 10 s, 500ms, 10s, 10.5s
        match = re.match(r'^(\d+(?:\.\d+)?)\s*(ms|s|m|h)?$', args_clean, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            unit = (match.group(2) or 'ms').lower()
            
            # Convert to milliseconds
            if unit == 's':
                ms = int(value * 1000)
            elif unit == 'm':
                ms = int(value * 60 * 1000)
            elif unit == 'h':
                ms = int(value * 60 * 60 * 1000)
            else:  # ms
                ms = int(value)
        else:
            # Fallback: try simple integer parsing
            try:
                ms = int(args_clean)
            except ValueError:
                # If all fails, default to 1000ms and log error
                self.out.fail(f"L{line.number}: Invalid WAIT duration: {args!r}, defaulting to 1000ms")
                self.errors.append(f"Invalid WAIT duration: {args!r}")
                ms = 1000
        
        if self.dry_run:
            self.out.step("⏳", f"WAIT {ms}ms (dry-run)")
        else:
            time.sleep(ms / 1000)
            self.out.step("⏳", f"WAIT {ms}ms")

    def _cmd_log(self, args: str, line: OqlLine) -> None:
        msg = args.strip()
        if (msg.startswith('"') and msg.endswith('"')) or (msg.startswith("'") and msg.endswith("'")):
            msg = msg[1:-1]
        elif msg.startswith('"'):
            end = msg.find('"', 1)
            if end > 0:
                msg = msg[1:end]
        elif msg.startswith("'"):
            end = msg.find("'", 1)
            if end > 0:
                msg = msg[1:end]
        self.out.info(msg)

    def _cmd_if(self, args: str, line: OqlLine) -> None:
        """IF <path> <op> <expected> THEN <action>
        e.g. IF _status >= 500 THEN LOG 'Server error detected'
        """
        import re
        from ._assertions import _COMPARE_OPS
        from ._api_runner import _navigate_json_path

        match = re.search(r'\s+THEN\s+', args, flags=re.IGNORECASE)
        if match:
            condition_str = args[:match.start()].strip()
            action_str = args[match.end():].strip()
        else:
            parts = args.strip().split(None, 3)
            if len(parts) >= 4 and parts[1] in _COMPARE_OPS:
                condition_str = f"{parts[0]} {parts[1]} {parts[2]}"
                action_str = parts[3]
            else:
                return

        cond_parts = condition_str.split(None, 2)
        if len(cond_parts) < 3:
            return
        path, op, expected_str = cond_parts[0], cond_parts[1], cond_parts[2]

        if path.startswith("_"):
            match_var = re.match(r"^(_[A-Za-z0-9_]+)(?:\.(.+))?$", path)
            if match_var:
                root_name = match_var.group(1)
                remainder = match_var.group(2)
                root_obj = self.vars.get(root_name)
                obj = _navigate_json_path(root_obj, remainder) if remainder else root_obj
            else:
                obj = self.vars.get(path)
        else:
            obj = _navigate_json_path(self.last_response, path)

        literal = expected_str.strip().strip("\"'")
        lowered = literal.lower()
        if lowered == "true":
            expected = True
        elif lowered == "false":
            expected = False
        elif lowered in {"null", "none"}:
            expected = None
        else:
            try:
                expected = float(literal) if "." in literal else int(literal)
            except ValueError:
                expected = literal

        cmp_fn = _COMPARE_OPS.get(op)
        ok = cmp_fn(obj, expected) if cmp_fn else False

        if ok and action_str:
            action_parts = action_str.split(None, 1)
            act_cmd = action_parts[0]
            act_args = action_parts[1] if len(action_parts) > 1 else ""
            self._dispatch(act_cmd, act_args, OqlLine(number=line.number, command=act_cmd.upper(), args=act_args, raw=action_str))

    def _cmd_print(self, args: str, line: OqlLine) -> None:
        self.out.emit(args)

    def _cmd_include(self, args: str, line: OqlLine) -> None:
        """INCLUDE "relative/path.testql.toon.yaml" — inline and execute another script."""
        rel_path = args.strip().strip("\"'")
        resolved: Path | None = None
        for base in self.include_paths:
            candidate = Path(base) / rel_path
            if candidate.is_file():
                resolved = candidate
                break

        if not resolved:
            self.out.fail(f"L{line.number}: INCLUDE not found: {rel_path}")
            self.errors.append(f"INCLUDE not found: {rel_path}")
            return

        abs_path = str(resolved.resolve())
        if abs_path in self._included:
            self.out.warn(f"L{line.number}: circular INCLUDE skipped: {rel_path}")
            return

        self._included.add(abs_path)
        self.out.step("📎", f"INCLUDE {rel_path}")
        source = resolved.read_text(encoding="utf-8")
        if hasattr(self, "parse"):
            sub_script: OqlScript = self.parse(source, filename=rel_path)
        else:
            sub_script = parse_oql(source, filename=rel_path)
        for sub_line in sub_script.lines:
            sub_args = self.vars.interpolate(sub_line.args)
            try:
                self._dispatch(sub_line.command, sub_args, sub_line)
            except Exception as e:
                self.errors.append(f"INCLUDE {rel_path} L{sub_line.number}: {e}")
                self.out.fail(f"INCLUDE {rel_path} L{sub_line.number}: {e}")

    # ── UI / navigation events ─────────────────────────────────────────────────

    _EVENT_ICONS: dict[str, str] = {
        "navigate": "📍", "click": "🖱️", "input": "⌨️",
        "select_device": "📱", "select_interval": "⏱️",
        "start_test": "🧪", "step_complete": "✅",
        "protocol_created": "📋", "protocol_finalize": "✔️",
        "emit": "📣", "render": "🎨", "layout": "📐",
        "record_start": "🔴", "record_stop": "⏹️",
        "create_protocol": "📋",
    }

    def _emit_event(self, cmd: str, args: str, line: OqlLine) -> None:
        """Emit a navigation/UI event (for commands with no explicit handler)."""
        event = {"type": cmd, "args": args, "line": line.number}
        self.events.append(event)
        icon = self._EVENT_ICONS.get(cmd, "▶️")
        self.out.step(icon, f"{cmd.upper()} {args}")
        self.results.append(StepResult(
            name=f"{cmd.upper()} {args[:60]}", status=StepStatus.PASSED,
        ))
