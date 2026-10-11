# Ticket 024: Reuse active GUI session on subsequent GUI_START

- **ID**: ticket-024
- **Owner**: agent:antigravity
- **Status**: PLAN
- **Workflow state**: EDIT
- **Created**: 2026-10-02

## Goal and scope

Allow `GUI_START` to safely reuse an existing active browser session (or navigate to new `app_path`)
when called multiple times (such as across `INCLUDE` child scenarios), avoiding Playwright sync loop
concurrency errors.

## Acceptance criteria

- [x] AC-01: `GUI_START` reuses open browser session and navigates if page is open.
- [x] AC-02: Unit test `tests/test_gui_reuse_session.py` passes.
- [x] AC-03: Governance checks pass.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: User requested sequential testing of all functionalities with testql, fixing the library directly if GUI testing fails, and merging the changes.

## Evidence boundary

Operational test receipts and browser execution logs remain local state.
