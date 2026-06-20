# Brief — issue 13268 / notes-editor-undo-scroll-jump

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** notes-editor-undo-scroll-jump
- **Defect:** In the Notes editor, working in a note long enough to have a scroll bar, pressing **Undo** also scrolls the editor to the top/first line — forcing the user to scroll back down to where they were. (Mantis 13268; confirmed, always reproducible.)
- **Success criterion:** Performing **Undo** in the Notes editor leaves the visible scroll position (and the cursor) at the edit site — the viewport is **not** reset to the top of the note — while the text state is correctly reverted.
- **Invariant to restore:** An Undo in the Notes editor preserves the editor's viewport — undo reverts the text without scrolling the `GtkTextView` to the top. (The undo handler must restore/keep scroll-and-cursor position after applying the reverse edit. Source: the notes-editor undo path in `gramps/gui/editors/editnote.py` and its `StyledTextEditor` / `GtkTextView` undo-stack integration.) SELF-TEST: stated over the undo operation in the notes editor generally, not the one repro note — category-level.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core).
- **Surfaces:** gui
- **Scope:** Undo in the Notes editor resets the scroll to the top instead of preserving position — make undo preserve the viewport/cursor. / **out of scope:** the editor's other undo correctness (text content is reverted fine — only the scroll jumps); paste/redo behaviour beyond what shares the same handler; issue **13267** (the same GIF in note 2 shows both — confirm whether 13267 shares this undo handler before broadening; if it does, flag to the human rather than silently bundling).
- **Repro instruction:** open a note long enough to require scrolling (Do builds a seeded long-note fixture — `example.gramps` notes are too short); scroll to the bottom; press Undo → editor jumps to the top. Root cause: the undo handler reapplies text without saving/restoring the `GtkTextView` scroll mark; confirm by reading the undo callback in `gramps/gui/editors/editnote.py` / the styled-text editor widget.
- **Test file:** Scroll position is hard to assert headlessly, so this is GUI-facing: ship an interface test `tests/interface/test_bug_13268_notes_undo_scroll.py` in gramps-testbed (subclass `GrampsInterfaceTestCase`) driving the note editor on the seeded long-note fixture and asserting the scroll/cursor position is preserved after undo. If a headless seam exists (the undo handler exposes the saved scroll mark independent of display), prefer a core `gramps/gui/editors/test/editnote_test.py` (`test/` singular, `*_test.py`) exercising that seam. If neither yields a runnable red→green C4 mechanic, flag `PDCA-UNVERIFIABLE` per INTEGRATION §3 with a numbered manual repro for the human.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change.
- **New/removed files:** if a new core `test/` file is added, register it in `po/POTFILES.skip` (no translatable strings) per doc 16 §Adding and removing Python files. (An interface test in gramps-testbed is not a core file — no POTFILES entry.)
- **Prior-art check (triage cycles):** search by path at Do time — `git -C ../gramps log upstream/maintenance/gramps61 -- gramps/gui/editors/editnote.py gramps/gui/widgets/styledtexteditor.py` (also `master`) + closed/rejected PRs for "note undo" / "styledtext undo". Related: **13267** (same GIF, possible shared undo-handler cause — read first).
- **Mantis:** 13268
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
