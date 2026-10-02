"""Tests for normalizing attribute selectors in TOON flow and GUI tables."""

from __future__ import annotations

from testql.interpreter._gui_expand import gui_row_fields
from testql.interpreter._testtoon_parser import _expand_flow
from testql.interpreter.testtoon_parser import ToonSection


def test_expand_flow_reconstructs_attribute_selector() -> None:
    """When TOON parses [data-action='search-devices'] as a 1-item list, reconstruct selector string."""
    section = ToonSection(
        type="FLOW",
        columns=["command", "target", "meta"],
        rows=[{"command": "click", "target": ["data-action='search-devices'"], "meta": None}],
    )
    lines: list = []
    _expand_flow(section, lines, 1)

    assert len(lines) == 1
    assert lines[0].command == "CLICK"
    assert lines[0].args == '"[data-action=\'search-devices\']"'
    assert lines[0].raw == 'CLICK "[data-action=\'search-devices\']"'


def test_expand_flow_cleans_dash_meta() -> None:
    """When meta is '-' or None, do not append trailing dash to args."""
    section = ToonSection(
        type="FLOW",
        columns=["command", "target", "meta"],
        rows=[{"command": "click", "target": "#btn-test", "meta": "-"}],
    )
    lines: list = []
    _expand_flow(section, lines, 1)

    assert len(lines) == 1
    assert lines[0].args == '"#btn-test"'
    assert lines[0].raw == 'CLICK "#btn-test"'


def test_gui_row_fields_normalizes_list_selector() -> None:
    """gui_row_fields converts list-wrapped selector to CSS attribute selector."""
    action, selector, value, wait_ms = gui_row_fields({
        "action": "click",
        "selector": ["data-testid='save'"],
    })
    assert selector == "[data-testid='save']"
