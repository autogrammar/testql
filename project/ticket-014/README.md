# Ticket 014: feat(gui): support remote CDP browser attach via cdp_url

- **ID**: ticket-014
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-25

## Goal and scope

Allow TestQL to attach directly to an existing, already-running Chromium browser via Chrome DevTools Protocol (`cdp_url` or `browser.cdp_url`), such as a physical display kiosk on Raspberry Pi:
1. In `_start_playwright`, detect if `cdp_url` / `browser.cdp_url` is configured.
2. If configured, attach via `playwright.chromium.connect_over_cdp(cdp_url)` instead of launching a new isolated browser.
3. Reuse existing active pages in the browser context so interactions occur directly on the physical display without opening unwanted new windows or resetting kiosk state.

## Acceptance criteria

- [x] AC-01: Detect `cdp_url` / `browser.cdp_url` in `_start_playwright` and connect over CDP using `p.chromium.connect_over_cdp()`.
- [x] AC-02: Reuse existing pages/contexts from the attached remote browser.
- [x] AC-03: Add unit tests in `tests/test_cdp_remote_attach.py`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
