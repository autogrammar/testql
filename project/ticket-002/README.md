# Ticket 002: Support binary HTTP response assertions

- **ID**: ticket-002
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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
- [ ] AC-02: JSON objects/lists and bounded text retain their current public
  representation.
- [ ] AC-03: Binary bodies are never decoded as UTF-8 and expose deterministic
  `content_type`, `byte_length`, `sha256` and `magic` evidence.
- [ ] AC-04: Classic and Unified IR API execution use the same parser and cannot
  diverge on PNG/PDF responses.
- [ ] AC-05: Focused tests, full pytest, Docker checks and
  `project/governance-check.sh` pass.

## Governance prerequisite

`.governance/manifest.json` assigns the `core` workstream only `src/**` and
`tests/**`, while this repository's production package lives under
`testql/**`. The active governance ticket `ticket-001` owns
`.governance/**`. The user explicitly authorized the minimal correction on
2026-09-01: add `testql/**` to `core.ownedPaths` without changing any other
workstream or delivery policy. The managed lock is updated to bind that local,
extendable manifest.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
