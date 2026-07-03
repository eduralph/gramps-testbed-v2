## Summary
**User impact:** Change a preformatted note's font size and then set it back to the default, and it looks right in the editor but prints at the wrong size in reports — with no way to undo it. A note whose size was never touched prints correctly; one that was changed and reset does not.

This makes resetting a size to the default actually clear it, so the note behaves like one that was never changed.

Reported in Mantis [#3214](https://gramps-project.org/bugs/view.php?id=3214).

## What to look at
The whole change is one guard: when the size (or font, colour, highlight) you pick is already the default, don't leave a hidden override behind. To try it: in a preformatted note, set the font size to 12, then back to 10, and confirm no size override remains. A new headless test does exactly this.

## Root cause
The apply path removes any prior tag for a style, then unconditionally applies a fresh tag — even when `value == StyledTextTagType.STYLE_DEFAULT[style]` (FONTSIZE default = 10, `gramps/gen/lib/styledtexttagtype.py:99`). The buffer already honours this invariant in the other write paths — `clear_selection` removes a tag only when `value != STYLE_DEFAULT[style]` (`gramps/gui/widgets/styledtextbuffer.py:519`), and `after_insert_text` re-applies only when `value and value != STYLE_DEFAULT[style]` (`:354`). The apply path was the one place that broke it.

## Fix
`StyledTextBuffer._apply_style_to_selection` now guards both the int (FONTSIZE) and str (FONTFACE, FONTCOLOR, HIGHLIGHT) branches (`gramps/gui/widgets/styledtextbuffer.py:476–483`) to skip tagging when the value equals the default, so applying a default value removes any prior tag without re-applying one.

## Verification
- **Claim:** setting a style back to its default leaves the text in the same tagged state as if the style had never been applied.
- **Checked:** `gramps/gui/widgets/styledtextbuffer.py:476–483` on `maintenance/gramps61` — apply now guards on `value != STYLE_DEFAULT[style]`, matching `clear_selection`/`after_insert_text`.
- **Test:** `gramps/gui/widgets/test/styledtextbuffer_test.py` (new) — FONTSIZE 12 → 10 leaves no explicit tag; a back-to-default note (18 → 10) carries identical tags to an untouched note; a genuine non-default size (12) is still recorded; and the str-typed branch (FONTFACE) upholds the same invariant. Red with the production change reverted, green with the fix.

Fixes [#3214](https://gramps-project.org/bugs/view.php?id=3214)

