# PR description

## Root cause

The pre-5.0 GEDCOM exporter mapped place parts into the ADDR/CITY structure by matching the (translated) place type against English "City"/"Town", so the place type drove the output. The 5.0 place-model rewrite removed that mapping entirely, and Python-3 UTF-8 correctly carries accented characters — so the reported discrepancy (export differing by place type) cannot reproduce on the current code.

## Fix

This patch adds a regression test (`gramps/plugins/export/test/exportgedcom_place_test.py`, new) that verifies:
1. An accented place title (e.g., "Forlì à la Côte") round-trips as UTF-8 in the exported PLAC line, preserving the accented bytes (ì, à, ô).
2. The PLAC output is byte-identical whether the place type is the accented "Città" or English "Town" — the type no longer drives the place export.

The test exercises the real production export path: it builds an in-memory tree, calls the real `GedcomWriter.write_gedcom_file()`, and inspects the raw bytes. Import-light shims (`sys.modules` stubs for `gramps.gui.*`) keep the test headless while exercising the real writer and place displayer.

## Verified against

- `gramps/plugins/export/exportgedcom.py:1579–1605` — `GedcomWriter._place()` emits only `PLAC = <place display name>` + MAP + notes, with no reference to place type
- `gramps/plugins/export/exportgedcom.py:1243–1245` — event export calls `_place()` with the event's place, reached via `_families()` → `_family()` → `_family_events()`
- `gramps/gen/display/place.py:88` and `gramps/gen/utils/location.py:39` — place display defaults to the place title when `place-auto=True` (config default), and the test sets both the `PlaceName` value and title for robustness

## Test

Regression test: `gramps/plugins/export/test/exportgedcom_place_test.py` (new). Two cases:

1. `test_accented_title_roundtrips_as_utf8` — exports a marriage place with title "Forlì à la Côte" and asserts the PLAC line contains the accented bytes as UTF-8.
2. `test_place_type_does_not_drive_place_export` — exports the same place twice, once typed as "Città" and once as `PlaceType.TOWN`, and asserts the PLAC output is identical (type does not drive it).

Both pass on the current production code (maintenance/gramps61 HEAD).

**Verify-first note:** This is a test that pins existing correct behaviour, not a fix for broken code. The C4-verify gate will emit `PDCA-UNVERIFIABLE` (exit 77) because there is no non-test production file to revert for the red-pass leg; this is expected per the brief. The human must clear §6 NEEDS-HUMAN at sign-off.

**POTFILES registration:** `po/POTFILES.skip` must be updated at commit time to register the new test file (it has no translatable strings). The test sorts before `exportvcard_test.py` at line 568.

Fixes #8362
