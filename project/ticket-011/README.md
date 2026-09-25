# Ticket 011: Add native CDP command and auto browser discovery

- **ID**: ticket-011
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-25

## Goal and scope

Add native Chrome DevTools Protocol (CDP) execution, project-local `.playwright-browsers` discovery, and in-page `window.encoderMode` fallback in TestQL.

Key improvements:
- Auto-discover project-local `.playwright-browsers` across search roots and prioritize over hardcoded system paths.
- Add `GUI_CDP` / `CDP` commands to `testql.interpreter._gui` leveraging Playwright CDP sessions with target variable capture.
- Add `CDP` section support to `testql.interpreter._testtoon_parser` and `testql.adapters.testtoon_adapter`.
- Add automatic fallback from unreachable HTTP encoder mock (:8105) to in-page `window.encoderMode` via the active Playwright GUI page.

## Acceptance criteria

- [x] AC-01: Auto-discover `.playwright-browsers` in project root and parent directories.
- [x] AC-02: Support `GUI_CDP` command and `CDP` TestTOON table with parameter passing and target variable assignment.
- [x] AC-03: Fallback from HTTP port 8105 to in-page `window.encoderMode` in active Playwright GUI session.
- [x] AC-04: Unit tests in `tests/test_cdp_and_browser_discovery.py` pass cleanly.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
