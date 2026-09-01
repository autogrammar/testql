---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-001
---
# Participant: codex (AI agent)

## Understanding

The governance pack declares Docker mandatory, but both Dockerfiles still copy
the removed `src/` layout and every Compose file mounts that absent directory.
This prevents ticket-002's otherwise validated binary-response change from
passing its required Docker gate. The repair belongs here because ticket-001
already owns all Docker and Compose paths.

The user's `continue` instruction, given immediately after this exact blocker
was reported, is `SESSION_EXECUTION_AUTHORIZATION` for this bounded repair.

## Execution plan

1. Bind the ticket to the Docker stack and actual package layout.
2. Separate the production CLI image from the test/plugin E2E image.
3. Point all declared Compose configurations at the E2E image.
4. Build both images and run focused plus complete container tests.
5. Run host regression and governance checks, then publish for protected review.

## Actual changes

- Created a separate ticket-001 worktree and branch from `origin/main`.
- Recorded the user's continuation authority without inventing human-owned
  participant content.
- Replaced the obsolete `src/` Docker inputs with the actual `testql/` package,
  copied the build metadata required by the wheel and added a working CLI
  entrypoint to the production image.
- Added a cached runtime stage and an E2E stage containing tests, root scenarios,
  `.testql` contracts and all local plugin sources needed by configured pytest.
- Installed the GraphQL, Proto, SQL and desktop plugins as editable packages so
  their entry points are discoverable during E2E execution.
- Set `PYTHONPATH=/app` so copied source assets such as NL lexicons and bundled
  diagnostic scenarios remain available even though the current wheel package
  data does not include them.
- Pointed all three Compose files at `Dockerfile.e2e` and removed stale bind
  mounts, producing reproducible tests from the image itself.
- Validation passed: runtime CLI/assets, `77` focused plugin tests, `183`
  resource regressions, full container/Compose `1683 passed, 23 skipped`, host
  `1697 passed, 9 skipped`, all Compose configs and governance.

## Publication

- Validator approved exact HEAD `d7ff12cb98cd86510320f1e9d8e41f3161c423d4`.
- PR #7 was merged as `1125743e4854eed84c3ee7c6b0a5d17c572fd16f`.
- Required post-merge CI passed and the remote branch was deleted.

The implementation publication is complete. The ticket remains active only
through the protected follow-up that reconciles root documentation with the
published Docker and binary-response work; a governance-only follow-up will
then mark it `DONE`.

The user's explicit request to update documentation is
`SESSION_EXECUTION_AUTHORIZATION` for this follow-up. The intent adds only the
previously omitted root `README.md`; that path already belongs to the
`governance` workstream, and no executable or shared-contract scope is added.
