# Brief — issue 11314 / gender-stats-columns-swapped-on-dbapi

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** gender-stats-columns-swapped-on-dbapi
- **Defect:** After converting/saving a tree to the SQLite (DBAPI) backend, the on-disk
  `gender_stats` table has its gender columns swapped relative to their names — the `female`
  column holds male counts and `male` holds female counts. Root cause (verified): the in-memory
  `GenderStats` tuple is `(male, female, unknown)`
  (gramps/gen/lib/genderstats.py:116,100,132), but `save_gender_stats`
  (gramps/plugins/db/dbapi/dbapi.py:1111–1121) unpacks it as `female, male, unknown = ...` and
  inserts those variables into the like-named columns — so the stored `female`/`male` columns
  are inverted. `get_gender_stats` (dbapi.py:1100–1109) reads them back with the same inversion,
  so Gramps round-trips correctly (the GUI looks fine) but the persisted columns are mislabeled
  and wrong to any external SQL consumer (the reporter saw this in DB Browser).
- **Success criterion:** after `save_gender_stats`, the SQLite `gender_stats.female` column
  holds female counts and `gender_stats.male` holds male counts (column semantics match their
  names), AND the in-memory round-trip (`get_gender_stats` → `save_gender_stats` →
  `get_gender_stats`) still preserves the `(male, female, unknown)` ordering, AND a tree saved
  before the fix is not silently inverted on read. Demonstrable by C4-verify against
  gramps/plugins/db/dbapi/test/db_test.py.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: a named database column stores the quantity its name denotes; a
  format-correctness fix must not silently invert data already written to existing databases.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** high
- **Scope:** the gender-count column mislabeling in the DBAPI gender_stats persistence
  (save/load), handled so existing databases stay correct. / out of scope: the in-memory
  `GenderStats` tuple order (genderstats.py is internally consistent — do not churn it); the
  BSDDB backend; unrelated schema columns.
- **Repro instruction:** on maintenance/gramps61, create/convert a tree to SQLite, populate
  people of known gender, then open the tree's `sqlite.db` externally and inspect
  `SELECT given_name, female, male FROM gender_stats` — the female/male counts are swapped
  versus the people's actual genders.
- **Test file:** gramps/plugins/db/dbapi/test/db_test.py (EXISTING — add cases). The test MUST
  drive the production `save_gender_stats`/`get_gender_stats` on a real DBAPI backend and assert
  the raw column semantics (principles.md §3.4), not a copy of the logic.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** none (test added to an existing file; no POTFILES change).
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/db/dbapi/dbapi.py` on
  upstream/maintenance/gramps61 — recent commits `Implement FamilySearch-Gramps Integration`
  (4972a2eb4e), `Small one-line fixes mainly to comments and log messages` (5aaad152a4), license
  text; none fixes the gender_stats column swap. No prior/closed PR found for this path.
- **Mantis:** 11314
- **Disposition hint:** likely-fix — **NEEDS-HUMAN (back-compat / migration):** existing SQLite
  trees already hold swapped columns, so the correctness fix must decide how to handle them
  (gender_stats is a derived, recomputable cache, so a schema-version bump + rebuild-on-upgrade
  is viable vs. accepting the legacy layout). That migration decision is the human's at sign-off.
