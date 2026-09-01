---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-002
---
# Participant: codex (AI agent)

## Understanding

TestQL 1.2.66 crashes when an API response is PNG/PDF because the classic
runner decodes every body as strict UTF-8. The editable 1.2.67 checkout avoids
the crash with replacement characters, but does not preserve binary evidence,
and the Unified IR executor still uses strict decoding. The repair should be a
single shared byte classifier used by both paths.

The user's `continue` instruction is `SESSION_EXECUTION_AUTHORIZATION` for this
implementation scope. The subsequent explicit `tak` authorizes the minimal
governance prerequisite: assign the repository's existing `testql/**` package
to the `core` workstream.

## Execution plan

1. Apply and validate the governance-owned correction assigning `testql/**`
   to `core`.
2. Add a shared response-byte classifier without a runtime dependency.
3. Adopt it in the classic and Unified IR HTTP executors.
4. Add focused JSON, text, PNG and PDF regression tests.
5. Run focused/full pytest, Docker and governance checks.

## Actual changes

- Read repository governance, roadmap, active tickets and both HTTP executor
  implementations.
- Reproduced the version split: project venv 1.2.66 fails on binary UTF-8,
  editable 1.2.67 completes but only retains replacement text.
- Created a bounded implementation ticket without touching executable source.
- Received explicit authority for the governance prerequisite and moved the
  ticket to `EDIT`.
- Added one dependency-free parser that classifies raw response bytes before
  decoding and records deterministic kind, normalized content type, byte
  length, SHA-256 and file magic.
- Routed both the classic interpreter and Unified IR API executor through the
  same parser. Classic OQL exposes evidence as `_body`; Unified IR exposes it
  as `body` and retains `_body` in execution variables.
- Preserved JSON object/list and bounded text compatibility, including legacy
  three-/two-value monkeypatch return shapes used by existing tests.
- Added contract tests for JSON, text, PNG, PDF, SVG, misleading MIME headers,
  classic OQL assertions and Unified IR assertions.
- Proved the contract against the live Viewer render endpoints and expanded
  its smoke scenario to assert raw-byte evidence rather than status alone.
- Validation passed: current focused `69 passed` (and the original wider
  selection `82 passed`), full TestQL `1704 passed, 9 skipped`, Viewer source
  suite `596 passed, 10 skipped`, live smoke `59/59`, E2E container
  `1690 passed, 23 skipped`, production container startup, Ruff, isolated
  mypy, all Compose configurations and governance.

## Resolved blockers

- `Dockerfile.e2e` previously copied the absent `src/` directory. Ticket-001
  corrected the repository packaging in PR #7, which Validator merged to
  `main` as `1125743e4854eed84c3ee7c6b0a5d17c572fd16f`.
- Root `TODO.md` is also owned by ticket-001, so this ticket records its status
  here instead of creating an overlapping governance diff.

Ticket-002 completed `VALIDATION` on the combined tree and moved to
`PUBLICATION`. It does not modify or claim ownership of the Docker, Compose or
root roadmap files brought in from `main`.

## Publication

- Validator approved exact HEAD `fe28201fd6d518da7aa38ae9e221904ffa26798e`
  after two stable reads.
- PR #6 was merged as `6b80259dadaee4738bf97d77ecd90b6f9a64f8f6`.
- Required post-merge CI passed in 9m15s and the remote branch was deleted.
- The separate organization metadata dispatch lacked its token; it was not a
  required TestQL check and did not change the publication verdict.

The implementation and publication are complete.
