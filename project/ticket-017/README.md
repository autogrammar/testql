# Ticket 017: Restore binary response test HTTP isolation

- **ID**: ticket-017
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-01

## Goal and scope

The classic interpreter uses a cookie-aware urllib opener. The binary-response
contract test mocked only urlopen and accidentally contacted example.invalid.
Mock both HTTP boundaries in the shared fixture without changing product code.

## Acceptance criteria

- [x] AC-01: Binary, SSL/cookie and optional-unreachable contract tests pass.
- [ ] AC-02: Managed governance gate and GitHub CI pass.
- [ ] AC-03: Independent protected publication merges the exact tested head.

## Tracking boundary

Scoped test repair; preserve existing runtime behavior and other writers' files.
