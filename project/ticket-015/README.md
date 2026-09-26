# Ticket 015: support insecure ssl and cookie jar in api runner

- **ID**: ticket-015
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-26

## Goal and scope

Support `insecure` SSL context (for `.local`, self-signed, internal TLS certificates, and explicit `insecure: true` / `TESTQL_INSECURE=1`) and persistent HTTP cookie jar session across multi-step API calls in TestQL's `ApiRunnerMixin`. Auto-propagate `X-CSRF-Token` when `csrf` variable is captured in scope.

## Acceptance criteria

- [x] AC-01: In `_api_runner.py`, use persistent `CookieJar` and `HTTPCookieProcessor` across requests.
- [x] AC-02: Support unverified SSL context for `.local` hosts or when `insecure: true` in config / `TESTQL_INSECURE=1`.
- [x] AC-03: Auto-inject `X-CSRF-Token` header if `csrf` variable is present in interpreter variables and not already explicitly set.
- [x] AC-04: Existing and new tests pass, governance checks pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
