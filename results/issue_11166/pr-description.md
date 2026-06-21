## Root cause

`LaTeXDoc.calc_latex_widths` builds the `\setlength{\grpictsize}` LaTeX command with `"".join((...))` over a tuple of fragments; one fragment is the bare numeric `self.pict_width` (a float) instead of its text form. Because `str.join()` requires every item to be a `str`, emitting a picture cell raises `TypeError: sequence item 1: expected str instance, float found`.

The two sibling emission sites already stringify the width consistently with `repr()`, but `calc_latex_widths` was the odd one out.

## Fix

**gramps/plugins/docgen/latexdoc.py:849** — wrap `self.pict_width` in `repr()` so the numeric value is rendered as text in the LaTeX markup, matching the two sibling emission sites at :804 and :1235.

**gramps/plugins/docgen/test/latexdoc_test.py** — extend the existing docgen test suite with `LaTeXPictureInTableTest`, which drives the production `LaTeXDoc` table+picture path via the real API (`start_table` → `start_row` → `start_cell` → `add_media` → `end_cell` → `end_row` → `end_table`) and asserts the emit raises no `TypeError`.

## Verified against

- **gramps/plugins/docgen/latexdoc.py:804** — `repack_row` already uses `repr(self.pict_width)` when emitting the picture width, matching the fix at :849
- **gramps/plugins/docgen/latexdoc.py:1235** — the cell emit also uses `repr(self.pict_width)`, consistent with both :804 and (now) :849
- **gramps/plugins/docgen/latexdoc.py:703** — `pict_width` is initialized as `0` (int), set to numeric width `x` at :1455, confirming the value is always numeric at emission
- **gramps/plugins/docgen/test/latexdoc_test.py** — existing `StrIncrTest` (testing the multicolumn counter, bug 13418) is preserved; the new `LaTeXPictureInTableTest` extends it with the picture-in-table case (bug 11166)

## Test

**gramps/plugins/docgen/test/latexdoc_test.py::LaTeXPictureInTableTest::test_picture_cell_emits_without_typeerror** — builds a one-column table through the real `LaTeXDoc` API with a picture cell (call `add_media` with float width 5.0), then asserts `end_table()` (which calls `calc_latex_widths`) raises no `TypeError`. The test forces `HAVE_PIL = True` via `mock.patch.object` to reproduce the affected user's environment; a `.jpg` input causes the production code to skip actual image conversion, so no Pillow install is exercised.

Without the fix, the test fails with the exact `TypeError: sequence item 1: expected str instance, float found` at line 846; with the fix, all three tests (the two pre-existing `StrIncr` tests plus the new picture test) pass.

Fixes #11166
