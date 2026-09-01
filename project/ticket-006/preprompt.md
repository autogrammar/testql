# Ticket preprompt

- **Task ID**: ticket-006
- **Task title**: Lock E2E plugin build tools
- **Created**: 2026-09-01T22:36:01Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
Add only dev build tools already required by the local packages; keep production
runtime dependencies, Dockerfiles and plugin manifests unchanged.
