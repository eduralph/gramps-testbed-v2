# Build notes — sqlite-export-person-serialize-6.1 (iteration 2)

## Summary of this iteration

The iteration-1 patch was **rejected on unverified red→green, not on the diff**
(carry-forward, brief.md:137). This iteration keeps the same production fix and test
(the carry-forward explicitly said "Do NOT re-engineer the fix") and **substantiates
the red→green claim that v1 could never run** — by finding and fixing the actual
harness defect that aborted the C4 runner, then running `run-verify.sh` to green.

The v1 carry-forward blamed the failure on the `run-addon-unit.sh` line-142 single-
quote/EOF bug (testbed #127). That bug is now **already fixed** (the runner carries a
warning comment at `engine/scripts/ubuntu/run-addon-unit.sh:281-284` documenting the
fix). It is also the **T3 advisory** runner, not the **C4 gating** runner. The real
C4 blocker was a *different, undiagnosed* harness bug — see "Harness fix required"
below.

## Root cause of the addon defect (verified against source)

Core 6.1 added a 22nd field to `Person.serialize()`/`unserialize()` —
`familysearch_sync` at index 21 — via the `FamilySearchSyncBase` mixin (commit
`4972a2eb4e` on `maintenance/gramps61`; `gramps/gen/lib/person.py` serialize/
unserialize). Core 6.0's Person is 21 fields.

The Sqlite addon hardcodes a fixed 21-tuple in two places on the shared (byte-identical
across `maintenance/gramps60` and `maintenance/gramps61`) source:

- **Export** `Sqlite/ExportSql.py:684-705` — `export_person` positionally unpacks
  exactly 21 names from `person.serialize()`. On core 6.1 that is a 22-tuple →
  `ValueError: too many values to unpack (expected 21)`. This is the crash the brief's
  repro hits in `setUp` (`exportSQL(...)`), **before** import is reached.
- **Import** `Sqlite/ImportSql.py:705-726` — `_process` builds a 21-tuple and feeds it
  to `Person.unserialize(data)`. On core 6.1 `unserialize` positionally unpacks 22 →
  it would raise `not enough values to unpack (expected 22, got 21)`. Import never ran
  in the repro only because export crashed first; the round-trip invariant requires
  both halves fixed.

## Fix (version-tolerant — the Invariant the brief names)

The Invariant: the addon's Person export/import must agree with the *targeted* core's
serialize field-set, on **both** 6.0 (21) and 6.1 (22) from one shared source. So the
fix must tolerate either arity, not hardcode 22 (a hardcode-to-22 would break the
gramps60×6.0 leg and would be wrong to cherry-pick forward).

- **Export** (`Sqlite/ExportSql.py:705`, new line): add `*_,  # 21+` to the unpack
  tail. `(... person_ref_list, *_,) = person` absorbs any fields past index 20 into a
  throwaway. On 6.0 `_` is `[]`; on 6.1 it is `[familysearch_sync_serialized]`. The
  export only persists handle/gid/gender/refs/change/private (the addon's `person`
  table columns — `ExportSql.py:159-167`), so dropping the extra is faithful to what
  the schema represents (brief Scope (b): persisting `familysearch_sync` is a separate
  enhancement).
- **Import** (`Sqlite/ImportSql.py:726`, after the 21-tuple): append the core's own
  defaults for any fields beyond index 20 — `data += Person().serialize()[len(data):]`.
  `len(data)` is 21. On 6.0 `Person().serialize()` is 21 → slice empty → no-op. On 6.1
  it is 22 → appends the default `familysearch_sync.serialize()`, which
  `Person.unserialize` passes to its setter. Using core's own default tuple means the
  addon never has to know the field's shape — it stays correct if core adds further
  Person fields, with no blanket arity refactor.

`Person` is already imported (`Sqlite/ImportSql.py:46`), so no new import.

### Why not the alternatives (with cost)

- **Hardcode the 22nd field** (`familysearch_sync` by name in both spots): wrong by the
  Invariant — it breaks the gramps60×6.0 leg (`ValueError: not enough values, expected
  22, got 21` on a 21-field Person) and is exactly the change that must NOT cherry-pick
  forward. Rejected on **correctness**, not cost.
- **Blanket "derive every object's tuple arity dynamically" refactor**: out of scope
  (brief Scope (c)). Verified across `gramps/gen/lib/` that **only Person** gained a
  serialize field in 6.1. The alternative would touch every primary object's
  export/import pair — Export `export_{person,family,event,place,source,citation,
  repository,media,note}` (9 unpacks) plus the 9 matching `_process` tuples in Import =
  ~18 hunks — for zero behavioural gain over the 2-line Person-scoped fix.

