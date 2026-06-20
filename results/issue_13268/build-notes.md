# Build notes — issue 13268 / notes-editor-undo-scroll-jump

## Root cause (two sentences)

In the Notes editor the undo/redo handlers
(`gramps/gui/widgets/undoablestyledbuffer.py`) restore the styled tags by calling
`self.set_text(s_text)`, which replaces the **entire** buffer content via
`Gtk.TextBuffer.set_text` (a full delete-all + reinsert). A full-buffer replace
collapses every `Gtk.TextMark` — including the marks a bound `GtkTextView` uses to
track its scroll position — to offset 0, so after an Undo the editor jumps to the
top of the note.

## Why the fix is where it is

The text is already correct *before* the `set_text` call in every undo/redo handler:
`_undo_insert` has already `delete()`d the inserted run (`undoablestyledbuffer.py:146`
on `maintenance/gramps61`), `_undo_delete` has already re-`insert()`ed the deleted
run (`:160`), and `_handle_undo`/`_handle_redo` change no text at all (`:201`, `:212`).
`set_text` is therefore called **only to restore styling**, but it does so by
rebuilding the whole buffer — and that rebuild is the cause of the scroll jump.

The fix removes the cause: extract the tag-application loop of
`StyledTextBuffer.set_text` into a new `apply_styled_tags(s_text)` method
(`styledtextbuffer.py:594` on target → refactored) that reapplies tags to the
**existing** text without replacing it (`remove_all_tags` + `apply_tag`), and have
`set_text` call it. The five undo/redo handlers then call `apply_styled_tags`
instead of `set_text`:

- `undoablestyledbuffer.py:146` `_undo_insert`
- `undoablestyledbuffer.py:160` `_undo_delete`
- `undoablestyledbuffer.py:176` `_redo_insert`
- `undoablestyledbuffer.py:201` `_handle_undo`
- `undoablestyledbuffer.py:212` `_handle_redo`

`_redo_delete` (`:191`) already does not call `set_text` (it's commented out), so it
is untouched. Tag correctness is preserved: `remove_all_tags` over the whole buffer
then reapplying the saved `undo_action.tags` yields exactly the same tag state that
`set_text` produced — `set_text` got fresh untagged text from
`Gtk.TextBuffer.set_text` and applied the same tags; here we strip then apply the
same tags. The only behavioural difference is that the buffer's text (and its marks)
are no longer torn down and rebuilt.

## Alternative considered and rejected — editor-level scroll guard

The obvious one-line idiom is, in `StyledTextEditor.undo`/`redo`
(`styledtexteditor.py:1009`, `:1012`), to re-scroll after the rebuild:

```python
def undo(self, *obj):
    self.textbuffer.undo()
    self.scroll_mark_onscreen(self.textbuffer.get_insert())   # +1 line
def redo(self, *obj):
    self.textbuffer.redo()
    self.scroll_mark_onscreen(self.textbuffer.get_insert())   # +1 line
```

That is **+2 lines** vs. this fix's ~15 changed lines, so it is the smaller diff. I
rejected it anyway, on the two axes the brief makes load-bearing:

1. **It guards the symptom, not the cause.** The full-buffer `set_text` rebuild still
   happens; we merely scroll back afterwards. The rebuild still collapses *all* other
   marks every undo (selection bounds, any future second view on the same buffer),
   and it forces a scroll-to-cursor even in cases where the viewport never moved. The
   brief names an **Invariant to restore** ("undo reverts the text *without scrolling*
   the GtkTextView to the top"); per principles §1.2/§2 the target is the smallest
   change that *restores the invariant*, not the smallest diff. Re-scrolling does not
   restore "without scrolling" — it scrolls twice.

2. **It is not headlessly testable.** `scroll_mark_onscreen` is a `GtkTextView`
   (widget) method; asserting its effect needs a realized widget + display, which the
   C4 gate (plain `python3 -m unittest`, no display) does not have. It would force an
   interface test, which the C4 classifier cannot run red→green (it recognises only
   `*_test.py` core / `test_*.py` addon) → `PDCA-UNVERIFIABLE`. The buffer-level fix,
   by contrast, lives in a plain `Gtk.TextBuffer` subclass that needs **no display**,
   so the cause is directly exercisable headlessly.

## Test — headless proxy for the viewport

`gramps/gui/widgets/test/undoablestyledbuffer_test.py` (new; `test/` singular,
`*_test.py` suffix — core convention). A `GtkTextView`'s scroll position cannot be
asserted without a display, but the *cause* (full-buffer rebuild collapsing marks)
can: the test creates a real `UndoableStyledBuffer`, seeds a 400-line note (with
`undo_disabled()` so only the edit under test is on the stack), makes an edit
(insert in one case, delete in the other), places an **independent `TextMark` at the
edit site deep in the note** as a stand-in for the viewport, calls the production
`buf.undo()`, and asserts the mark did **not** collapse to offset 0.

- Pre-fix: `set_text`'s whole-buffer delete moves the mark to offset 0 → `assertGreater(0, 0)` fails → **RED**.
- Post-fix: `apply_styled_tags` touches no text, the mark survives → **GREEN**.

The test drives the real production `UndoableStyledBuffer.undo()` →
`_undo_insert`/`_undo_delete` → `apply_styled_tags` path (no hand-copy), so any drift
in the production undo path is caught. Verified via
`engine/scripts/ubuntu/run-verify.sh`: `green-with-fix=PASS / red-without-fix=PASS`.

## Housekeeping

- New core `.py` files registered in `po/POTFILES.skip` (no translatable strings):
  `gramps/gui/widgets/test/__init__.py` and
  `gramps/gui/widgets/test/undoablestyledbuffer_test.py` (doc 16 §Adding and removing
  Python files).
- `black` run over all touched files (target repo's commit hook runs black).

## Scope / 13267

The brief flags issue **13267** (same GIF) as a possible shared-undo-handler cause.
This fix touches the shared undo **and** redo path (`undoablestyledbuffer.py`), and
redo is in scope ("paste/redo behaviour beyond what shares the same handler" is out
of scope — redo *does* share this handler). If 13267 is also a "undo/redo jumps the
note view to the top" report, it is fixed by the same change. I did **not** broaden
the patch to claim 13267, and did not bundle it silently — **flag for the human** to
confirm 13267's symptom against this handler at sign-off rather than assume it.
