## Root cause

`get_birth_or_fallback` and `get_death_or_fallback` (gramps/gen/utils/db.py:53–74) return the primary Birth/Death event as soon as one exists, regardless of whether it has a usable date. When a person has a dateless primary Birth event and a dated Baptism fallback, `get_age` (gramps/gen/utils/db.py:95) receives the dateless event and, after finding its date invalid (line 120: `birth_date.get_valid() and not birth_date.is_empty()`), returns `None` instead of consulting the dated fallback.

## Fix

Add an opt-in `require_date=False` parameter to `get_birth_or_fallback` (line 53) and `get_death_or_fallback` (line 74), plus a shared `_has_usable_date(event)` helper. When `require_date=True`, a primary event without a usable date is skipped, allowing a dated fallback (e.g. Baptism for birth, Burial for death) to be returned instead. `get_age` now calls both helpers with `require_date=True` (lines 109–110 on the fallback path), while existing callers default to `require_date=False` and see no behaviour change.

## Verified against

- gramps/gen/utils/db.py:53–74 — `get_birth_or_fallback` and `get_death_or_fallback` signatures and fallback-selection logic
- gramps/gen/utils/db.py:95–126 — `get_age` function, including the validity check at lines 120–122
- gramps/gen/utils/db.py:109–110 — the fallback branch calls to the two helpers
- po/POTFILES.skip — registry of test files to skip during translation (existing `*_test.py` entries matched)

## Test

gramps/gen/utils/test/db_test.py (NEW) — a unittest-based regression test (headless, no `gi`/`gramps.gui`). Two cases:

1. `test_dateless_birth_falls_back_to_dated_baptism` — verifies that a person with a dateless place-only Birth event, a dated Baptism, and a dated Death event yields an age (50 years) computed from the Baptism date, not `None`.
2. `test_dated_primary_birth_unaffected` — verifies that a person whose primary Birth event has a date computes age from that birth (not from a differently-dated Baptism), so the fix does not regress the dated-primary path.

The test drives the production `get_age` path (the same function fanchartview calls), not a re-implementation.

Fixes #7832
