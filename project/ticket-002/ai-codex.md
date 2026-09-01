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
- Validation passed: focused `82 passed`, full TestQL `1704 passed, 9 skipped`,
  Viewer `596 passed, 10 skipped`, live smoke `59/59`, Ruff, isolated mypy,
  Compose configuration and governance.

## Blockers

- `Dockerfile.e2e` still copies the absent `src/` directory, so the declared
  repository image cannot build. A clean Python 3.12 container probe of this
  ticket's parser passes, but the image definition is owned by active
  governance ticket `ticket-001`. Publication is blocked until that ticket
  corrects the packaging or explicitly hands off the path.
- Root `TODO.md` is also owned by ticket-001, so this ticket records its status
  here instead of creating an overlapping governance diff.
