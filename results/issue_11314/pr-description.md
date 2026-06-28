# Fix gender_stats column swap on DBAPI save/read (bug 11314)

## Root cause

The DBAPI backend's `save_gender_stats` and `get_gender_stats` both treated the in-memory `GenderStats` tuple as `(female, male, unknown)` when it actually stores `(male, female, unknown)`, so each count landed in the opposite database column. This produced correctly round-tripping in-memory data but persisted mislabeled columns visible to external SQL consumers (e.g., DB Browser for the reporter).

## Fix

`gramps/plugins/db/dbapi/dbapi.py`:

1. `save_gender_stats` now unpacks the tuple correctly as `male, female, unknown = gstats.stats[key]` (lines 1128–1129 post-fix) and inserts into the like-named columns (line 1137). It also sets a metadata marker `gender_stats_fixed = True` (line 1140) to track corrected tables.
2. `get_gender_stats` branches on that marker (lines 1104–1116 post-fix): with marker, it reads the corrected column order; without it (legacy pre-fix tables), it reads the swapped order and re-applies the same inversion so the in-memory tuple is still correct and data is not silently inverted on read.

Two regression tests added to `gramps/plugins/db/dbapi/test/db_test.py`:
- `test_gender_stats_column_semantics` (lines 66–83): asserts the raw on-disk columns store the correct counts and the in-memory round-trip preserves order.
- `test_gender_stats_legacy_not_inverted` (lines 85–109): ensures a pre-fix-format row (swapped columns, no marker) reads back to the correct in-memory tuple, guarding against naive fixes that would break backward compatibility.

## Verified against

- `gramps/gen/lib/genderstats.py:116` — tuple construction order `(male, female, unknown)`
- `gramps/plugins/db/dbapi/dbapi.py:1105–1109` (pre-fix `get_gender_stats`) — legacy column read order
- `gramps/plugins/db/dbapi/dbapi.py:1115–1121` (pre-fix `save_gender_stats`) — legacy unpacking order
- `gramps/gen/db/generic.py:918` — saves gender stats on close, so legacy data heals to corrected layout on the first save after upgrade

## Test

Regression tests in `gramps/plugins/db/dbapi/test/db_test.py` drive the production `save_gender_stats`/`get_gender_stats` on a real in-memory SQLite DBAPI backend (not a logic copy), asserting both raw column semantics and backward compatibility. Pre-fix, the raw columns fail the semantic check; a naive fix without the legacy branch would fail the backward-compatibility check.

Verification (`PDCA_BUNDLE=… engine/scripts/ubuntu/run-verify.sh`): green-with-fix; red-without-fix; black formatting check passed.

Fixes #11314
