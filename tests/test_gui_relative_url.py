"""Unit tests for relative URL handling and optional input values in GUI mixin."""

from __future__ import annotations

import pytest

from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


def test_gui_start_relative_url_dry_run() -> None:
    """Test GUI_START accepts relative routes in dry-run mode."""
    interp = OqlInterpreter(
        api_url="http://localhost:8100",
        variables={"base_url": "http://localhost:8100"},
        dry_run=True,
        quiet=True,
    )
    line = OqlLine(number=1, command="GUI_START", args='"/connect-id"', raw='GUI_START "/connect-id"')
    interp._cmd_gui_start(line.args, line)

    assert interp.results[-1].status.value == "passed"


def test_gui_input_selector_only_dry_run() -> None:
    """Test GUI_INPUT accepts selector without text argument (defaults to empty string)."""
    interp = OqlInterpreter(api_url="http://localhost:8100", dry_run=True, quiet=True)
    line = OqlLine(number=1, command="GUI_INPUT", args='"#add-name"', raw='INPUT "#add-name"')
    interp._cmd_gui_input(line.args, line)

    assert interp.results[-1].status.value == "passed"


def test_gui_input_dash_placeholder_dry_run() -> None:
    """Test GUI_INPUT treats '-' placeholder as empty string."""
    interp = OqlInterpreter(api_url="http://localhost:8100", dry_run=True, quiet=True)
    line = OqlLine(number=1, command="GUI_INPUT", args='"#add-name" -', raw='INPUT "#add-name" -')
    interp._cmd_gui_input(line.args, line)

    assert interp.results[-1].status.value == "passed"


def test_start_playwright_relative_path_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _start_playwright resolves relative paths against base_url."""
    interp = OqlInterpreter(api_url="http://example.com:8100", dry_run=False, quiet=True)
    interp._gui_driver = "playwright"
    interp._gui_playwright_backend = "python"

    opened_urls: list[str] = []

    class MockPage:
        url = ""

        def set_default_timeout(self, t: int) -> None:
            pass

        def set_default_navigation_timeout(self, t: int) -> None:
            pass

        def goto(self, url: str, **kwargs: object) -> None:
            opened_urls.append(url)

    class MockBrowser:
        def new_page(self) -> MockPage:
            return MockPage()

    class MockChromium:
        def launch(self, **kwargs: object) -> MockBrowser:
            return MockBrowser()

    class MockPlaywright:
        chromium = MockChromium()

        def start(self) -> MockPlaywright:
            return self

    import playwright.sync_api
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", lambda: MockPlaywright())

    interp._start_playwright("/connect-id", "")
    assert opened_urls == ["http://example.com:8100/connect-id"]
