# Ticket 013: feat(gui): keyboard, mouse, and hardware scanner support

- **ID**: ticket-013
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-25

## Goal and scope

Add comprehensive keyboard, mouse, and hardware scanner (QR/Barcode/RFID) support to TestQL:
1. Provide GUI keyboard press commands (`GUI_PRESS` / `PRESS` / `KEY`) with Playwright `keyboard.press()` and TestTOON table mapping.
2. Provide GUI hover and mouse commands (`GUI_HOVER` / `HOVER`, `GUI_MOUSE` / `MOUSE`) with Playwright `hover()` / `mouse.*` and TestTOON table mapping.
3. Provide hardware scanner commands (`SCANNER_SCAN` / `SCANNER_STATUS`) and TestTOON `SCANNER` table expansion supporting dual-mode: in-page wedge event injection (`window.dispatchEvent` with `barcodeScanned`) and hardware ingest API HTTP fallback (`/api/v3/identification/scanner/ingest`).
4. Support `KEYBOARD` / `KEY` and `SCANNER` tables in TestTOON parser.

## Acceptance criteria

- [x] AC-01: Implement `GUI_PRESS` / `PRESS` / `KEY` in `_gui.py` and map in `_gui_expand.py` and `_testtoon_parser.py`.
- [x] AC-02: Implement `GUI_HOVER` / `HOVER` and mouse actions in `_gui.py` and map in `_gui_expand.py`.
- [x] AC-03: Implement `ScannerMixin` (`SCANNER_SCAN`, `SCANNER_STATUS`) in `_scanner.py` with in-page DOM/wedge event dispatch and scanner ingest HTTP fallback.
- [x] AC-04: Support `SCANNER` and `KEYBOARD` tables in TestTOON parser (`_testtoon_parser.py`).
- [x] AC-05: Unit test coverage in `tests/test_keyboard_mouse_scanner.py` passing cleanly.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
