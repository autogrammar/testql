# Ticket 001: Adopt wellmanifest/new-project governance pack

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-17

## Goal and scope

Complete the adopted governance pack's Docker boundary so the repository's
declared production and E2E images build from the actual `testql/` package
layout. Keep the production image limited to the CLI runtime; keep tests and
local plugin installation in the E2E image. Make all declared Compose files
exercise the E2E image without obsolete `src/` mounts.

## Acceptance criteria

- [x] AC-01: The user's `continue` instruction after the exact Docker blocker
  was reported is recorded as `SESSION_EXECUTION_AUTHORIZATION`.
- [x] AC-02: `Dockerfile` builds and starts the TestQL CLI from `testql/`.
- [x] AC-03: `Dockerfile.e2e` installs the local SQL, Proto, GraphQL and desktop
  plugins and runs the complete configured pytest suite.
- [x] AC-04: All declared Compose files resolve to the E2E Dockerfile without
  an obsolete `src/` bind mount.
- [x] AC-05: Focused Docker builds/tests, host pytest and the managed governance
  check pass.

## Validation evidence

- Production image build and `testql --version`: passed (`1.2.67`).
- Runtime lexicon and bundled scenario probe: passed.
- Focused plugin/IR container suite: `77 passed`.
- Focused packaged-resource regression: `183 passed`.
- Complete E2E image: `1683 passed, 23 skipped`.
- Complete E2E execution through `compose.e2e.yml`: `1683 passed, 23 skipped`.
- Host suite: `1697 passed, 9 skipped`.
- All three Compose configurations and managed governance check: passed.

The runtime image is approximately 707 MB because the current mandatory
dependency graph pulls Playwright, LiteLLM, pandas, boto3 and notebook tooling.
Dependency separation belongs to the integration workstream and is deliberately
not mixed into this packaging repair.

## Publication evidence

Validator approved exact HEAD `d7ff12cb98cd86510320f1e9d8e41f3161c423d4`
and merged [PR #7](https://github.com/autogrammar/testql/pull/7) as
`1125743e4854eed84c3ee7c6b0a5d17c572fd16f`. Required post-merge CI passed and
the remote ticket branch was deleted. The implementation is complete; the
ticket stayed active only as the governance owner of the post-merge README,
changelog and roadmap reconciliation that followed.

That reconciliation was approved for exact HEAD
`101df583750a153b3f29b4ff86ffd71f2c55b8cb` and merged through
[PR #8](https://github.com/autogrammar/testql/pull/8) as
`e24f0ba406c77347ec951d2858146b6d9836d4e5`. Required CI passed, Validator
converged after two stable reads, and the remote documentation branch was
deleted. No implementation or documentation work remains in this ticket.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-devin.md](ai-devin.md)
- Agent participant: [ai-codex.md](ai-codex.md)
