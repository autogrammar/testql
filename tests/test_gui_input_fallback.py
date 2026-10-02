"""Tests for GUI_INPUT and GUI_SELECT fallback selector resolution and fast-fail."""

from unittest.mock import MagicMock
import pytest
from testql.base import StepStatus
from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


@pytest.fixture
def interpreter():
    interp = OqlInterpreter()
    interp.out = MagicMock()
    return interp


def test_gui_input_dry_run(interpreter):
    interpreter.dry_run = True
    line = OqlLine(number=1, command="GUI_INPUT", args='"#missing-input" "test"', raw='GUI_INPUT "#missing-input" "test"')
    interpreter._cmd_gui_input(line.args, line)

    assert len(interpreter.results) == 1
    assert interpreter.results[-1].status == StepStatus.PASSED


def test_gui_input_not_found_fast_fail(interpreter):
    """When element is not found after fallbacks, GUI_INPUT fails gracefully without timing out."""
    interpreter.dry_run = False
    mock_page = MagicMock()
    # is_visible returns False for all fallback probes
    mock_page.is_visible.return_value = False
    interpreter._gui_page = mock_page
    interpreter._gui_driver = "playwright"

    line = OqlLine(number=1, command="GUI_INPUT", args='"#non-existent-input" "hello"', raw='GUI_INPUT "#non-existent-input" "hello"')
    interpreter._cmd_gui_input(line.args, line)

    assert len(interpreter.results) == 1
    assert interpreter.results[-1].status == StepStatus.FAILED
    assert "Element not found" in interpreter.results[-1].message
    # fill should not have been called
    mock_page.fill.assert_not_called()


def test_gui_input_fallback_found(interpreter):
    """When original selector fails but fallback succeeds, GUI_INPUT fills resolved element."""
    interpreter.dry_run = False
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_page.locator.return_value = mock_locator

    # selector is '#add-name' -> fallback '.add-name' is visible
    def is_visible_mock(selector, timeout=None):
        return selector == ".add-name"

    mock_page.is_visible.side_effect = is_visible_mock
    interpreter._gui_page = mock_page
    interpreter._gui_driver = "playwright"

    line = OqlLine(number=1, command="GUI_INPUT", args='"#add-name" "test user"', raw='GUI_INPUT "#add-name" "test user"')
    interpreter._cmd_gui_input(line.args, line)

    assert len(interpreter.results) == 1
    assert interpreter.results[-1].status == StepStatus.PASSED
    mock_page.locator.assert_called_with(".add-name")
    mock_locator.fill.assert_called_once_with("test user", timeout=30000)


def test_gui_select_not_found_fast_fail(interpreter):
    """When select element is not found after fallbacks, GUI_SELECT fails gracefully."""
    interpreter.dry_run = False
    mock_page = MagicMock()
    mock_page.is_visible.return_value = False
    interpreter._gui_page = mock_page
    interpreter._gui_driver = "playwright"

    line = OqlLine(number=1, command="GUI_SELECT", args='"#missing-select" "val1"', raw='GUI_SELECT "#missing-select" "val1"')
    interpreter._cmd_gui_select(line.args, line)

    assert len(interpreter.results) == 1
    assert interpreter.results[-1].status == StepStatus.FAILED
    assert "Element not found" in interpreter.results[-1].message
    mock_page.select_option.assert_not_called()
