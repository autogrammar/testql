# Ticket 020: Resolve relative URLs and optional input values in GUI scenarios

- **ID**: ticket-020
- **Owner**: agent:antigravity
- **Status**: PLAN
- **Workflow state**: EDIT
- **Created**: 2026-10-02

## Goal and scope

Fix TestQL GUI interpreter when handling relative URL paths in GUI_START / NAVIGATE
and support optional input values in FLOW / GUI_INPUT steps. Validate all GUI scenario
suites sequentially against DisplayNet.

## Acceptance criteria

- [ ] AC-01: GUI_START resolves relative paths (e.g. /connect-id) against base_url instead of failing with local executable not found.
- [ ] AC-02: GUI_INPUT supports omitted text (or '-' placeholder) without throwing 'GUI_INPUT requires selector and text'.
- [ ] AC-03: Sequentially execute and pass TestQL test-gui-* scenario suites against DisplayNet.
- [ ] AC-04: Existing TestQL unit tests pass and governance checks succeed.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: User requested sequential testing of all functionalities with testql, fixing the library directly if GUI testing fails, and merging the changes.

## Evidence boundary

Operational test receipts and browser execution logs remain local state.
