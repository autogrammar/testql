# Ticket Changelog (ticket-002)

## [0.1.0] - 2026-09-01

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Recorded `SESSION_EXECUTION_AUTHORIZATION`, the binary-response acceptance
  criteria and the unmapped `testql/**` workstream blocker.
- Recorded explicit authorization to add `testql/**` to `core.ownedPaths` and
  resumed the ticket in `EDIT`.
- Added shared binary-safe HTTP response evidence for classic OQL and Unified
  IR API execution, with JSON/text compatibility and PNG/PDF/SVG regression
  tests.
- Validated the implementation with the full TestQL and Viewer suites plus a
  live render smoke test.
- Moved the ticket to `BLOCKED` in validation because the pre-existing
  `Dockerfile.e2e` copies missing `src/`; that path belongs to active
  governance ticket `ticket-001`.
- Resumed validation after ticket-001 fixed Docker packaging and PR #7 was
  merged to `main`; ticket-002 itself does not modify the Docker-owned paths.
- Revalidated the combined tree with the focused and full host suites, Ruff,
  mypy, all Compose configurations, managed governance, both container builds,
  the full E2E image suite and the live Viewer scenarios.
- Completed every acceptance criterion and moved the ticket to `PUBLICATION`.
