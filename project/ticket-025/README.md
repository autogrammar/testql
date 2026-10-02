# Ticket 025: Fallback selector resolution for GUI input and select

- **ID**: ticket-025
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-02

## Goal and scope

Resolve selectors with fallback strategies in `GUI_INPUT` and `GUI_SELECT` commands before executing fill/clear/select operations, and fail fast when the element is not found, avoiding 5000ms Playwright timeout stalls and uncaught exceptions.

## Acceptance criteria

- [x] AC-01: `GUI_INPUT` uses `_find_element_with_logging` to resolve selectors and fallback candidates before calling fill.
- [x] AC-02: `GUI_INPUT` returns clean failure without Playwright timeout when selector cannot be found.
- [x] AC-03: `GUI_SELECT` uses `_find_element_with_logging` for selector resolution.
- [x] AC-04: Unit test `tests/test_gui_input_fallback.py` passes.
- [x] AC-05: Governance checks pass.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: User requested sequential testing of all functionalities with testql, fixing the library directly if GUI testing fails, and merging the changes.

## Evidence boundary

Operational test receipts and browser execution logs remain local state.
