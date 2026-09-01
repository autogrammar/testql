# Ticket 003: Assign Docker lockfile to integration

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Establish the missing ownership boundary for the portable `uv.lock` required by
TestQL issue #10. The integration workstream will own the dependency contract.
The ticket also restores the already-red required CI check by installing the
repository's declared `nlp2env` extra after `main` began importing it. It makes
no runtime or Docker implementation change.

## Acceptance criteria

- [x] AC-01: The user's autonomous sequential-completion request is recorded as
  `SESSION_EXECUTION_AUTHORIZATION` on 2026-09-01.
- [x] AC-02: `uv.lock` is declared as an integration-owned dependency manifest
  and shared integration path.
- [x] AC-03: No existing ownership or runtime behavior changes.
- [x] AC-04: Required CI installs the declared `nlp2env` test extra and passes
  the suite that already exercises that optional integration; its existing
  workflow path is explicitly assigned to governance.
- [x] AC-05: Governance, Docker configuration and protected exact-head
  publication checks pass.

The managed manifest lock is updated only to bind the resulting local
extendable manifest, following the repository's existing governance pattern.

## Authorization

The user's instruction to continue the interrupted session and close all tasks
sequentially authorizes this issue #10 prerequisite. It does not authorize
secret access, self-approval, direct merge or unrelated changes.

## Validation evidence

- Managed governance check: passed with zero errors and warnings.
- All three declared Compose configurations: passed.
- Docker engine `29.1.3` reachable; Docker build check: passed with no warnings.
- Declared `nlp2env` import and `PromptScenario` resolution: passed.
- `git diff --check`: passed.

The first protected publication attempt correctly stopped because required CI
on pre-existing `main` failed with `ModuleNotFoundError: nlp2env`. The workflow
installed `.[dev]` even though its suite imports the declared `nlp2env` extra;
the exact correction is validated by the replacement required check.

## Publication evidence

Validator run `33562763375` approved exact HEAD
`a604a49ca35d0b249dd641629ba61fbcb8011209` after the required `test` check
passed. PR #11 merged as `6e4c92b5da968ee223cc6917aadd651cf5876d77`
on 2026-09-01, and the remote ticket branch was deleted automatically.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
