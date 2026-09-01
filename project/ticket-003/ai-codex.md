---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-003
---
# Participant: codex (AI agent)

## Understanding

TestQL's external Docker build needs a portable frozen lockfile, but `uv.lock`
is absent from the coordination and dependency-manifest registries. This ticket
only declares that integration-owned contract before any lock or image change.

## Execution plan

1. Add `uv.lock` to the integration and dependency-manifest registries.
2. Run managed governance and declared Docker configuration checks.
3. Publish through exact-head Validator review.

## Actual changes

- Recorded the user's session execution authorization and started the narrow
  governance prerequisite for TestQL issue #10.
- Updated the managed lock digest to bind the local manifest extension required
  by the fail-closed governance gate.
- Declared `uv.lock` in all three required registries without changing runtime
  behavior; governance, Compose and Docker build checks passed.
- Moved the exact candidate to protected publication.

## Blockers

- None.
