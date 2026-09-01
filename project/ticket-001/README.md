# Ticket 001: Adopt wellmanifest/new-project governance pack

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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
- [ ] AC-02: `Dockerfile` builds and starts the TestQL CLI from `testql/`.
- [ ] AC-03: `Dockerfile.e2e` installs the local SQL, Proto, GraphQL and desktop
  plugins and runs the complete configured pytest suite.
- [ ] AC-04: All declared Compose files resolve to the E2E Dockerfile without
  an obsolete `src/` bind mount.
- [ ] AC-05: Focused Docker builds/tests, host pytest and the managed governance
  check pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-devin.md](ai-devin.md)
- Agent participant: [ai-codex.md](ai-codex.md)
