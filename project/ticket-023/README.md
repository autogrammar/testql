# ticket-023: Preserve NL literal whitespace

- **ID**: ticket-023
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-02

## Goal and scope

Preserve exact literal arguments while matching normalized NL verb phrases. Keep repeated spaces, tabs and Unicode whitespace in the original remainder passed to existing extractors.

## Acceptance criteria

- [x] AC-01: New regressions fail on the base and pass after correction.
- [x] AC-02: NL subsystem tests and exact-base governance pass.
- [x] AC-03: Independent protected review approves and merges the exact head.

## Validation

14 new regressions fail before the correction; 135 NL subsystem tests pass after it. Exact literal spaces, tabs, nonbreaking spaces and Unicode survive recognition into GUI input, CSS selectors and SQL IR. Wellman reports zero errors and warnings. Raw logs remain private; independent publication is pending.