## Test (`Sqlite/tests/test_sqlite.py`)

The pre-existing `test_export_sql` body called `importSQL` with **no assertion** — it
only caught the bug via the `setUp` crash. Strengthened into a genuine round-trip
regression that drives the production path already present (`exportSQL`/`importSQL`
directly — no parallel copy, principles §3.4): assert the SQL re-import (`database2`)
reproduces the people exported from the source XML tree (`database1`) — equal
`get_number_of_people()` and, per source handle, equal gramps_id / gender / primary
first-name / surname. The assertions run *after* the round-trip, so on a regression the
arity break surfaces as a test failure, not only a `setUp` error.

GTK pinning left to the runner's `gi_bootstrap` shim + upstream root `tests/__init__.py`
pin, per the brief — no `gi.require_version` block added, and the edit stays at the
bottom of the file, away from the gramps61-only inline pin block, so the cherry-pick to
gramps61 stays clean (verified: `git apply --check` clean on both branches).

## Verification — red→green via the engine runner (now that it runs)

`PDCA_BUNDLE=… ./engine/scripts/ubuntu/run-verify.sh` (saved verbatim, progress spam
stripped, in `c4-verify.log`):

- **gramps61 × core 6.1.0** (the defect / red→green leg):
  `green-with-fix=PASS / red-without-fix=PASS`. Green = `Ran 1 test … OK`; red (prod
  reverted, test kept) = `ERROR … ValueError: too many values to unpack (expected 21)`
  → `FAILED (errors=1)`. **Genuine red→green.**
- **gramps60 × core 6.0.8** (no-regression leg): `green-with-fix=PASS /
  red-without-fix=FAIL`. As the brief's Verification note 1 states, the 6.0 leg has
  **no pre-existing defect**, so its red-without-fix half is structurally
  unsatisfiable; green-with-fix confirms no regression. The leg's overall non-zero exit
  is expected and is NOT a bundle failure — confirm this framing at sign-off.

`git apply --check --whitespace=error` of `patch.diff` is clean on **both**
`addons-source-6.0` (target) and `addons-source-6.1` (cherry-pick target).

## Harness fix required (engine/* — out of bundle scope, NOT in patch.diff)

The reason v1's C4 "never ran" is a harness bug I had to fix to verify this bundle:

- `engine/scripts/ubuntu/run-verify.sh:93-95` `_parse_fork_ref()` is a
  `grep | head | sed` pipeline. For an addon brief with **no** `Verification base:`
  field (the normal matrix path — this brief included), `grep` exits 1; under the
  script's `set -euo pipefail` the pipeline returns non-zero, and line 110
  (`[ "$MODE" = addon ] && FORK_REF="$(_parse_fork_ref …)"`) — the command after the
  final `&&`, so `set -e` applies — **aborts the whole runner with exit 1 before a
  single test runs**. Introduced in commit `e885299` ("Verify an addon bundle against a
  fork's PR branch"). This is the true C4 blocker (the v1 carry-forward mis-attributed
  it to the already-fixed run-addon-unit.sh #127 quoting bug).
- **Minimal fix applied** to my working tree so C4 could run: append `|| true` to the
  `_parse_fork_ref` pipeline (one line). This is an `engine/*` change — per project
  rules (`CLAUDE.md`, MEMORY: engine changes are not PDCA bundles) it is **not** part
  of this bundle's `patch.diff`; it must be landed out-of-band as a separate
  gramps-testbed-v2 issue + PR. **It is currently uncommitted in the working tree**, so
  Check's C4 re-run will see it and pass; if it is reverted, C4 will abort again with
  the same silent exit-1. Please land it.

No `po/POTFILES.{in,skip}` change: addon fix, no core `.py` added/removed.

## NEEDS-HUMAN (surfaced, not decided)

- **Branch target** is `maintenance/gramps60` per the brief default; production hunks
  are byte-identical across gramps60/gramps61 so the cherry-pick is mechanical and is
  *correct* on gramps61 only because the fix is version-tolerant (the 6.1 C4 leg proves
  it). Confirm the branch-target judgment call (brief Verification note 2).
- **6.0-leg red-without-fix=FAIL** is the expected no-regression signal, not a failure
  (brief Verification note 1).
- **Engine harness fix** above must be landed out-of-band for C4 to keep running.
