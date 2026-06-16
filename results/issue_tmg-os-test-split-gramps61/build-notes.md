# Build notes — tmg-os-test-split-gramps61 (addons-source #48)

## What the brief asked for

Port the already-merged gramps60 OS-test split forward to
`maintenance/gramps61`. End state (Success criterion + Invariant): `TMGimporter/tests/`
on gramps61 must be **structurally identical** to gramps60's post-split layout —
`test_libtmg.py` holds only the OS-portable pure-function tests, and a new
`test_linux_libtmg.py` holds the DB-backed tests + shared helpers (Linux-only by the
`test_linux_*` filename convention). The brief pins the exact end state: the two
resulting files must match gramps60 blobs `4851746a` (`test_libtmg.py`) and `35bd117`
(`test_linux_libtmg.py`).

The maintainer's `git cherry-pick` of the split commit failed because gramps61's
`test_libtmg.py` had independently diverged with two stopgaps in exactly the regions the
split rewrites:
- an inline `gi.require_version("Gtk"/"Gdk", "3.0")` pin block at the top
  (gramps61 `test_libtmg.py:16-29`), and
- a `sys.platform == "win32"` `SkipTest` inside `_make_db()`
  (gramps61 `test_libtmg.py:80-85`).

## Root cause / why this is the right shape

