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

## Blockers

- None after the explicitly authorized ownership correction passes governance.
