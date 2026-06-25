# Build notes — issue 6549 / odf-table-column-style-overflow

Target: gramps-project/gramps @ maintenance/gramps61 (worktree `gramps-6.1`,
HEAD `b679c084f6`).

## Root cause

The ODF docgen names each table-column style `<table-style>.<suffix>` where the
suffix is `chr(ord("A") + col)`. Two independent defects:

1. **Naming overflow.** `chr(ord("A") + col)` is a valid, unique letter only for
   `col` 0–25 (A–Z). At `col` 26 it emits `[`, `\`, `]`, … (punctuation the ODF
   validator rejects as a style name), and at `col` ≥ 63 it runs past `chr(127)`
   into control/non-ASCII characters — malformed style names. Both call sites used
   it: the column-style **definition** loop (`odfdoc.py:706` on the base branch) and
   the column-style **reference** loop in `start_table` (`odfdoc.py:1096`).

2. **Definition/reference mismatch.** The definition loop was capped at
   `min(style.get_columns(), 50)` (`odfdoc.py:701`) while the reference loop in
   `start_table` iterated *all* columns (`odfdoc.py:1089`). For a table wider than
   50 columns every column past 49 referenced a style name that was never defined.

Together these break the census report's 78-column US-1840 table (the reported case).

## Fix (smallest reviewable delta — non-structural behavioural fix, principles §1.1)

`gramps/plugins/docgen/odfdoc.py`:

- Add a module-level helper `_column_style_suffix(col)` (new, base-branch line 425)
  that returns a spreadsheet-style bijective base-26 token: A, B, … Z, AA, AB, … —
  a valid, unique identifier for **any** column count.
- Definition loop (base `:701`/`:706`): drop the `min(…, 50)` cap →
  `range(0, style.get_columns())`, and use `_column_style_suffix(col)`.
- Reference loop in `start_table` (base `:1096`): use `_column_style_suffix(col)`.

Both emission sites now route through the one helper, so definition and reference
names agree for every column and are valid/unique for any width. This is the
correctness requirement the brief names ("definition and reference must agree;
a valid, unique token for any column count").

## Why a shared helper, not two in-line fixes

Patching each `chr(...)` site in place with an in-line base-26 expression would
duplicate the naming logic across two call sites (the exact drift trap the brief
warns about: definition and reference must stay consistent). A single helper both
sites call is one source of truth and ~3 added call-line changes vs. two ~6-line
in-line loops — and it gives the test a way to exercise the *production* names
without re-implementing them.

## Test — `gramps/plugins/docgen/test/odfdoc_test.py` (new)

Drives the **production** path, not a re-implementation (principles §3.4): builds a
real `StyleSheet` with one 78-column `TableStyle`, a `PaperStyle`, and an `ODFDoc`,
then calls the production methods `doc.open()` → `doc.init()` (emits the column-style
**definitions**) → `doc.start_table()` (emits the **references**), and asserts on the
emitted content XML:

- one reference per column (78),
- every referenced suffix is a valid token (`^[A-Za-z]+$`),
- every referenced name was actually defined (definition ⊇ reference),
- referenced names are unique per column.

These are exactly the brief's Success criterion. The test imports `ODFDoc` only — no
`gi`/`gramps.gui` — so it is safe for the **headless** C4 core runner (`odfdoc.py`'s
`gi` uses are lazy, inside functions; importing the module does not pull a GUI). I
deliberately did **not** import the `_column_style_suffix` helper into the test: an
earlier draft did, which made the pre-fix red a bare `ImportError` (the helper is
reverted with the production change) rather than a real assertion failure — weak
evidence that the test catches the *bug*. Driving `init`/`start_table` instead, the
pre-fix red is a genuine failure (invalid `[`, `\`, control-char names; 28 columns
referencing undefined styles), demonstrating both defects.

## Verification (red → green)

The harness C4 runner (`engine/scripts/ubuntu/run-verify.sh`, docker) could not be
launched from this build sandbox (container exec required interactive approval), so I
ran the equivalent red→green locally against the `gramps-6.1` worktree on
`PYTHONPATH` with `GRAMPS_RESOURCES` set (the same `python3 -m unittest` the headless
C4 leg runs):

- **Green** (patch applied): all 4 tests pass.
- **Red** (production hunks reverted, test kept): `test_every_referenced_name_is_valid`
  fails on `[`, `\`, … control chars and `test_every_referenced_name_was_defined`
  fails with 28 undefined references (cols 50–77). C4's gate re-runs this in docker.

Black (target's formatter, the publish-commit hook) is clean on both touched `.py`
files (`black --check`).

## POTFILES

`gramps/plugins/docgen/test/odfdoc_test.py` has no translatable strings → registered
in `po/POTFILES.skip` (alongside the sibling `latexdoc_test.py`), per doc 16.

## Scope / limits

- Out of scope (per brief): census-report redesign, other ODF style naming, cosmetic
  reformatting.
- `TableStyle.colwid` is pre-allocated `[0] * 100` (`tablestyle.py:76`), so a table
  with **>100** columns would already `IndexError` in `set_column_width` independent
  of this bug. 78 (the reported case) is well within that; widening the column-width
  store is a separate, unrelated concern and left untouched.
