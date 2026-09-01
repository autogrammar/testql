# Ticket preprompt

- **Task ID**: ticket-005
- **Task title**: Harden external Docker build
- **Created**: 2026-09-01T22:29:28Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
Use only digest-pinned tool/runtime stages and the committed `uv.lock`; do not
change dependencies, executable source or integration-owned paths.
