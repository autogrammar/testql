---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-005
---
# Participant: codex (AI agent)

## Understanding

TestQL's externally consumed Dockerfile still used a mutable Python tag and
resolved dependencies with pip. The E2E image repeated both behaviors and then
invoked four additional editable package builds. The merged portable lock and
published plugin sources allow both paths to be resolver-free.

## Execution plan

1. Pin uv 0.11.28 and Python 3.12.14 stages by manifest digest.
2. Check the portable graph in no-sources mode, then replace pip resolution
   with frozen/non-editable uv sync.
3. Install E2E plugin metadata without build isolation or dependency resolution.
4. Build and execute both images, then run governance and Compose checks.
5. Publish through exact-head Validator review and close issue #10.

## Actual changes

- Recorded the user's session execution authorization and implemented the two
  bounded Docker build paths on the exact merged `ticket-004` base.
- Split portable-lock validation from frozen installation because uv 0.11.28
  correctly rejects simultaneous `sync --frozen --no-sources`: frozen performs
  no source resolution, while the preceding no-sources check binds the graph.
- Resumed after ticket 006 locked the dev build backend, and installed all four
  local plugin distributions with `--no-build-isolation --no-deps`.
- Built both images from scratch on immutable base digests. Production reports
  TestQL 1.2.67, uv 0.11.28 and `nlp2env` 0.1.6; the E2E image exposes all
  required plugin entry points and passes 1701 tests with 12 skips.

## Blockers

- None. Ticket 006 supplied and validated the frozen build-tool prerequisite.
