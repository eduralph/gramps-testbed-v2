# Brief — issue sqlite-export-6.1 / Sqlite addon Person round-trip breaks on core 6.1

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** sqlite-export-person-serialize-6.1
- **Defect:** The Sqlite addon's `example.gramps` export→import round-trip raises
  `ValueError: too many values to unpack (expected 21, got 22)` against gramps core
  6.1. Core 6.1 added a 22nd field — `familysearch_sync` (index 21) — to
  `Person.serialize()`/`unserialize()` (commit `4972a2eb4e` "Implement
  FamilySearch-Gramps Integration", via the new `FamilySearchSyncBase` mixin), but the
  addon hardcodes a fixed 21-tuple: `ExportSql.export_person` unpacks 21 names from
  `person.serialize()` (`ExportSql.py:684`), and `ImportSql._process` builds a 21-tuple
  for `Person.unserialize()` (`ImportSql.py:705`). The crash is in **export** (in the
  test's `setUp`), not import as the tracking issue surmised. Surfaced as the
  `addons-source gramps61 × core 6.1` leg of the addon-unit matrix; the
  `gramps60 × core 6.0` leg is green (21-field Person).
- **Success criterion:** The `example.gramps` export→import round-trip through the
  Sqlite addon completes without error against core 6.1's 22-field Person
  serialization **and** continues to pass against core 6.0's 21-field form — i.e.
  `Sqlite.tests.test_sqlite.ExportSQLTestCase` is green on **both** the gramps61×core-6.1
  and gramps60×core-6.0 addon-unit legs.
- **Invariant to restore:** The Sqlite addon's Person export/import must agree with the
  targeted core version's `Person.serialize()`/`unserialize()` field set — it must
  round-trip a Person against every core it declares support for. The addon ships from a
  single shared `ExportSql.py`/`ImportSql.py` on both `maintenance/gramps60`
  (`Sqlite.gpr.py gramps_target_version="6.0"`) and `maintenance/gramps61`
  (`="6.1"`), so the same code must tolerate both the 21-field 6.0 form and the
  22-field 6.1 form. Source: gramps core `gramps/gen/lib/person.py` `serialize`/
  `unserialize` are the positional contract the addon consumes; `Sqlite.gpr.py
  gramps_target_version` declares the supported core(s). (Behavioural/data-format
  compatibility fix — `docs/principles.md` §1.1; minimalism is scoped to **Person**, the
  only object whose serialize tuple changed in 6.1 — verified across `gramps/gen/lib/` —
  not a blanket arity-tolerance refactor.) SELF-TEST: not satisfiable by guarding one
  module — it is the addon's cross-version agreement with core's serialization contract.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
  (addons production; the maintainer cherry-picks forward to gramps61 — INTEGRATION §2).
  The fix lives in the shared `ExportSql.py`/`ImportSql.py`, so the cherry-pick to
  gramps61 must remain correct: it must keep the gramps60×6.0 leg green and make the
  gramps61×6.1 leg green. (NEEDS-HUMAN — see Verification note: branch-target is a
  judgment call given the defect is 6.1-only.)
- **Surfaces:** data (backend/logic export→import round-trip; no GUI E2E — the addon-unit
  runner uses xvfb only because the module imports Gtk at load, not for any UI interaction).
- **Scope:** Restore the Person export→import round-trip in the Sqlite addon so it works
  against core 6.1's 22-field `Person.serialize()` while remaining correct against core
  6.0's 21-field form. The change is confined to the Person handling in `ExportSql.py`
  (`export_person`, the unpack at `ExportSql.py:684`) and `ImportSql.py` (the person
  section of `_process`, the tuple built for `Person.unserialize` at `ImportSql.py:705`).
  / out of scope: (a) other primary objects — only Person's serialize tuple changed in 6.1
  (verified: no other `gramps/gen/lib` object gained a field), so do not touch the
  event/family/note/etc. handlers; (b) persisting the new `familysearch_sync` payload —
  the addon's SQL `person` table stores only a subset of Person fields, so a faithful,
  error-free round-trip of the fields the addon's schema already represents is sufficient;
  adding schema to persist familysearch_sync is a separate enhancement; (c) any blanket
  "derive every object's tuple arity dynamically" refactor.
- **Repro instruction:** fixture `example.gramps`. On core 6.1:
  `CORE_VERSION=6.1 ./engine/scripts/ubuntu/run-addon-unit.sh Sqlite` → ERROR in
  `setUp`: `ValueError: too many values to unpack (expected 21, got 22)` at
  `ExportSql.py:684` (`export_person(db, person.serialize())`). On core 6.0:
  `CORE_VERSION=6.0 ./engine/scripts/ubuntu/run-addon-unit.sh Sqlite` → green (confirms
  the 6.0/6.1 split). Verified locally against the `gramps-6.1` worktree.
- **Test file:** `Sqlite/tests/test_sqlite.py` (addon `tests/` package, `test_*.py`
  prefix — INTEGRATION §3). `ExportSQLTestCase` already errors on core 6.1 (red pre-fix).
  The patch MUST include this file: `run-verify.sh` identifies the test to run by the
  `test_*.py` file present in the patch. The current `test_export_sql` body has **no
  assertion** (it merely calls `importSQL`); strengthen it into a genuine round-trip
  regression (e.g. assert the re-imported person count / a known person's identity equals
  the exported source). It must exercise the PRODUCTION path — it already calls
  `exportData`/`importData` directly (no parallel copy), per `docs/principles.md` §3.4.
  **GTK pinning is NOT Do's concern:** the edit is the round-trip assertion only — do not
  add/duplicate a `gi.require_version` block. Pinning is handled by the testbed runner's
  `gi_bootstrap` shim (how C4 verifies) and, centrally upstream, by the repo-root
  `tests/__init__.py` GTK/GDK-3.0 pin (commit `2e4ced9a2`, now on both maintenance
  branches) — which fires when the addon's unit tests are executed through the root (the
  path a forthcoming `make.py <Addon>` runner will formalize for a single addon).
- **Citations expected:** Do must cite path:line on the target branch for every change
  (`ExportSql.py:684`, `ImportSql.py:705`). Root-cause core reference: `gramps/gen/lib/
  person.py` `serialize()` field #21 added by commit `4972a2eb4e` on
  `maintenance/gramps61`.
- **New/removed files:** N/A — addon fix; modifies existing `.py` (`ExportSql.py`,
  `ImportSql.py`) plus the existing test. Adds/removes no core `.py`, so no
  `po/POTFILES.{in,skip}` change (that MUST is core-only).
- **Prior-art check (triage cycles):** searched by file path. Merged history —
  `git -C ../addons-source log upstream/maintenance/gramps6{0,1} -- Sqlite/ExportSql.py
  Sqlite/ImportSql.py`: identical on both branches, no 6.1 person-serialize fix. Open/closed
  PRs — `gramps-project/addons-source` + `eduralph/addons-source`: PR 832 "Update
  unittests for 6.1" touched the addon tests but not the export arity; no PR addresses the
  `familysearch_sync` 22-field break. Result: **no prior art; clear to fix.**
- **Mantis:** none — fork issue eduralph/addons-source #47 (upstream
  gramps-project/addons-source has GitHub issues disabled, so it is tracked on the fork per
  INTEGRATION §1). The T4 `Fixes/Bug #id` trailer MUST is waived; the PR body states the
  origin in plain text.
