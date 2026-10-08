# Ticket 022: Support TestTOON files in INCLUDE command

- **ID**: ticket-022
- **Owner**: agent:antigravity
- **Status**: PLAN
- **Workflow state**: EDIT
- **Created**: 2026-10-02

## Goal and scope

Allow the `INCLUDE` command to parse included TestTOON scenarios (`.testql.toon.yaml`)
using the interpreter's format detection (`self.parse(...)`) instead of assuming
legacy OQL syntax (`parse_oql`).

## Acceptance criteria

- [ ] AC-01: `INCLUDE` command parses TestTOON files through `self.parse(...)` instead of hardcoding `parse_oql`.
- [ ] AC-02: Unit test `tests/test_include_testtoon.py` passes.
- [ ] AC-03: Governance checks pass.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: User requested sequential testing of all functionalities with testql, fixing the library directly if GUI testing fails, and merging the changes.

## Evidence boundary

Operational test receipts and browser execution logs remain local state.
