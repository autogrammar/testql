# Ticket 006: Lock E2E plugin build tools

- **ID**: ticket-006
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Add the existing setuptools build backend and wheel helper to TestQL's dev
extra, then regenerate the portable lock with `--no-sources`. This lets the E2E
image create distribution metadata for four local plugins with
`--no-build-isolation --no-deps`, without invoking an external resolver.

This ticket adds no production runtime dependency and changes no Dockerfile or
plugin package declaration.

## Acceptance criteria

- [x] AC-01: The user's autonomous sequential-completion request is recorded as
  `SESSION_EXECUTION_AUTHORIZATION`.
- [x] AC-02: `setuptools` and `wheel` are dev-only and resolved with hashes in
  the portable lock.
- [x] AC-03: A locked/no-sources dev sync can install all four local plugin
  distributions with no build isolation and no dependency resolution.
- [x] AC-04: GraphQL, Proto and SQL entry points are discoverable and the
  focused registration tests pass.
- [x] AC-05: Governance, Compose and Docker build checks pass before protected
  exact-head publication.

## Validation evidence

- `uv lock --check --no-sources`: 190 packages; `setuptools==84.0.0` and
  `wheel==0.48.0` have registry artifacts and SHA-256 hashes.
- Locked dev plus `nlp2env` sync and resolver-free editable installation of
  all four plugins completed successfully.
- The `graphql`, `proto` and `sql` `testql.plugins` entry points resolve to
  their local distributions; focused regression suite: `77 passed`.
- `./project/governance-check.sh`: `GOV-PASS`.
- All three root Compose configurations and both Docker build checks pass.

## Authorization

The user's request to continue and close all tasks sequentially authorizes this
bounded prerequisite discovered while validating TestQL issue #10. It does not
authorize secrets, self-approval, direct merge or unrelated dependency changes.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
