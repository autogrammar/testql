"""Tests for keyboard, mouse, and hardware scanner support in TestQL."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from testql.interpreter._testtoon_parser import testtoon_to_oql as parse_to_oql
from testql.interpreter.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine
from testql.base import StepStatus


def test_expand_keyboard_in_testtoon_to_oql():
    toon = """\
# SCENARIO: Keyboard Navigation Test
# TYPE: gui

KEYBOARD[2]{key, wait_ms}:
  ArrowDown, 100
  Enter, 200
"""
    script = parse_to_oql(toon, "test-keyboard.testql.toon.yaml")
    commands = [(line.command, line.args) for line in script.lines]

    assert commands == [
        ("GUI_PRESS", '"ArrowDown"'),
        ("WAIT", "100"),
        ("GUI_PRESS", '"Enter"'),
        ("WAIT", "200"),
    ]


def test_expand_scanner_in_testtoon_to_oql():
    toon = """\
# SCENARIO: Scanner Hardware Test
# TYPE: gui

SCANNER[2]{code, type, wait_ms}:
  BARCODE:1234567890, barcode, 150
  QR:admin@fleet.local, qr, 250
"""
    script = parse_to_oql(toon, "test-scanner.testql.toon.yaml")
    commands = [(line.command, line.args) for line in script.lines]

    assert commands == [
        ("SCANNER_SCAN", '"BARCODE:1234567890" barcode'),
        ("WAIT", "150"),
        ("SCANNER_SCAN", '"QR:admin@fleet.local" qr'),
        ("WAIT", "250"),
    ]


def test_expand_gui_press_and_hover():
    toon = """\
# SCENARIO: GUI Actions Test
# TYPE: gui

GUI[3]{action, selector, value, wait_ms}:
  press, -, ArrowDown, 50
  hover, button#submit, -, 100
  mouse, move, 200 300, 150
"""
    script = parse_to_oql(toon, "test-gui-actions.testql.toon.yaml")
    commands = [(line.command, line.args) for line in script.lines]

    assert ("GUI_PRESS", '"ArrowDown"') in commands
    assert ("GUI_HOVER", '"button#submit"') in commands
    assert ("GUI_MOUSE", "move 200 300") in commands


def test_gui_press_playwright_execution():
    interp = OqlInterpreter(dry_run=False)
    mock_page = MagicMock()
    interp._gui_page = mock_page

    line = OqlLine(number=1, command="GUI_PRESS", args='"ArrowDown"', raw='GUI_PRESS "ArrowDown"')
    interp._cmd_gui_press('"ArrowDown"', line)

    mock_page.keyboard.press.assert_called_once_with("ArrowDown")
    assert len(interp.results) == 1
    assert interp.results[0].status == StepStatus.PASSED


def test_gui_hover_playwright_execution():
    interp = OqlInterpreter(dry_run=False)
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_page.locator.return_value = mock_locator
    interp._gui_page = mock_page
    interp._gui_driver = "playwright"

    line = OqlLine(number=1, command="GUI_HOVER", args='"button#submit"', raw='GUI_HOVER "button#submit"')
    interp._cmd_gui_hover('"button#submit"', line)

    mock_locator.hover.assert_called_once()
    assert len(interp.results) == 1
    assert interp.results[0].status == StepStatus.PASSED


def test_gui_mouse_playwright_execution():
    interp = OqlInterpreter(dry_run=False)
    mock_page = MagicMock()
    mock_mouse = MagicMock()
    mock_page.mouse = mock_mouse
    interp._gui_page = mock_page

    line = OqlLine(number=1, command="GUI_MOUSE", args="move 100 250", raw="GUI_MOUSE move 100 250")
    interp._cmd_gui_mouse("move 100 250", line)

    mock_mouse.move.assert_called_once_with(100.0, 250.0)
    assert len(interp.results) == 1
    assert interp.results[0].status == StepStatus.PASSED


def test_scanner_scan_dual_mode():
    interp = OqlInterpreter(dry_run=False)
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {"dispatched": True, "sink_filled": True}
    interp._gui_page = mock_page

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success": true, "data": {"code": "BARCODE:123"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        line = OqlLine(number=1, command="SCANNER_SCAN", args='"BARCODE:123" barcode', raw='SCANNER_SCAN "BARCODE:123" barcode')
        interp._cmd_scanner_scan('"BARCODE:123" barcode', line)

        mock_page.evaluate.assert_called_once()
        mock_urlopen.assert_called_once()
        assert len(interp.results) == 1
        assert interp.results[0].status == StepStatus.PASSED
        assert interp.vars.get("_last_scan")["code"] == "BARCODE:123"


def test_scanner_scan_gui_only_fallback_on_http_error():
    interp = OqlInterpreter(dry_run=False)
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {"dispatched": True}
    interp._gui_page = mock_page

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        line = OqlLine(number=1, command="SCANNER_SCAN", args='"BARCODE:999"', raw='SCANNER_SCAN "BARCODE:999"')
        interp._cmd_scanner_scan('"BARCODE:999"', line)

        mock_page.evaluate.assert_called_once()
        assert len(interp.results) == 1
        assert interp.results[0].status == StepStatus.PASSED


def test_scanner_status_http_success():
    interp = OqlInterpreter(dry_run=False)

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status": "online", "scanner_present": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        line = OqlLine(number=1, command="SCANNER_STATUS", args="", raw="SCANNER_STATUS")
        interp._cmd_scanner_status("", line)

        assert len(interp.results) == 1
        assert interp.results[0].status == StepStatus.PASSED
        assert interp.vars.get("_scanner_status")["scanner_present"] is True
