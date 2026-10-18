# Ticket 029: Support default value variable interpolation when oqlos-core is installed

- **ID**: ticket-029
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-18

## Goal and scope

Ensure `VariableStore.interpolate` in `testql.base` and `testql._base_fallback` supports `${var:-default}` syntax (with environment fallback when unset in the variable store), even when `oqlos.core.base.VariableStore` is imported from an older `oqlos-core` installation.

## Acceptance criteria

- [x] AC-01: `VariableStore.interpolate` expands `${var:-default}` using stored variable, `os.environ`, or fallback default.
- [x] AC-02: Unit tests in `tests/test_ir_runner_interpolation.py` cover `${var:-default}` interpolation via `testql.base.VariableStore`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
