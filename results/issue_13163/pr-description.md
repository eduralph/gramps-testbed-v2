# German date parser: regression test for "bis" modifier (bug 13163)

## Root cause

With the German UI, entering "bis 1760" ("until 1760") as a date was silently
converted to "0.8.1760" (August 1760). The parser did not recognize "bis" as a
modifier and fell through to month-name matching, where the loose prefix
abbreviation expansion matched "bisemond" (an old German month name for August,
month 8), yielding the incorrect conversion.

## Fix

The fix—adding "bis" to `DateParserDE.modifier_to_int` mapping to
`Date.MOD_TO`—is already in place on the target branch (maintenance/gramps61).
This merge adds a regression test to ensure the behaviour does not break in the
future. The test verifies that parsing "bis 1760" yields a to/until date
(modifier MOD_TO) for year 1760 with no month, never month 8 (August).

## Verified against

- `gramps/gen/datehandler/_date_de.py:219` — `"bis": Date.MOD_TO` is in the
  `DateParserDE.modifier_to_int` table, ensuring "bis" is consumed as a modifier
  before month-name matching is reached.
- `gramps/gen/datehandler/test/date_de_test.py` — new regression test (added)
  that asserts parsing "bis 1760" yields `modifier == Date.MOD_TO`,
  `year == 1760`, and `month == 0` (not 8), mirroring the structure of the
  existing Finnish parser test (`date_fi_test.py`).
- `po/POTFILES.skip:73` — the new test file is registered as having no
  translatable strings.

## Test

The regression test at `gramps/gen/datehandler/test/date_de_test.py` exercises
`DateParserDE.parse("bis 1760")` and verifies:
- `get_modifier() == Date.MOD_TO` (to/until modifier, not a month)
- `get_year() == 1760` (correct year)
- `get_month() == 0` (no month, explicitly not 8 / August)

The test imports only `gramps.lib.date.Date` and
`gramps.gen.datehandler._date_de.DateParserDE`, so it runs headless under plain
`unittest` without GUI, D-Bus, or display dependencies. The reported symptom
("bis 1760" → August) has been manually verified as already resolved on the
target branch; this test pins the fix against future regression.

Fixes #13163
