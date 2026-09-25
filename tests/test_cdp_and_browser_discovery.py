"""Tests for CDP support, browser discovery, and encoder fallback in TestQL."""

from __future__ import annotations

import json
from pathlib import Path
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from testql.interpreter import _node_playwright as node_playwright
from testql.interpreter._testtoon_parser import parse_testtoon, testtoon_to_oql as parse_to_oql
from testql.adapters.testtoon_adapter import parse as parse_testtoon_ir
from testql.ir import GuiStep
from testql.interpreter.interpreter import OqlInterpreter
from testql.interpreter._encoder import EncoderMixin
from testql.interpreter._parser import OqlLine
from testql.base import StepStatus


def test_find_playwright_browsers_dir(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    sub = root / "subdir" / "nested"
    sub.mkdir(parents=True)
    browsers_dir = root / ".playwright-browsers"
    browsers_dir.mkdir()

    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    monkeypatch.setenv("PWD", str(sub))

    found = node_playwright.find_playwright_browsers_dir(sub)
    assert found == browsers_dir


def test_find_browser_executable_in_playwright_browsers(tmp_path, monkeypatch):
    root = tmp_path / "app"
    browsers_dir = root / ".playwright-browsers"
    chrome_dir = browsers_dir / "chromium-1155" / "chrome-linux"
    chrome_dir.mkdir(parents=True)
    chrome_exe = chrome_dir / "chrome"
    chrome_exe.write_text("#!/bin/sh\n", encoding="utf-8")
    chrome_exe.chmod(0o755)

    for env_name in node_playwright._BROWSER_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browsers_dir))

    found = node_playwright.find_browser_executable()
    assert found == str(chrome_exe)


def test_expand_cdp_in_testtoon_to_oql():
    toon = """\
# SCENARIO: CDP Test
# TYPE: gui

CDP[2]{method, params, target}:
  Page.enable, -, -
  Runtime.evaluate, {"expression": "1 + 1", "returnByValue": true}, eval_result
"""
    oql = parse_to_oql(toon)
    raw_lines = [l.raw for l in oql.lines]
    assert any("GUI_CDP" in r and "Page.enable" in r for r in raw_lines)
    assert any("GUI_CDP" in r and "Runtime.evaluate" in r and "eval_result" in r for r in raw_lines)


def test_parse_cdp_in_testtoon_adapter():
    toon = """\
# SCENARIO: CDP Adapter Test
# TYPE: gui

CDP[2]{method, params}:
  DOM.getDocument, {"depth": 1}
  Page.captureScreenshot, {"format": "png"}
"""
    plan = parse_testtoon_ir(toon)
    cdp_steps = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "cdp"]
    assert len(cdp_steps) == 2
    assert cdp_steps[0].selector == "DOM.getDocument"
    assert json.loads(cdp_steps[0].value) == {"depth": 1}
    assert cdp_steps[1].selector == "Page.captureScreenshot"


def test_cmd_gui_cdp_execution():
    interp = OqlInterpreter(api_url="http://localhost:8100", quiet=True, dry_run=False)
    mock_session = MagicMock()
    mock_session.send.return_value = {"result": {"value": 42}}

    mock_context = MagicMock()
    mock_context.new_cdp_session.return_value = mock_session

    mock_page = MagicMock()
    mock_page.context = mock_context
    interp._gui_page = mock_page

    args = 'Runtime.evaluate {"expression": "40 + 2", "returnByValue": true} -> cdp_res'
    line = OqlLine(1, "GUI_CDP", args, f"GUI_CDP {args}")

    # Execute CDP command
    interp._cmd_gui_cdp(args, line)

    mock_context.new_cdp_session.assert_called_once_with(mock_page)
    mock_session.send.assert_called_once_with(
        "Runtime.evaluate", {"expression": "40 + 2", "returnByValue": True}
    )
    assert interp.vars.get("cdp_res") == {"result": {"value": 42}}
    assert interp.results[-1].status == StepStatus.PASSED


def test_encoder_to_js_translation():
    js_nav = EncoderMixin._encoder_to_js("/encoder/page-next")
    assert "remoteScroll(1)" in js_nav

    js_prev = EncoderMixin._encoder_to_js("/encoder/page-prev")
    assert "remoteScroll(-1)" in js_prev

    js_click = EncoderMixin._encoder_to_js("/encoder/click")
    assert "remoteClick()" in js_click

    js_status = EncoderMixin._encoder_to_js("/encoder/status")
    assert "getStatus()" in js_status


def test_encoder_fallback_to_gui_page():
    interp = OqlInterpreter(api_url="http://localhost:8100", quiet=True, dry_run=False)
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {"ok": True, "active": 2}
    interp._gui_page = mock_page

    # Calling _cmd_encoder_page_next when http fails should fall back to mock_page.evaluate
    with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
        line = OqlLine(1, "ENCODER_PAGE_NEXT", "", "ENCODER_PAGE_NEXT")
        interp._cmd_encoder_page_next("", line)

        assert mock_page.evaluate.called
        assert interp.vars.get("_encoder_status") == {"ok": True, "active": 2}
        assert interp.results[-1].status == StepStatus.PASSED


def test_encoder_fallback_on_http_404():
    interp = OqlInterpreter(api_url="http://localhost:8100", quiet=True, dry_run=False)
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {"ok": True, "active": 1}
    interp._gui_page = mock_page

    err = urllib.error.HTTPError("http://localhost:8105/encoder/activate", 404, "Not Found", {}, None)
    with patch("urllib.request.urlopen", side_effect=err):
        line = OqlLine(1, "ENCODER_ON", "", "ENCODER_ON")
        interp._cmd_encoder_on("", line)

        assert mock_page.evaluate.called
        assert interp.vars.get("_encoder_status") == {"ok": True, "active": 1}
        assert interp.results[-1].status == StepStatus.PASSED


def test_cmd_gui_cdp_nested_quotes_unwrapping():
    interp = OqlInterpreter(api_url="http://localhost:8100", quiet=True, dry_run=False)
    mock_session = MagicMock()
    mock_session.send.return_value = {"result": {"value": 100}}

    mock_context = MagicMock()
    mock_context.new_cdp_session.return_value = mock_session

    mock_page = MagicMock()
    mock_page.context = mock_context
    interp._gui_page = mock_page

    # Double-wrapped nested quotes around JSON params
    args = '\'Runtime.evaluate\' \'\'{"expression": "50 * 2"}\'\' -> cdp_res'
    line = OqlLine(1, "GUI_CDP", args, f"GUI_CDP {args}")

    interp._cmd_gui_cdp(args, line)

    mock_session.send.assert_called_once_with(
        "Runtime.evaluate", {"expression": "50 * 2"}
    )
    assert interp.vars.get("cdp_res") == {"result": {"value": 100}}
    assert interp.results[-1].status == StepStatus.PASSED

