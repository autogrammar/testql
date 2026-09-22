# Ticket 010: fix(browser): refine layout probe for svg elements and resilient nlp2env import

- **ID**: ticket-010
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-22

## Goal and scope

Refine browser layout anomaly probe in `PlaywrightPageProbe` so internal SVG vector elements (`<circle>`, `<path>`, etc. inside `<svg>`) are not incorrectly treated as HTML container boundary breakouts.
Additionally, make `nlp2env` imports in `testql.nlp2env` lazy and guarded with `TYPE_CHECKING` so `testql.cli` can be imported and executed without requiring the optional `nlp2env` package.

## Acceptance criteria

- [x] AC-01: `PlaywrightPageProbe` ignores internal SVG vector children (`el.ownerSVGElement`) during HTML container breakout evaluation.
- [x] AC-02: `testql.nlp2env.__init__` and `runner.py` guard `PromptScenario` import to ensure `testql.cli` imports cleanly without `nlp2env`.
- [x] AC-03: Regression unit tests verify `testql.cli` resilience and browser discovery probe accuracy.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
