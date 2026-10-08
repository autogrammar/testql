# Ticket 021: Normalize attribute selectors parsed as lists in TOON tables

- **ID**: ticket-021
- **Owner**: agent:antigravity
- **Status**: PLAN
- **Workflow state**: EDIT
- **Created**: 2026-10-02

## Goal and scope

Normalize CSS attribute selectors like `[data-action='foo']` when parsed into
single-element lists by the TOON table parser. Reconstruct proper CSS attribute
selector strings in `_testtoon_parser.py`, `_gui_expand.py`, and `_gui.py`.

## Acceptance criteria

- [ ] AC-01: Attribute selectors in FLOW/GUI tables expand to `[data-action='...']` rather than list representations.
- [ ] AC-02: `GUI_CLICK` and element finding in `_gui.py` normalize any lingering list repr selectors.
- [ ] AC-03: `tests/test_toon_attribute_selector.py` passes and governance checks pass.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: User requested sequential testing of all functionalities with testql, fixing the library directly if GUI testing fails, and merging the changes.

## Evidence boundary

Operational test receipts and browser execution logs remain local state.
