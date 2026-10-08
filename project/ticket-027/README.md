# Ticket 027: repair autoupdate support PR

- **ID**: ticket-027
- **Owner**: trusted-runner:PLF-17128
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-07

## Goal and scope

Repair pull request autogrammar/testql#43 at frozen head
`9b2f8cd073435b636ca0851c50a52b1d4e73698f` against fetched main
`aa92ec9fb8ff91a427ed3a3e5fa0ec55e0563caf`.

This ticket is the single integration ticket for the complete frozen PR diff
and the bounded repair delta. It owns only the exact candidate paths listed in
`intent.json`.

## Acceptance criteria

- [ ] AC-01: The CLI autoupdate path never performs a synchronous PyPI request
      during ordinary command startup.
- [ ] AC-02: Ticket intent records the exact PR-diff base and candidate path
      ownership required by the trusted runner.
- [ ] AC-03: Focused repository tests for the CLI autoupdate behavior pass.
- [ ] AC-04: Required todo2code evidence is emitted for ticket2dsl, code2dsl,
      docs2dsl and service2dsl.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
