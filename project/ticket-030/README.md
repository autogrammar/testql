# Ticket 030: Honor explicit TestQL target and validate dry runs

- **ID**: ticket-030
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-26

## Goal and scope

Continue autogrammar/testql STARTER-023, discovered during maskservice PLF-17350/17354. Honor an explicit CLI --url when scenario CONFIG supplies a base_url default. Preserve ordinary SET behavior and scenario targets when no explicit override is supplied. Validate dry runs without claiming runtime assertion success or contacting devices.

SESSION_EXECUTION_AUTHORIZATION: The operator requested continued repair and testing after reviewing the hardware verification report. This authorizes bounded implementation, tests and protected publication; independent approval remains required.

## Acceptance criteria

- [x] AC-01: A two-server HTTP regression proves CONFIG cannot redirect requests away from an explicit CLI target.
- [x] AC-02: Scenario defaults and ordinary variable assignments keep their documented behavior without a CLI override.
- [x] AC-03: Dry-run validates response assertions without evaluating unavailable runtime responses or sending network requests.
- [ ] AC-04: Focused regressions and managed governance pass; publication is independently verified.

## Validation

114 focused target-selection, interpreter, TestTOON, HTTP, assertion and dry-run tests pass with managed governance. All 19 device E2E scenarios validate in dry-run (428 validated steps, zero executed). Two independent local HTTP servers prove the CLI-selected target receives requests and the scenario default receives none. Independent protected publication remains pending. Raw results stay in ignored operational receipts.
