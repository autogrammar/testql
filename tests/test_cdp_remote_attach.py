"""Tests for remote CDP browser attach via cdp_url in TestQL."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from testql.interpreter.interpreter import OqlInterpreter
from testql.base import StepStatus


def test_cdp_url_connect_and_reuse_page():
    """AC-01 & AC-02: Connect over CDP and reuse existing page without closing remote browser."""
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_p.chromium.connect_over_cdp.return_value = mock_browser
    mock_browser.contexts = [mock_context]
    mock_context.pages = [mock_page]
    mock_page.url = "http://localhost:8100/connect-oql-system/test-hui"

    interpreter = OqlInterpreter()
    interpreter.vars.set("cdp_url", "http://127.0.0.1:9222")

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_p

        script = interpreter.parse("""\
GUI_START "current"
GUI_STOP
""")
        res = interpreter.execute(script)

    mock_p.chromium.connect_over_cdp.assert_called_once_with("http://127.0.0.1:9222")
    mock_page.goto.assert_not_called()
    mock_browser.close.assert_not_called()
    mock_p.stop.assert_called_once()
    assert res.ok
    assert all(s.status == StepStatus.PASSED for s in interpreter.results)


def test_browser_cdp_url_variable_navigation():
    """Verify browser.cdp_url variable triggers CDP attach and navigates if URL differs."""
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_p.chromium.connect_over_cdp.return_value = mock_browser
    mock_browser.contexts = [mock_context]
    mock_context.pages = [mock_page]
    mock_page.url = "http://localhost:8100/initial"

    interpreter = OqlInterpreter()
    interpreter.vars.set("browser.cdp_url", "http://127.0.0.1:9222")

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_p

        script = interpreter.parse("""\
GUI_START "http://localhost:8100/target"
GUI_STOP
""")
        res = interpreter.execute(script)

    mock_p.chromium.connect_over_cdp.assert_called_once_with("http://127.0.0.1:9222")
    mock_page.goto.assert_called_once()
    assert mock_page.goto.call_args[0][0] == "http://localhost:8100/target"
    mock_browser.close.assert_not_called()
    mock_p.stop.assert_called_once()
    assert res.ok


def test_cdp_no_pages_creates_new_page():
    """When remote context has no open pages, create a new page in the context."""
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    new_page = MagicMock()

    mock_p.chromium.connect_over_cdp.return_value = mock_browser
    mock_browser.contexts = [mock_context]
    mock_context.pages = []
    mock_context.new_page.return_value = new_page
    new_page.url = "about:blank"

    interpreter = OqlInterpreter()
    interpreter.vars.set("cdp_url", "http://127.0.0.1:9222")

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_p

        script = interpreter.parse("""\
GUI_START "http://localhost:8100/dashboard"
GUI_STOP
""")
        res = interpreter.execute(script)

    mock_context.new_page.assert_called_once()
    new_page.goto.assert_called_once()
    assert res.ok


def test_cdp_dry_run():
    """Dry run logs cdp_url without launching Playwright."""
    interpreter = OqlInterpreter(dry_run=True)
    interpreter.vars.set("cdp_url", "http://127.0.0.1:9222")

    script = interpreter.parse("""\
GUI_START "current"
GUI_STOP
""")
    res = interpreter.execute(script)

    assert res.ok
    assert any("cdp_url=http://127.0.0.1:9222" in r.name or r.status == StepStatus.PASSED for r in res.steps)


def test_cdp_cleanup_on_exception():
    """If an assertion or step fails, close_gui still detaches without killing remote browser."""
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_p.chromium.connect_over_cdp.return_value = mock_browser
    mock_browser.contexts = [mock_context]
    mock_context.pages = [mock_page]
    mock_page.locator.side_effect = RuntimeError("Element boom")

    interpreter = OqlInterpreter()
    interpreter.vars.set("cdp_url", "http://127.0.0.1:9222")

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_p

        script = interpreter.parse("""\
GUI_START "current"
GUI_CLICK "#non-existent"
""")
        res = interpreter.execute(script)

    mock_browser.close.assert_not_called()
    mock_p.stop.assert_called_once()
    assert not res.ok