This is an **Invariant to restore**, not a cost-vs-minimalism call. The invariant is:
an addon's OS-environment-dependent tests are separated from its portable ones by file
*placement* (`test_<os>_*`), so a test a lane can't run is *not in a file that lane
executes* — rather than guarded at runtime inside a portable file. gramps61 violated it
by keeping the DB-backed tests (which hang on the Windows CI lane against a mismatched
conda-forge Gramps, addons-source #32) in `test_libtmg.py` and papering over the symptom
with a runtime `win32` skip. The smallest change that restores the invariant is the
gramps60 split itself: move the cause (DB tests in a Windows-run file), don't guard the
symptom. The SELF-TEST in the brief is explicit — guarding one module is *not*
acceptable; correct file placement is.

## Verification that this is a verbatim relocation, not a silent swap

The brief mandates the result equal the gramps60 blobs, but I first confirmed gramps61's
test *logic* is byte-identical to gramps60's so that adopting the gramps60 blobs is a
true verbatim relocation of gramps61's own tests (not importing different assertions).

AST comparison (`/tmp/cmp.py`) of every top-level class/function:
- gramps61 `test_libtmg.py` (single file) vs gramps60 `test_libtmg.py` ∪
  `test_linux_libtmg.py`: **identical name set, zero body mismatches except `_make_db`.**
- The sole `_make_db` difference is precisely the `win32` `SkipTest` stopgap gramps60's
  split removed (gramps61 `test_libtmg.py:68-90` vs gramps60 `test_linux_libtmg.py:60-64`).

So the 13 DB-backed classes (TestImportNotes, TestTrialEvents, TestImportSources,
TestImportPlaces, TestLinkEventPlaces, TestImportPeople, TestLinkPersonEvents,
TestImportFamilies, TestImportRepositories, TestImportCitations, TestShortPlaceName,
TestTagTypeName) + helpers (`_Rec`, `_table`, `_make_db`, `_add_person`) and the
`Event, NoteType, Person, Place, Source` / `make_database` / `DbTxn` imports move
**verbatim** into `test_linux_libtmg.py`; the pure-function classes and the reduced
`from gramps.gen.lib import Date` import stay in `test_libtmg.py`. The two stopgaps
(inline pin, `win32` skip) vanish as a consequence, exactly as on gramps60.

## The change (cited on `maintenance/gramps61`)

`patch.diff` (git diff --staged, applies cleanly to clean
`upstream/maintenance/gramps61` — verified `git apply --check` → "APPLIES CLEANLY"):

- **`TMGimporter/tests/test_libtmg.py`** (modified): removed the inline `gi.require_version`
  pin block (`test_libtmg.py:11-29` region), the DB-backed imports (`:35-37`), the shared
  helpers incl. the `win32`-guarded `_make_db` (`:45-100`), and all 13 DB-backed classes
  (interleaved `:218-1437`). Result = gramps60 blob `4851746a` (`git hash-object` →
  `4851746a624121f99949105c5af81c642e0c56da` ✓).
- **`TMGimporter/tests/test_linux_libtmg.py`** (new file): the Linux-only module with the
  docstring documenting the `test_*.py` / `test_linux_*.py` / `test_windows_*.py` /
  `test_integration_*.py` convention, the moved helpers and 13 DB-backed classes. Result
  = gramps60 blob `35bd117` (`git hash-object` →
  `35bd117175815c810bb9eac7fb59d95c4e457f10` ✓).

gramps60 (`maintenance/gramps60`) is **untouched** — it already carries the split.

## Tests / files registration

No new `test_*.py` is authored — the deliverable *is* the two test files (per brief
"Test file" and "New/removed files"). TMGimporter ships **no `po/POTFILES.*`** on either
branch (confirmed: `git ls-tree -r upstream/maintenance/gramps61 TMGimporter/` has no
POTFILES), and gramps60's merged split registered the new file in none — so **no POTFILES
action**, matching gramps60. `tests/__init__.py` is the empty blob `e69de29` on both
branches; this PR neither adds nor reinstates an addon-level GTK pin (that is
addons-source #38's repo-wide rollout, out of scope).

## How I verified red→green / per-OS behaviour

The brief directs verification by per-OS behaviour via
`CORE_VERSION=6.1 ./engine/scripts/ubuntu/run-addon-unit.sh`, **not** a fresh regression
test — and explicitly *not* `run-verify.sh`.

`run-verify.sh` structurally **cannot** gate this bundle: it requires the patch to ship
exactly one test file *and* at least one non-test production file to revert for the red
pass (`run-verify.sh:128-130` — `PROD` must be non-empty). Here both changed files have
basename `test_*.py`, so `PROD` is empty and the script exits 1 with "patch has no
production change to revert". This is expected for a data/test-infrastructure surface;
Check's per-OS run (`run-addon-unit.sh`) is the authoritative green check.

Static red→green evidence (with the patch applied to a clean
`upstream/maintenance/gramps61` checkout):
- **RED (pre-fix):** `grep -c "class TestImportNotes\|win32\|require_version"
  test_libtmg.py` = 3+ — the DB-backed classes, the `win32` skip and the GTK pin all
  ride in `test_libtmg.py`, the file the Windows lane executes (the defect).
- **GREEN (post-fix):** same grep on `test_libtmg.py` = **0**; the DB classes + `_make_db`
  now live only in `test_linux_libtmg.py` (`grep -c "class TestImportNotes\|def _make_db"`
  = 2). `run-addon-unit.sh` includes `test_linux_*` on the Linux lane (only
  `test_windows_*` is excluded — `run-addon-unit.sh:241-243`), so the Linux lane discovers
  and runs **both** modules; the addons-source GitHub Windows lane excludes `test_linux_*`
  by the convention proven green on gramps60.
- `python3 -m py_compile` passes on both files.
- Both files are byte-identical to the **already-merged, already-green** gramps60 blobs
  (157 pass on Linux, 95 of them the real-DB classes, per the brief), and the matching
  core (`../gramps` = 6.1.0) is the same DB API surface — so the per-OS behaviour is
  guaranteed equivalent to gramps60's merged result.

**Runner caveat:** the Docker-backed engine runners (`run-addon-unit.sh`,
`run-verify.sh`) require interactive approval that the headless builder session cannot
grant, so I could not execute the containerised suite here. The evidence above (exact
blob match to the merged-green gramps60 files + AST verbatim-equivalence + clean apply +
structural grep) establishes correctness; Check re-runs `run-addon-unit.sh` as the
authoritative gate.

## Commit-readiness

Content is byte-identical to files already merged on `maintenance/gramps60`, which passed
that branch's hooks; no formatting (black) drift is possible. The patch applies cleanly
to clean `upstream/maintenance/gramps61`.

## Alternatives ruled out

- **Migrate the GTK `require_version` pin into `tests/__init__.py`** instead of dropping
  it — out of scope: that is addons-source #38's coordinated repo-wide rollout. gramps60's
  split simply removed the pin (the gi_bootstrap sitecustomize the runner puts on
  PYTHONPATH already pins GI), and the invariant is restored by placement, not pinning.
- **Keep the `win32` runtime skip in a single combined file** — this is the rejected
  symptom-guard the brief's SELF-TEST forbids; it leaves DB tests in a Windows-run file
  and violates the invariant. Cost is not the axis; correctness of placement is.
