# Ticket 002: Support binary HTTP response assertions

- **ID**: ticket-002
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Make the classic and Unified IR HTTP runners classify response bytes before
decoding. Preserve JSON/text compatibility and expose bounded body evidence for
binary responses: media type, byte length, SHA-256 and detected magic type.

This ticket owns only the shared response parser, both HTTP executors and their
focused regression tests. It does not add a new DSL command or implement
domain-specific PNG/PDF/KiCad validation.

## Acceptance criteria

- [x] AC-01: The user's `continue` instruction is recorded as
  `SESSION_EXECUTION_AUTHORIZATION` for the stated binary-response scope.
- [x] AC-02: JSON objects/lists and bounded text retain their current public
  representation.
- [x] AC-03: Binary bodies are never decoded as UTF-8 and expose deterministic
  `content_type`, `byte_length`, `sha256` and `magic` evidence.
- [x] AC-04: Classic and Unified IR API execution use the same parser and cannot
  diverge on PNG/PDF responses.
- [x] AC-05: Focused tests, full pytest, Docker checks and
  `project/governance-check.sh` pass.

## Governance prerequisite

`.governance/manifest.json` assigns the `core` workstream only `src/**` and
`tests/**`, while this repository's production package lives under
`testql/**`. The active governance ticket `ticket-001` owns
`.governance/**`. The user explicitly authorized the minimal correction on
2026-09-01: add `testql/**` to `core.ownedPaths` without changing any other
workstream or delivery policy. The managed lock is updated to bind that local,
extendable manifest.

## Validation evidence

- Current focused HTTP/interpreter/IR suite: `69 passed`; the original wider
  implementation run also passed all `82` selected tests.
- Full suite after installing the repository's four local test plugins:
  `1704 passed, 9 skipped`.
- Ruff and isolated mypy check for the new dependency-free parser: passed.
- Viewer live scenarios against `127.0.0.1:8088`: `59/59 passed`, including
  byte-derived MIME/magic/size assertions for two PNG files, two SVG files and
  one PDF file.
- Viewer source validation: `596 passed, 10 skipped`; PCB/SCH hashes unchanged.
- Compose configuration for all three declared files: passed.
- Production image build and CLI startup: passed with TestQL `1.2.67`.
- E2E image build and execution: `1690 passed, 23 skipped`.
- Managed governance check and `git diff --check`: passed.

The repository-authored Docker packaging blocker was resolved independently by
ticket-001 and merged through PR #7. Ticket-002 was resumed and fully validated
on top of that exact `main` revision without taking ownership of Docker or
Compose paths.

## Publication evidence

Validator approved exact HEAD `fe28201fd6d518da7aa38ae9e221904ffa26798e`
after two stable policy reads and merged
[PR #6](https://github.com/autogrammar/testql/pull/6) as
`6b80259dadaee4738bf97d77ecd90b6f9a64f8f6`. Required post-merge CI passed in
9m15s and the remote ticket branch was deleted. The unrelated organization
metadata dispatch failed because its workflow received no authentication
token; this did not affect TestQL validation or publication.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
