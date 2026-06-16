# Brief — issue tmg-os-test-split-gramps61 / addons-source #48

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Tracks addons-source fork issue #48 (no Mantis — non-Mantis→fork-issue convention).
> Surfaced from @GaryGriffin's feedback on the merged upstream split PR: the cherry-pick
> forward to gramps61 failed; a gramps61-targeted PR is needed.

- **Slug:** tmg-os-test-split-gramps61
- **Defect:** On `addons-source` `maintenance/gramps61`, `TMGimporter/tests/test_libtmg.py`
  is still a **single file** carrying the 13 real-DB import test classes alongside the
  pure-function tests. On the Windows CI lane those DB-backed tests run against a
  mismatched Gramps (conda-forge has no 6.1, resolves to 6.0.8) and **hang** (addons-source
  #32). The upstream split PR fixed this on `maintenance/gramps60` by moving the DB-backed
  tests into `test_linux_libtmg.py` (Linux-only via the `test_linux_*` filename
  convention), but the maintainer's cherry-pick of that split forward to gramps61
  **failed**: gramps61's `test_libtmg.py` independently diverged with two stopgaps — an
  inline `gi.require_version` GTK/Gdk pin block at the top and a `sys.platform == "win32"`
  `SkipTest` inside the shared `_make_db()` helper — in exactly the regions the split
  rewrites, so the patch context no longer matches.
- **Success criterion:** `TMGimporter/tests/` on `maintenance/gramps61` is structurally
  identical to `maintenance/gramps60` after the split — `test_libtmg.py` holds only the
  pure-function tests (every OS) and a new `test_linux_libtmg.py` holds the DB-backed
  tests + shared helpers (Linux-only). Under `run-addon-unit.sh CORE_VERSION=6.1` the
  Linux lane discovers and runs **both** files green against the matching gramps 6.1; the
  DB-backed tests no longer ride in a file the Windows lane runs.
- **Invariant to restore:** an addon's OS-environment-dependent tests are separated from
  its portable ones by the `test_<os>_*` filename convention, so a test that cannot run
  on a lane's environment is *not placed in a file that lane executes* — rather than being
  guarded at runtime inside an OS-portable file. Stated over the category (the addon's
  whole `tests/` dir, both branches' mechanism converged), not one helper. Source:
  the `test_linux_*` / `test_windows_*` convention codified in `run-addon-unit.sh`
  (`engine/scripts/ubuntu/run-addon-unit.sh:235-247`) and gramps60's merged
  `test_linux_libtmg.py` docstring; project/test-placement convention (`docs/INTEGRATION.md`
  §"Test placement", Tier C, `docs/principles.md` §5). SELF-TEST: could Do satisfy this by
  guarding one module? No — it removes a runtime OS-guard in favour of correct file
  placement, the same shape the upstream split established on gramps60.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps61
  — the gap is **gramps61-only**; `maintenance/gramps60` already carries the split.
  **Do NOT touch gramps60.**
- **Surfaces:** data (test-infrastructure / no production code change).
- **Scope:** converge gramps61's `TMGimporter/tests/` onto gramps60's post-split layout —
  move the DB-backed test classes + shared helpers (`_Rec`, `_table`, `_make_db`,
  `_add_person`) and their imports out of `test_libtmg.py` into a new
  `test_linux_libtmg.py`, leaving `test_libtmg.py` with the pure-function tests and the
  reduced `from gramps.gen.lib import Date` import. As a consequence the two gramps61-only
  stopgaps disappear: the inline `gi.require_version` pin block and the `win32` `SkipTest`
  in `_make_db()`. The two resulting files must match gramps60 blobs `4851746a`
  (`test_libtmg.py`) and `35bd117` (`test_linux_libtmg.py`).
  / **out of scope:** gramps60 (already split); migrating the GTK pin *into*
  `TMGimporter/tests/__init__.py` (that is addons-source #38's coordinated repo-wide
  rollout — this PR neither adds nor reinstates an addon-level pin); closing addons-source
  #32 (the Windows real-DB coverage gap stays open until gramps 6.1 reaches conda-forge);
  any libtmg production change or test-logic change.
- **Repro instruction:** on `addons-source` `maintenance/gramps61`:
  `git show maintenance/gramps61:TMGimporter/tests/test_libtmg.py | grep -n "require_version\|win32\|class TestImportNotes"`
  shows the inline pin block, the `win32` skip, and the DB-backed classes still co-located.
  Compare to `maintenance/gramps60`, which has both `test_libtmg.py` (pure-function only)
  and `test_linux_libtmg.py`. A `git cherry-pick` of the split's commit onto gramps61
  conflicts in `test_libtmg.py`.
- **Test file:** no new `test_*.py` is authored — the deliverable **is** the two test
  files, and they carry the same assertions already proven on gramps60 (157 pass on Linux,
  95 of them the real-DB classes). Verify by per-OS behaviour, not a fresh regression test:
  `CORE_VERSION=6.1 ./engine/scripts/ubuntu/run-addon-unit.sh` discovers and runs
  `TMGimporter.tests.test_libtmg` **and** `TMGimporter.tests.test_linux_libtmg` green on
  Linux; the DB-backed classes now reside only in `test_linux_libtmg.py`, which the Windows
  lane excludes by the `test_linux_*` convention (the mechanism proven green on gramps60).
  PRODUCTION-PATH: the moved classes drive the real `libtmg.import_notes` / `make_database`
  path unchanged — they are relocated verbatim, not reimplemented.
- **Citations expected:** Do cites, on `maintenance/gramps61`, the lines removed from
  `TMGimporter/tests/test_libtmg.py` (the inline pin block, the `win32` skip, the moved
  classes/helpers/imports) and the lines created in `TMGimporter/tests/test_linux_libtmg.py`,
  and confirms each resulting file matches the named gramps60 blob.
- **New/removed files:** adds `TMGimporter/tests/test_linux_libtmg.py` (a test file, no
  translatable strings). TMGimporter ships **no `po/POTFILES.*`** on either branch, and
  gramps60's merged split registered the new file in none — so there is **no POTFILES
  action** here; match gramps60 (no registration). `test_libtmg.py` is modified, not
  added/removed.
- **Prior-art check (triage cycles):** gramps60 already carries the split (merged
  upstream — the reference). Related fork issues: addons-source #32 (Windows real-DB
  coverage — this is its gramps61 mechanism arm, but does not close it) and addons-source
  #38 (move `require_version` pins into addon `tests/__init__.py` — owns the pin placement
  this PR defers to). No Mantis ticket (originated from the upstream split PR's review
  feedback). No existing PR for the gramps61 split.
- **Disposition hint:** likely-fix (port of an already-merged, already-green split; low
  risk — relocates verbatim test code and removes two superseded stopgaps).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
