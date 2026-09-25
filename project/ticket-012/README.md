# Ticket 012: fix(cdp): unwrap params and handle HTTP 404 fallback in encoder

- **ID**: ticket-012
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-25

## Goal and scope

Fix CDP parameter unwrapping so nested quotes around JSON payloads are properly unwrapped without SyntaxError, and ensure HTTP 404/error on encoder mock automatically falls back to in-page `window.encoderMode` in active Playwright GUI session.

## Acceptance criteria

- [x] AC-01: Unwrap nested quotes around `params` in `_cmd_gui_cdp`.
- [x] AC-02: Prevent accidental double quoting of already quoted params in `_expand_cdp`.
- [x] AC-03: Fallback from HTTPError (including 404) to active GUI session `window.encoderMode` in `_encoder_call`.
- [x] AC-04: Unit tests in `tests/test_cdp_and_browser_discovery.py` pass cleanly.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
