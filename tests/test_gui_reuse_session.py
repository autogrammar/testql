"""Unit tests for reusing active GUI sessions across GUI_START invocations."""

from __future__ import annotations

import pytest

from testql.interpreter import OqlInterpreter


def test_start_playwright_reuses_active_page() -> None:
    """Test _start_playwright reuses an already active open page and navigates."""
    interp = OqlInterpreter(api_url="http://example.com:8100", dry_run=False, quiet=True)
    interp._gui_driver = "playwright"
    interp._gui_playwright_backend = "python"

    navigated_urls: list[str] = []

    class MockPage:
        url = "http://example.com:8100/initial"

        def is_closed(self) -> bool:
            return False

        def goto(self, url: str, **kwargs: object) -> None:
            navigated_urls.append(url)
            self.url = url

    class MockBrowser:
        closed = False

        def close(self) -> None:
            self.closed = True

    class MockPlaywright:
        stopped = False

        def stop(self) -> None:
            self.stopped = True

    mock_page = MockPage()
    mock_browser = MockBrowser()
    mock_playwright = MockPlaywright()

    interp._gui_page = mock_page
    interp._gui_app = (mock_playwright, mock_browser)

    # Calling _start_playwright should reuse existing session and navigate
    interp._start_playwright("/connect-test", "")

    assert navigated_urls == ["http://example.com:8100/connect-test"]
    assert interp.results[-1].status.value == "passed"
    assert mock_browser.closed is False
    assert mock_playwright.stopped is False


def test_start_playwright_recovers_if_page_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _start_playwright safely closes stale session if is_closed returns True."""
    interp = OqlInterpreter(api_url="http://example.com:8100", dry_run=False, quiet=True)
    interp._gui_driver = "playwright"
    interp._gui_playwright_backend = "python"

    class ClosedPage:
        url = "http://example.com:8100/dead"

        def is_closed(self) -> bool:
            return True

    class OldBrowser:
        closed = False

        def close(self) -> None:
            self.closed = True

    class OldPlaywright:
        stopped = False

        def stop(self) -> None:
            self.stopped = True

    old_browser = OldBrowser()
    old_playwright = OldPlaywright()
    interp._gui_page = ClosedPage()
    interp._gui_app = (old_playwright, old_browser)

    new_opened_urls: list[str] = []

    class NewPage:
        url = ""

        def set_default_timeout(self, t: int) -> None:
            pass

        def set_default_navigation_timeout(self, t: int) -> None:
            pass

        def goto(self, url: str, **kwargs: object) -> None:
            new_opened_urls.append(url)

    class NewBrowser:
        def new_page(self) -> NewPage:
            return NewPage()

    class NewChromium:
        def launch(self, **kwargs: object) -> NewBrowser:
            return NewBrowser()

    class NewPlaywright:
        chromium = NewChromium()

        def start(self) -> NewPlaywright:
            return self

    import playwright.sync_api
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", lambda: NewPlaywright())

    interp._start_playwright("/connect-test", "")

    assert old_browser.closed is True
    assert old_playwright.stopped is True
    assert new_opened_urls == ["http://example.com:8100/connect-test"]
    assert interp.results[-1].status.value == "passed"
