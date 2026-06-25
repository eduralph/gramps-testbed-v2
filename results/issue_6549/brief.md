# Brief — issue 6549 / odf-table-column-style-overflow

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** odf-table-column-style-overflow
- **Defect:** The ODF document generator names each table-column style with
  `chr(ord("A") + col)` (gramps/plugins/docgen/odfdoc.py:706 and :1096). Past column
  index 25 this emits non-letter characters, and at column index ≥ 63 it emits
  characters past `chr(127)` — yielding malformed/invalid column-style names and the
  reported error when a report renders a table with more than 63 columns (e.g. the
  census report's 78-column US-1840 table). A second, related inconsistency: the
  style-DEFINITION loop is capped at `min(get_columns(), 50)` (:701) while the
  style-REFERENCE loop iterates all columns (:1089), so for >50 columns the references
  point at style names that were never defined.
- **Success criterion:** Generating an ODF document that contains a table with more
  than 63 columns (e.g. 78) completes without error, every column references a
  column-style name that is valid and was actually defined, and the names are unique
  per column. Demonstrable by C4-verify (the test drives the production ODFDoc table
  emission and asserts well-formed, defined, unique column-style names for a >63-column
  table).
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md
  §1.1): the smallest reviewable delta. (Correctness requirement: a column-style name
  must be a valid, unique token for any column count, and definition and reference must
  agree.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium — one file, but two call-sites (style definition at :706, style
  reference at :1096) must stay consistent, plus the 50-column definition cap interacts
  with the uncapped reference loop.
- **Scope:** column-style identifiers emitted by the ODF docgen must be generated so
  they are valid and unique for an arbitrary number of columns, and the style-definition
  loop and the style-reference loop must produce matching names for every column. / out
  of scope: redesigning the census report; changing any non-column ODF style naming;
  cosmetic reformatting of odfdoc.py.
- **Repro instruction:** On maintenance/gramps61, render any report whose table has >63
  columns (steps: a census report containing the US-1840 census, a 78-column table). For
  the regression test, drive ODFDoc to open/close a table whose TableStyle declares >63
  columns and assert the generated column-style names are valid, defined and unique.
- **Test file:** gramps/plugins/docgen/test/odfdoc_test.py — must fail pre-fix
  (invalid/undefined column-style name for a >63-column table) and pass post-fix. The
  test MUST drive the production ODFDoc path (the same methods that emit the column
  styles), not a re-implementation of the naming logic (principles.md §3.4).
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds gramps/plugins/docgen/test/odfdoc_test.py (no translatable
  strings) → po/POTFILES.skip.
- **Prior-art check (triage cycles):** searched gramps/plugins/docgen/odfdoc.py history
  on upstream/maintenance/gramps61 (pinned worktree) — the `chr(ord("A") + col)`
  construction is unchanged and unguarded at both sites; no merged or open/closed PR
  found for this path addressing column overflow. Not previously fixed.
- **Mantis:** 6549
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
