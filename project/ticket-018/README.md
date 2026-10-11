# Ticket 018: Validate adopted Wellman source in CI

- **ID**: ticket-018
- **Owner**: agent:codex
- **Status**: PLAN
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-01

## Goal and scope

Complete infrastructure dependency AC-05 of merged ticket-016. Run the existing
metadata checker on pull requests and pushes to main using verified Wellman
source at 58d7ae1ba768ead256e0e9a05fd641a0d8faec28. The read-only job uses
immutable action revisions and does not invoke pip or a build backend.

## Acceptance criteria

- [ ] AC-01: Exact Wellman source validates the adopted repository locally and in CI.
- [ ] AC-02: Managed governance accepts the infrastructure scope.
- [ ] AC-03: Independent protected delivery accepts and merges the tested head.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: the owner requested installation, completion,
testing, push and protected merge of Wellmanifest adoption across Autogrammar.
This authorizes process invocation, not trusted merge approval.

## Tracking boundary

Raw output and receipts stay in private external state. This job preserves
existing product and governance gates and does not claim S3-S5 certification.
