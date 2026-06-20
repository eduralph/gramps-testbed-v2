## Root cause

An empty date can be stored as `MOD_TEXTONLY` with empty text — the path used by the XML reader (`gramps/plugins/importer/importxml.py:2774` → `Date.set_as_text("")`). The Gramps-XML writer emits a `MOD_TEXTONLY` date as `<datestr val="…"/>` (gramps/plugins/export/exportxml.py:1074), so an empty date serializes to `<datestr val=""/>` — distinct from the pre-6.0.0 form (missing element). On re-import, this reconstructs the non-canonical form, breaking the roundtrip invariant and causing validation to flag it as an invalid date (gramps/plugins/tool/verify.py:247–248).

## Fix

Normalize empty text to a canonical empty date (`MOD_NONE`, `dateval = Date.EMPTY`) at the two entry points in gramps/gen/lib/date.py:

- `set_as_text(text)` (line 1939): when `text` is empty, set `MOD_NONE` instead of `MOD_TEXTONLY`. This path is used by the XML reader, so it closes the deserialize side — an empty `<datestr val=""/>` now imports as canonical.
- `Date.set(...)` (line 1827): after setting text, if the result is `MOD_TEXTONLY` with empty text, normalize to `MOD_NONE`. This covers the editor's text-only path, closing the serialize/export side.

The XML writer already omits `<datestr>` for `MOD_NONE` dates with empty ISO start (gramps/plugins/export/exportxml.py:1052–1074), so an empty date now exports without the `<datestr>` element, matching pre-6.0.0 behavior. The roundtrip is stable: `serialize() → unserialize() → serialize()` returns the same canonical empty tuple.

## Verified against

- gramps/gen/lib/date.py:1827, 1939 — empty-text normalization in `set` and `set_as_text`
- gramps/gen/lib/test/date_test.py:1729+ — 5 new test methods added to `EmptyDateTest` (no new file; existing test class)
- Red without fix: tests fail with 4 assertion errors; green with fix: all 45 tests pass
- Imports pass (no syntax/lint errors); black formatting clean

## Test

Added to gramps/gen/lib/test/date_test.py (class `EmptyDateTest`, lines 1746–1799; no new file, so no po/POTFILES.* change). Tests exercise the production path (`Date.set_as_text`, `Date.set`, `Date.serialize`, `Date.unserialize`):

- `test_set_as_text_empty_is_regular_empty` — `set_as_text("")` yields `MOD_NONE`, empty, and valid.
- `test_empty_text_date_serializes_canonically` — an empty date's serialized tuple equals `Date().serialize()` (the missing ≡ empty equivalence; transitively ensures the XML writer omits the element).
- `test_empty_date_serialize_roundtrip_stable` — serialize → unserialize → serialize is stable and empty.
- `test_set_text_only_with_empty_text_normalizes` — `Date.set(MOD_TEXTONLY, text="")` also yields `MOD_NONE`.
- `test_text_only_with_text_is_preserved` — regression: a genuine text-only date (non-empty text) keeps `MOD_TEXTONLY` and its text.

Fixes #13744
