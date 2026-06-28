# Build notes — issue 11314 (gender_stats columns swapped on DBAPI)

## Root cause (confirmed against source)

`GenderStats` keeps each entry in memory as `(male, female, unknown)`
(`gramps/gen/lib/genderstats.py:116`, `:100`, `:132`).

The DBAPI persistence layer was self-consistent but mislabeled on disk:

- `save_gender_stats` (`gramps/plugins/db/dbapi/dbapi.py:1115` pre-fix) unpacked the
  tuple as `female, male, unknown = gstats.stats[key]` and inserted those vars into the
  like-named columns → the `female` column received the **male** count and the `male`
  column received the **female** count.
- `get_gender_stats` (`dbapi.py:1105` pre-fix) read `SELECT given_name, female, male,
  unknown` and mapped `(row[1], row[2], row[3])` straight to `(male, female, unknown)`,
  i.e. it re-applied the same inversion, so the in-memory round-trip looked fine and the
  GUI was unaffected. Only an external SQL reader (DB Browser, the reporter's case) saw
  the mislabeling.

## What the fix does

`gramps/plugins/db/dbapi/dbapi.py`:

1. `save_gender_stats` now unpacks `male, female, unknown = gstats.stats[key]` and inserts
   into `(given_name, male, female, unknown)` — each count lands in the column whose name
   denotes it (Success criterion #1). It also records a metadata marker
   `gender_stats_fixed = True` (via `_set_metadata(..., use_txn=False)` inside the existing
   save transaction).
2. `get_gender_stats` branches on that marker:
   - marker present → `SELECT given_name, male, female, unknown` (corrected layout);
   - marker absent (a tree written before the fix) → `SELECT given_name, female, male,
     unknown` (legacy/swapped layout). Either way it builds the in-memory
     `(male, female, unknown)` tuple correctly.

This satisfies all three parts of the Success criterion:
- new writes store correct column semantics;
- the in-memory round-trip preserves `(male, female, unknown)` (after a save the marker is
  set, so the read uses the corrected branch);
- a pre-fix tree is **not silently inverted on read** — absent the marker the legacy
  branch reads the swapped columns back into the right tuple, exactly as the old code did.
  The first subsequent `save_gender_stats` (Gramps saves gender stats on close,
  `gramps/gen/db/generic.py:918`) rewrites the table in corrected layout and sets the
  marker, so the data heals to correct on-disk semantics on next save.

The `CREATE TABLE gender_stats` columns are left as `(female, male)` — per the tracker
(Nick_H ~0057524: "I wouldn't make any changes to the CREATE statement"). The INSERT/SELECT
name their columns explicitly, so the create order is irrelevant.

`_get_metadata`/`_set_metadata` are already available on the class and are called during
`load()` after the serializer is set (`generic.py:738`), before `get_gender_stats` runs
(`generic.py:793`), and the adjacent index reads at `generic.py:797+` already use
`_get_metadata` — so the marker lookup is safe at that point.

## Alternative considered and rejected: schema-version bump + rebuild-on-upgrade

The "proper migration" Nick_H/prculley discussed (rebuild gender stats on a schema
upgrade) means bumping `DbGeneric.VERSION` from `(22, 0, 0)` to `(23, 0, 0)` and adding a
`gramps_upgrade_23`. **Cost / blocker, not an adjective:**

- `gramps/gen/db/generic.py:422` is `VERSION = (22, 0, 0)` on `maintenance/gramps61`.
  `maintenance/gramps60` is `VERSION = (21, 0, 0)` (`gramps-6.0/.../generic.py:423`) and
  **master is also `(22, 0, 0)`** (`gramps/.../generic.py:422`). Schema versions are
  allocated per release; `6.1` and `master` currently share `22`. Bumping `6.1` to `23`
  would collide with the number the next release will take and create an inconsistent
  schema-version lineage across the maintenance/master branches — a `git apply` would be
  clean but the change would be *wrong on the target* (CLAUDE.md "cherry-pickable" rule).
- It also forces every existing `6.1` tree through a full schema upgrade (`_gramps_upgrade`
  rebuilds secondary + reference maps, `generic.py:2803-2806`) for a derived,
  recomputable cache — heavyweight for a maintenance-branch fix.

The marker approach restores correct column semantics on a maintenance branch **without**
a schema-version change, which is why it is the chosen fix. It also matches the brief's
named option "accepting the legacy layout" while still meeting criterion #3 (no silent
inversion).

## Tradeoff to flag for the human (NEEDS-HUMAN: migration)

Because the schema version is unchanged, an **old** (unfixed) Gramps could still open a
tree written by the **fixed** Gramps and would read the corrected columns with its old
swapped SELECT — i.e. inverted in that backward direction. This affects only the derived
name→gender guess for previously-unseen given names, and only when downgrading Gramps.
The schema-bump alternative would instead block the downgrade outright. The brief assigns
this migration policy to the human at sign-off; the disposition hint already marks it
NEEDS-HUMAN.

Out of scope (untouched): `gramps/plugins/db/bsddb/bsddb.py:195-207` writes the same legacy
column order during BSDDB→DBAPI conversion and sets no marker, so my legacy read branch
interprets its output correctly — consistent, and BSDDB is explicitly out of scope.

## Test (`gramps/plugins/db/dbapi/test/db_test.py`, existing file, cases added)

Added to `DbPersonTest` (real in-memory SQLite DBAPI backend, drives production
`save_gender_stats`/`get_gender_stats` — not a copy of the logic, per principles §3.4):

- `test_gender_stats_column_semantics`: saves a controlled `GenderStats({"Probe": (5, 2, 1)})`
  (asymmetric so a swap is detectable; deterministic rather than relying on the shared-db
  `genderStats` which accumulates across the class's tests — the first draft used the
  shared object and saw doubled `(6,2,2)` counts), then asserts the **raw** columns
  `SELECT male, female, unknown ... = (5, 2, 1)` and that the round-trip preserves order.
  This is the red→green driver: pre-fix the raw columns read `(2, 5, 1)`.
- `test_gender_stats_legacy_not_inverted`: writes a pre-fix-format row (swapped columns,
  no marker) and asserts `get_gender_stats` returns the correct `(male, female, unknown)`.
  Green on both original and fixed code, but **red on a naive fix** that swaps the SELECT
  without the legacy branch — it guards criterion #3.

## Verification

`PDCA_BUNDLE=… engine/scripts/ubuntu/run-verify.sh` →
`C4-verify: green-with-fix=PASS / red-without-fix=PASS` (PASS-ON-ESSENTIAL: the clean
upstream 6.1 leg hits the known pre-existing `headless-ut-segfault`, so it verifies on the
essential worktree; recorded in `essential-dependency.json`).

`black` run over both changed files: no reformatting needed (commit-ready for the target's
pre-commit hook).

No files added/removed → no `po/POTFILES.in`/`.skip` change (the test file already exists).
