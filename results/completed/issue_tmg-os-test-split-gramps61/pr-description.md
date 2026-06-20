# Move DB-backed TMGimporter tests into a Linux-only test module

No Mantis ticket — surfaced from review feedback on upstream PR 949, the split
that fixed the Windows unit-test hang (the issue described in that PR) on
`maintenance/gramps60` but whose cherry-pick forward to `maintenance/gramps61`
failed. Targets `gramps-project/addons-source` @ `maintenance/gramps61`.

## Root cause

On `maintenance/gramps61`, `TMGimporter/tests/test_libtmg.py` still held the 13
real-database import test classes alongside the pure-function tests; those
DB-backed tests hang on the Windows CI lane, which can only get a mismatched
Gramps (conda-forge has no 6.1), so the file papered over the symptom with an
inline `gi.require_version` GTK/Gdk pin block and a `win32` `SkipTest` inside
`_make_db()` instead of placing the unrunnable tests outside the files that
lane executes (the `test_<os>_*` convention).

## Fix

Split the suite so OS-environment-dependent tests are separated from portable
ones by file placement. The 13 DB-backed classes plus the shared helpers
(`_Rec`, `_table`, `_make_db`, `_add_person`) and their DB-layer imports move
verbatim into a new Linux-only `test_linux_libtmg.py`; `test_libtmg.py` keeps
the pure-function tests and a reduced `from gramps.gen.lib import Date`. The two
gramps61-only stopgaps (the inline pin block and the `win32` skip) drop out as a
consequence. This converges `maintenance/gramps61` onto the layout already
merged on `maintenance/gramps60`; gramps60 is untouched, and there is no
production-code or test-logic change.

## Verified against

- `TMGimporter/tests/test_libtmg.py:11-93` (gramps61) — the removed inline
  `gi.require_version` pin block, the DB-backed imports, the shared helpers
  including the `win32`-guarded `_make_db`, and the 13 DB-backed classes; the
  resulting file is byte-identical to the gramps60 `test_libtmg.py` blob
  (`git hash-object` → `4851746a624121f99949105c5af81c642e0c56da`).
- `TMGimporter/tests/test_linux_libtmg.py:1-17` (new) — the module docstring
  documenting the `test_*` / `test_linux_*` / `test_windows_*` /
  `test_integration_*` placement convention.
- `TMGimporter/tests/test_linux_libtmg.py:19-1218` (new) — the moved helpers
  and 13 DB-backed classes; the resulting file is byte-identical to the gramps60
  `test_linux_libtmg.py` blob (`git hash-object` →
  `35bd117175815c810bb9eac7fb59d95c4e457f10`).
- `engine/scripts/ubuntu/run-addon-unit.sh:241-243` — the Linux lane discovers
  `test_linux_*`; only `test_windows_*` is excluded, so both modules run on
  Linux against the matching Gramps 6.1.

## Test

No new `test_*.py` is authored — the deliverable *is* the two test files, which
carry the same assertions already proven green on `maintenance/gramps60` (157
pass on Linux, 95 of them the real-DB classes). An AST comparison confirmed
gramps61's test logic was byte-identical to gramps60's apart from the `win32`
stopgap, so adopting the gramps60 blobs is a true verbatim relocation rather
than a swap of assertions. Verification is per-OS behaviour, not a fresh
regression test: `CORE_VERSION=6.1 ./engine/scripts/ubuntu/run-addon-unit.sh`
discovers and runs both `TMGimporter.tests.test_libtmg` and
`TMGimporter.tests.test_linux_libtmg` green on Linux, with the DB-backed classes
now residing only in `test_linux_libtmg.py`, which the Windows lane excludes by
the `test_linux_*` convention proven green on gramps60. (`run-verify.sh` cannot
gate this bundle: it requires a non-test production file to revert, and this
data/test-infrastructure change ships only `test_*.py` files.)
