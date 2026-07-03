## Summary

In the Note editor, changing a preformatted note's font size from the default (10) to a different value (e.g., 12) and back to 10 does **not** clear the FONTSIZE style tag. The stored text retains an explicit `FONTSIZE=10` tag. This appears correct in the editor but breaks report rendering: reports treat explicit tags as absolute overrides on the paragraph style, so the rendered size differs from a note whose size was never changed. The user has no way to restore the original.

**The fix:** `StyledTextBuffer._apply_style_to_selection` now skips applying an explicit tag when the value equals the style default, matching the invariant already enforced by `clear_selection`. Applying a default value removes any prior tag without re-applying one, leaving the text in the same tagged state as if the style had never been applied.

## What to look at

- `gramps/gui/widgets/styledtextbuffer.py:476–483` — the int/str style-apply branches now guard tag application on `value != STYLE_DEFAULT[style]`.
- `gramps/gui/widgets/test/styledtextbuffer_test.py` (new) — a headless unit test that exercises the public `apply_style` path and asserts that setting FONTSIZE from 12 back to 10 leaves no explicit tag.

## Root cause / Fix

The apply path removes any prior tag for a style, then unconditionally applies a fresh tag — even when `value == StyledTextTagType.STYLE_DEFAULT[style]` (FONTSIZE default = 10, `gramps/gen/lib/styledtexttagtype.py:99`). The buffer already honours this invariant in two other write paths:

- `clear_selection` removes a tag **only** when `value != STYLE_DEFAULT[style]` (`gramps/gui/widgets/styledtextbuffer.py:519`).
- `after_insert_text` re-applies a style **only** when `value and value != STYLE_DEFAULT[style]` (`gramps/gui/widgets/styledtextbuffer.py:354`).

The apply path was the one place that broke the invariant. The fix guards both the int (FONTSIZE) and str (FONTFACE, FONTCOLOR, HIGHLIGHT) branches to skip tagging when the value equals the default.

## Verified against

**Pre-fix (red):** Setting FONTSIZE from 12 back to 10 leaves an explicit `FONTSIZE=10` tag in the buffer's text — the regression test fails.

**Post-fix (green):**
- The tag is removed and not re-applied; `get_text().get_tags()` contains no FONTSIZE tag (`gramps/gui/widgets/test/styledtextbuffer_test.py:123`).
- A back-to-default note (set 18 → 10) carries identical tags to a note whose size was never touched (`gramps/gui/widgets/test/styledtextbuffer_test.py:135`).
- A genuine non-default size (12) is still recorded — no over-removal (`gramps/gui/widgets/test/styledtextbuffer_test.py:145`).
- The str-typed branch (FONTFACE) upholds the same invariant (`gramps/gui/widgets/test/styledtextbuffer_test.py:156`).

All regression tests pass on `upstream/maintenance/gramps61`.

## Test

`gramps/gui/widgets/test/styledtextbuffer_test.py` (new) — a headless unit test driving the public `apply_style` path: FONTSIZE 12 → 10 leaves no explicit tag; a back-to-default note (18 → 10) carries identical tags to an untouched note; a genuine non-default size (12) is still recorded; and the str-typed branch (FONTFACE) upholds the same invariant. Red with the production change reverted, green with the fix.

---

Fixes [#3214](https://gramps-project.org/bugs/view.php?id=3214)
