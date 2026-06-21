# PR description

## Root cause

The surname-grouping consumers (TopSurnamesGramplet, SameSurnames quick view, and FilterByName) resolved group names inconsistently: some used `Name.get_group_name()` (which ignores the database-wide name-group mapping) and the SameSurnames filter rule matched on raw `get_surname()`. The only database-aware resolver is `NameDisplay.name_grouping_name(db, name)` which honors both the per-name override and the global mapping — but only TopSurnamesGramplet consulted it, making the consumers disagree when surnames were globally grouped.

## Fix

Route all three surname consumers through the canonical `NameDisplay.name_grouping_name(db, name)` so they all honor both the per-name "group as" override and the database-wide name-group mapping:

- `gramps/plugins/gramplet/topsurnamesgramplet.py`: `record_surnames()` now takes `db` as its first argument and tallies by `name_grouping_name()` instead of `get_group_name()`.
- `gramps/plugins/quickview/samesurnames.py`: the `SameSurname` filter rule's `apply_to_one()` now matches on the group name instead of the raw surname; a new helper `_same_surname_handles()` centralizes the group resolution so both the `run()` display path and the filter rule drive one implementation.
- `gramps/plugins/quickview/filterbyname.py`: the "unique surnames" tally now uses `name_grouping_name()` instead of `get_group_name()`, so it matches the SameSurnames display (which this quick view's double-click opens).

## Verified against

- `gramps/gen/display/name.py:1102-1117` — the canonical `NameDisplay.name_grouping_name(db, pn)` that the fix routes all consumers through
- `gramps/plugins/gramplet/topsurnamesgramplet.py:55-80` — `record_surnames()` now calls `name_grouping_name(db, name)` on lines 68 and 71
- `gramps/plugins/quickview/samesurnames.py:59-63` — `SameSurname.apply_to_one()` previously matched on raw `get_surname()`; now matches on `name_grouping_name(db, name)`
- `gramps/plugins/quickview/samesurnames.py:272-296` — new `_same_surname_handles()` helper driving both `run()` and the filter rule through one code path
- `gramps/plugins/quickview/filterbyname.py:463-241` — "unique surnames" tally now uses `name_grouping_name()` instead of `get_group_name()`

## Test

Extended `gramps/plugins/gramplet/test/topsurnamesgramplet_test.py` with a new `SurnameGroupingConsistencyTest` class that:

1. Builds a real in-memory sqlite database with Smith and Jones persons
2. Sets `db.set_name_group_mapping("Jones", "Smith")` (the "Group As → Group All" global mapping)
3. Drives all three consumer code paths and asserts they gather the same {Smith, Jones} group:
   - `SameSurname(["Smith"]).apply_to_one(db, ...)` — the filter rule run() builds
   - `_same_surname_handles(db, ...)` — the function run() calls
   - `record_surnames(db, ...)` — the TopSurnames tally

All tests (5 existing + 4 new) pass with the patch applied; the red leg (production code reverted, test kept) fails on the key assertion `test_samesurnames_filter_honors_global_mapping: AssertionError: False is not true`, confirming the fix is necessary.

Fixes #6825
