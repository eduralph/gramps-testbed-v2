# ODF table column-style naming for tables with >63 columns

## Root cause

The ODF docgen names table-column styles using `chr(ord("A") + col)`, which is only valid and unique for columns 0–25 (A–Z). Past column 25, this produces non-letter characters; past column 62, it emits characters beyond `chr(127)`, yielding malformed style names that fail ODF validation. A second independent defect caps the style-definition loop at `min(get_columns(), 50)` while the style-reference loop iterates all columns, so for tables wider than 50 columns every excess column references a style name that was never defined.

## Fix

Add a module-level helper `_column_style_suffix(col)` (new, inserted at line 425) that generates spreadsheet-style bijective base-26 tokens (A, B, … Z, AA, AB, … AZ, BA, …), a valid, unique identifier for any column count. Update the style-definition loop (odfdoc.py:701) to remove the 50-column cap (`range(0, min(style.get_columns(), 50))` → `range(0, style.get_columns())`) and use the new helper at both the definition site (odfdoc.py:706) and the reference site in `start_table` (odfdoc.py:1096). Both sites now route through a single source of truth, ensuring valid, unique, and consistent column-style names for any table width. Register the new test file in `po/POTFILES.skip` (alongside the sibling `latexdoc_test.py`).

## Verified against

- `gramps/plugins/docgen/odfdoc.py:701` — the style-definition loop cap removed
- `gramps/plugins/docgen/odfdoc.py:706` — the definition site now calls `_column_style_suffix(col)`
- `gramps/plugins/docgen/odfdoc.py:1096` — the reference site now calls `_column_style_suffix(col)`
- `gramps/plugins/docgen/test/odfdoc_test.py` — new test file (not previously present)
- `po/POTFILES.skip:556` — test file registered in the skip list (alongside `latexdoc_test.py`)

## Test

The regression test `gramps/plugins/docgen/test/odfdoc_test.py` (new) drives the production ODFDoc emission path — the same `init()` (column-style definitions) and `start_table()` (column-style references) methods a real report uses — for a 78-column table. It then asserts on the generated content XML that: (1) one reference is emitted per column (78), (2) every referenced suffix is a valid ASCII-letter token (`^[A-Za-z]+$`), (3) every referenced name was actually defined (no undefined references), and (4) referenced names are unique per column. These assertions directly verify the fix for both defects (naming overflow and definition/reference mismatch) as named in the brief's Success criterion. The test imports only `ODFDoc` (no `gi`/`gramps.gui`), so it is safe for headless C4 core runners. Pre-fix, the test fails with invalid names (punctuation, control characters) and 28 undefined column references (cols 50–77); post-fix, all assertions pass.

Fixes #6549
