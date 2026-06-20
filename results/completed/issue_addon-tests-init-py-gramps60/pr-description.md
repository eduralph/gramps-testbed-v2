# Add missing tests/__init__.py markers to four gramps60 addons

## Root cause
On `maintenance/gramps60`, four addons ship a `tests/` directory with
`test_*.py` files but no `tests/__init__.py` package marker, so those
directories are not proper Python packages. `maintenance/gramps61` already
carries the marker for all of its addon test directories (23/23), making this a
gramps60-only parity gap (gramps60 had 18 markers for 22 test directories).

## Fix
Add an empty `tests/__init__.py` to each of the four addons that lacked one, so
every addon test directory on `maintenance/gramps60` is an importable package,
discoverable via the dotted path `<Addon>.tests.<module>` (parity with the empty
markers already present on `maintenance/gramps61`):

- `CalculateEstimatedDates/tests/__init__.py`
- `DataEntryGramplet/tests/__init__.py`
- `Form/tests/__init__.py`
- `TMGimporter/tests/__init__.py`

This brings `maintenance/gramps60` to 22/22 markers. The change is gramps60-only;
`maintenance/gramps61` already conforms and is untouched, so the maintainer's
cherry-pick-forward is a no-op there. This is the gramps60 counterpart to the
sister cleanup in https://github.com/gramps-project/addons-source/pull/931 ("Add
__init__.py to all unittest folders").

## Verified against
- `CalculateEstimatedDates/tests/__init__.py`, `DataEntryGramplet/tests/__init__.py`,
  `Form/tests/__init__.py`, `TMGimporter/tests/__init__.py` (new, empty) on
  `maintenance/gramps60` — the four directories reported by the gap check below.
- Gap check on `maintenance/gramps60` (`LC_ALL=C`): pre-fix lists exactly these four
  directories, post-fix lists none (markers 18/22 → 22/22):
  ```
  comm -23 \
    <(git ls-files '*/tests/test_*.py' | sed -E 's#/tests/.*#/tests/#' | sort -u) \
    <(git ls-files '*/tests/__init__.py' | sed 's#__init__.py$##' | sort -u)
  ```
- `maintenance/gramps61` reference — all addon test directories already carry an
  empty `tests/__init__.py` (23/23); the four new files match those byte-for-byte
  (0 bytes).
- `git apply --check`: applies cleanly on gramps60; fails on gramps61 (files
  already exist), confirming the change is gramps60-only.

## Test
No new `test_*.py` ships — this is a structural packaging fix, not a logic change.
The red→green proof is the gap check above (four missing → none). Discovery under
`CORE_VERSION=6.0 run-addon-unit.sh` runs the four suites (244 tests, OK); the
markers pin each `tests/` as a real package so the suite cannot be silently
re-resolved as a namespace package on a colliding `sys.path`.
