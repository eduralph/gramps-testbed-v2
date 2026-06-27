## Root cause

The `remove_uninteresting_parents` method in `gramps/plugins/graph/gvfamilylines.py:664–822` keeps ancestors via a fixed set of heuristics to decide which people to include in the Family Lines Graph report when "remove extra people and families" is enabled. One heuristic (lines 772–791) checks if an ancestor's surname string matches any person of interest, with no lineage-based criterion independent of surname text.

A top-of-tree direct ancestor with a single child of interest, no further kept parents, and no person-of-interest status is kept *only* by the surname-equality test (lines 804–806); when that surname spelling drifts between generations, the legitimate bloodline ancestor is removed as "extra" despite being included by "follow parents".

## Fix

Extract the people/family-selection logic into a new GUI-free class `FamilyLinesSelection` (a testable seam: depends only on the database and option flags, not on the Report base or GUI machinery). The selection methods move verbatim from `FamilyLinesReport` to the new class with one change:

1. Add a new `_direct_ancestors()` method (line 260–293 in the patched file) that computes the transitive closure of parent links from the interest set, deciding membership purely by lineage (parent links), cached to avoid recomputation.

2. In `remove_uninteresting_parents`, check if a person's handle is in the direct-ancestor set *before* the surname heuristic (lines 650–251 in the patched file). A direct-line ancestor is never "extra"; surname spelling drift no longer prunes the legitimate direct line.

3. `FamilyLinesReport.begin_report` now constructs a `FamilyLinesSelection`, calls its `select()` method, and copies the four results back onto `self` — production routes through the extracted unit; the report and the test drive the identical implementation.

## Verified against

- `gramps/plugins/graph/gvfamilylines.py:590–662` — `find_parents()` builds the initial set of direct-line ancestors by recursively following parent-family links.
- `gramps/plugins/graph/gvfamilylines.py:664–822` — `remove_uninteresting_parents()` applies keep-heuristics; the new lineage-based criterion (lines 650–251 of the patched code) is checked before surname text matching (lines 772–791 in the original).
- `gramps/plugins/graph/gvfamilylines.py:823–870` — `find_children()` extends the set downward; direct-line membership is computed only from `find_parents` output.
- `po/POTFILES.skip` — registers the new test file (no translatable strings, same registration style as existing `year_only_date_test.py`).

## Test

New regression test `gramps/plugins/graph/test/gvfamilylines_test.py`: drives the production `FamilyLinesSelection.find_parents()` + `remove_uninteresting_parents()` on a real in-memory database (created via `import_as_dict` from an inline fixture). The fixture is a four-generation direct line where the paternal surname drifts every generation (Smith → Smithe → Smyth) with a married-in spouse each generation. The test asserts that no direct-line ancestor is pruned, including I0005 "Smyth" (the drifted top-of-line great-grandfather) and I0006 "White" (the married-in great-grandmother). Import-light: `gvfamilylines` imports only `gramps.gen.*` (no `gramps.gui`); the existing `year_only_date_test.py` already imports it and runs headless in the core suite.

Fixes #10415