- **Disposition hint:** likely-fix

## Verification note (NEEDS-HUMAN — surfaced, not decided)

The defect is **core-6.1-only**; the addon code is byte-identical across gramps60/gramps61
and a version-tolerant fix is a no-op behaviourally on 6.0. Two consequences the human/Check
must weigh:

1. **C4-verify runs the addon matrix on BOTH cores and requires per-leg red→green**
   (`engine/scripts/ubuntu/run-verify.sh:99,172`). On the **6.1 leg** the contract holds
   cleanly: reverting the production fix re-raises the `ValueError`, so red-without-fix /
   green-with-fix both pass. On the **6.0 leg** the test is green-with-fix but there is **no
   pre-existing defect**, so its "red-without-fix" half is not satisfiable — the
   gramps60×6.0 leg is a *no-regression* check, not a red→green one. The meaningful
   red→green evidence is the 6.1 leg (and the `T3-addon-unit-61` matrix gate that surfaced
   this). Confirm this framing rather than treating the 6.0-leg red-without-fix=FAIL as a
   bundle failure.

2. **Branch target** is therefore a judgment call (INTEGRATION §4 "ambiguous branch-target
   choice"): the default addon path is gramps60 → cherry-pick to gramps61 (keeps both
   branches' code identical, as they are today). Direct-to-gramps61 is defensible since
   that is the only affected core. Brief defaults to **maintenance/gramps60**; the
   maintainer's preference overrides.

3. **Cherry-pick gramps60 → gramps61 (verified).** `ExportSql.py` and `ImportSql.py` are
   **byte-identical** across the two branches, so the production hunks apply mechanically
   clean. Correctness on gramps61 holds *only because the fix is version-tolerant* (the
   same property the Invariant requires and that the gramps60×6.0 leg enforces) — a
   hardcode-to-22 fix would break the 6.0 leg and must not be what is picked forward. The
   `tests/test_sqlite.py` files still differ at the **top** (gramps61 has an inline
   GTK-3.0 pin block, gramps60 does not — now redundant with the upstream repo-root
   `tests/__init__.py` pin and the runner's `gi_bootstrap` shim), so confine the test edit
   to the round-trip assertion in `setUp`/`test_export_sql` (bottom of file) — away from
   that region — and both the production and test hunks cherry-pick clean.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Rejected on unverified red→green, NOT on the patch. The diff is sound and in-scope (C1/C2/C3/C5 PASS): export `*_,` unpack + import `data += Person().serialize()[len(data):]` pad are minimal, symmetric and version-tolerant. Do NOT re-engineer the fix. The C4 gating-fail and T3 addon-unit DELTAs are a PRE-EXISTING HARNESS BUG, not the patch: both the 6.0 and 6.1 addon-unit runner logs die with a shell syntax error "-c: line 142: unexpected EOF while looking for matching `)'" — the per-addon loop body runs inside a single-quoted `bash -c '…'` string and a stray apostrophe/paren broke the quoting, so bash exited 2 before running a single test. Zero tests ran → no JUnit → t3_baseline reports "no parsed failures / new failure mode." The same exit-2 signature appears in issue_46, confirming it is not specific to this fix. Next attempt: re-run Check only after the engine/* addon-unit runner quoting bug is fixed out-of-band (tracked as an Act candidate / separate GitHub issue+PR). The Sqlite round-trip regression test was never actually executed, so the red→green claim is simply unsubstantiated, not disproven. §6 unchanged: T1 (__init__.py flag — likely false-positive on Sqlite/tests/__init__.py, but the dead runner gives no signal), T5 (branch target), and V (fitness-to-purpose) all remain unresolved because nothing ran.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — ./engine/scripts/ubuntu/run-verify.sh
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ Sqlite: addon dir has __init__.py — breaks plugin loading (doc16-addon §Structure, Mantis 12691)
- Failing gate: T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer) (advisory) — T2 ⚠ ImportSql.py:897 candidate diagnostic print() — reviewer to confirm it is not intentional output (AGENTS.md §Loggin
- Failing gate: T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix) (advisory) — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- Failing gate: T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest) — raw runner o
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
