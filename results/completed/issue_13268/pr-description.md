## Root cause

In the Notes editor the undo/redo handlers in `undoablestyledbuffer.py` restore the styled tags by calling `set_text()`, which replaces the **entire** buffer content. A full-buffer replace deletes the whole buffer, which collapses every `Gtk.TextMark` to offset 0 — including the marks that a bound `GtkTextView` uses to track its scroll position, causing the editor to jump to the top of the note after an Undo.

## Fix

The patch extracts the tag-application logic from `StyledTextBuffer.set_text()` into a new `apply_styled_tags()` method that reapplies tags to the **existing** text without replacing it. This preserves all `Gtk.TextMark`s in the buffer (which track viewport state), while still restoring correct styling.

The five undo/redo handlers that previously called `set_text()` now call `apply_styled_tags()` instead:
- `UndoableStyledBuffer._undo_insert()` — line 146
- `UndoableStyledBuffer._undo_delete()` — line 160
- `UndoableStyledBuffer._redo_insert()` — line 176
- `UndoableStyledBuffer._handle_undo()` — line 201
- `UndoableStyledBuffer._handle_redo()` — line 212

The new `apply_styled_tags()` method is added to `StyledTextBuffer` at line 594 (immediately after `set_text()`). Two new test files are registered in `po/POTFILES.skip` as no-translate paths.

## Verified against

- `gramps/gui/widgets/styledtextbuffer.py:594` — existing `set_text()` method extracted to expose `apply_styled_tags()` which reapplies tags without rebuilding text
- `gramps/gui/widgets/undoablestyledbuffer.py:146,160,176,201,212` — five undo/redo handlers switched from `set_text()` to `apply_styled_tags()`
- `gramps/gui/widgets/test/undoablestyledbuffer_test.py` — new regression test with two test cases exercising undo of insert and delete operations
- `po/POTFILES.skip` — new test files registered as no-translate

## Test

The regression test `gramps/gui/widgets/test/undoablestyledbuffer_test.py` is a headless unit test that stands in for the viewport by placing an independent `Gtk.TextMark` deep in a long (400-line) buffer. It calls `buf.undo()` and asserts the mark did **not** collapse to offset 0:

- **`test_undo_of_insert_preserves_viewport_mark`** — inserts text, places a viewport-stand-in mark, undoes, and verifies the mark survives at its original offset
- **`test_undo_of_delete_preserves_viewport_mark`** — deletes text, places a mark, undoes, and verifies the mark survives

Both tests drive the real production `UndoableStyledBuffer.undo()` path (`_undo_insert`/`_undo_delete` → `apply_styled_tags`), so any drift in the undo logic is caught. Pre-fix: `set_text()`'s full-buffer delete collapses the mark to 0 → **RED**. Post-fix: `apply_styled_tags()` touches no text, the mark survives → **GREEN**.
