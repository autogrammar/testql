# Ticket 019: Run Wellman CI without site-packages

- **ID**: ticket-019
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-01

## Goal and scope

Run the existing metadata checker with Python -S so runner-installed packages
cannot mask missing dependencies. Preserve the pinned source and existing gates.

## Acceptance criteria

- [ ] AC-01: Local and hosted metadata validation runs without site-packages.
- [ ] AC-02: Managed governance validates this scope.
- [ ] AC-03: Independent Validator merges the tested head.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: the owner requested completion, testing, push
and protected merge of Wellmanifest adoption across Autogrammar repositories.
This authorizes process invocation, not trusted merge approval.

## Evidence boundary

Raw output and receipts remain private external operational state.
