# Ticket 004: Generate portable Docker lockfile

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Generate a portable `uv.lock` from TestQL's published package metadata while
ignoring the developer-only relative `tool.uv.sources` override. This is the
integration-owned dependency contract required by TestQL issue #10 and the
external Koru Docker build.

This ticket changes no dependency declaration, executable source or Dockerfile.

## Acceptance criteria

- [x] AC-01: The user's autonomous sequential-completion request is recorded as
  `SESSION_EXECUTION_AUTHORIZATION`.
- [x] AC-02: `uv lock --no-sources` produces a lockfile with no external
  relative-path or editable dependency; only the root project remains
  represented as editable `.` in uv's standard lock format.
- [x] AC-03: Repeated `uv lock --check --no-sources` validation is stable.
- [x] AC-04: Managed governance, Compose configuration, Docker build check and
  whitespace validation pass.
- [x] AC-05: Protected exact-head publication succeeds.

## Authorization

The user's request to continue and close all tasks sequentially authorizes this
bounded issue #10 dependency-contract step. It does not authorize secrets,
self-approval, direct merge or unrelated changes.

## Validation evidence

- uv 0.11.28 resolved 188 packages using `--no-sources`.
- Only the root TestQL project has uv's standard `editable = "."` record;
  external dependencies, including `vdisplay 0.1.58` and `nlp2env 0.1.6`,
  resolve from PyPI with artifact hashes.
- Two consecutive locked checks retained SHA-256
  `efe18353c7fc9edb6ab1963f11a92b54000a13afbd59229542bfa1d38185f1a7`.
- A clean `--locked --no-dev --extra nlp2env --no-sources --no-editable`
  sync installed the project and `testql --version` reported `1.2.67`.
- Managed governance, all declared Compose configs, Docker build check and
  `git diff --check`: passed.

## Publication evidence

Required CI passed and Validator run `33565378018` approved exact HEAD
`0c8faed91ee8210a1759926a61fcee28f67c025e`. PR #13 merged as
`8e759086b8e4ac4aeb4bb547d1f342430762170c` on 2026-09-01, and its remote
ticket branch was deleted. The advisory model was unavailable because the
generated lock required 50 chunks; deterministic checks remained the approval
authority.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
