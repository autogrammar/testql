# Ticket 009: feat(probe): detect layout anomalies and container breakout in browser probe

- **ID**: ticket-009
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-22

## Goal and scope

Enhance Playwright browser probe and result analyzer in TestQL to detect visual and layout anomalies during automated browser inspection:
1. Container breakout: child elements extending beyond parent container boundaries horizontally.
2. Viewport overflow: elements extending beyond window.innerWidth causing unwanted horizontal scrolling.
3. Squished text: text nodes with multiple words squeezed into excessively narrow widths.
4. Clipped overflow: hidden/clipped scrollWidth overflowing clientWidth on bounded elements.
5. Report findings as finding.browser.layout with remediation advice and diagnostic metadata.

## Acceptance criteria

- [x] AC-01: Layout anomaly detection script integrated into Playwright browser probe in testql/discovery/probes/browser/playwright_page.py.
- [x] AC-02: Analyzer surfaces finding.browser.layout and suggested fix in testql/results/analyzer.py.
- [x] AC-03: Regression tests verify layout anomaly detection in tests/test_browser_discovery.py.
- [x] AC-04: Successfully detects real-world choice-card container breakout anomalies on Clonerd web app.

## Participants

- Human participant: unresolved; user authorized continuation.
- Agent participant: Antigravity
