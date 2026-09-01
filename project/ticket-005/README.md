# Ticket 005: Harden external Docker build

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Harden both TestQL Docker build paths consumed by external repositories. Pin
the uv tool and Python runtime stages by immutable manifest digest, verify the
portable graph in no-sources mode, and install the project exclusively from the
committed lock in frozen, non-editable mode.

The E2E image also installs its declared `dev` extra from that lock and creates
distribution metadata for the four local plugins without invoking a second
dependency resolver or isolated build environment.

## Acceptance criteria

- [x] AC-01: The user's autonomous sequential-completion request is recorded as
  `SESSION_EXECUTION_AUTHORIZATION`.
- [x] AC-02: Every uv/Python Docker stage is selected by an immutable sha256
  digest.
- [x] AC-03: Production first checks the portable graph with `uv lock --check
  --no-sources`, then installs through `uv sync --frozen --no-editable` with
  the required `nlp2env` extra.
- [x] AC-04: E2E dependencies come from the same lock and local plugin sources
  require no package resolver.
- [x] AC-05: Both images build; production CLI, package tests, Compose,
  governance and Docker checks pass.
- [ ] AC-06: Exact-head protected publication closes TestQL issue #10 and
  provides an immutable revision for Koru.

## Authorization

The user's request to continue and close all tasks sequentially authorizes this
bounded TestQL issue #10 implementation and protected publication. It does not
authorize secrets, self-approval, direct merge or unrelated changes.

## Resolved prerequisite

The no-cache runtime image builds and runs TestQL 1.2.67, but the first E2E run
reported `1650 passed, 53 skipped, 10 failed`: local plugin imports worked via
`PYTHONPATH`, while entry-point discovery correctly failed because the packages
were not installed distributions. Ticket 006 locked `setuptools` and `wheel` in
the dev graph and proved resolver-free local metadata installation, so this
ticket resumes on merged revision `2528dcfcfe95b1b786016bf9956900f6f1797843`.

## Validation evidence

- No-cache production image `sha256:a78e6ba5e881b196eac6a12839fc93aca299664413260127433d6f68c2cf1fd1`
  reports TestQL 1.2.67, uv 0.11.28 and `nlp2env` 0.1.6.
- No-cache E2E image `sha256:a68a4fbe88dfc505771f9aebb2f2e3ae09c83e37651aa9208d31ac74a26f4744`
  installed all four plugins without build isolation or dependency resolution.
- Its `testql.plugins` catalog resolves `graphql`, `proto` and `sql` to the
  expected local distributions.
- Full container suite: `1701 passed, 12 skipped, 1 warning` in 17.82 seconds;
  all 1713 previously collected cases completed without failure.
- Both Docker build checks and all three root Compose configurations pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
