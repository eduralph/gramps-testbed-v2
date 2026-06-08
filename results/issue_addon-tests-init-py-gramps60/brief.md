# Brief — issue addon-tests-init-py-gramps60 / addons-source #43

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Tracks addons-source fork issue #43 (no Mantis — non-Mantis→fork-issue convention).
> Surfaced from gramps-testbed-v2 #8 task 2.

- **Slug:** addon-tests-init-py-gramps60
- **Defect:** On `addons-source` `maintenance/gramps60`, four addons have a `tests/`
  directory containing `test_*.py` files but **no `tests/__init__.py`** package marker —
  `CalculateEstimatedDates`, `DataEntryGramplet`, `Form`, `TMGimporter`.
  `maintenance/gramps61` already carries `__init__.py` for all of them (23/23), so this
  is a **gramps60-only parity gap** (gramps60 has 18 markers for 22 test dirs). Without
  the marker the `tests/` dir is not a proper Python package, so the addon-unit loader's
  dotted-path discovery (`<Addon>.tests.<module>`) can silently skip the suite.
- **Success criterion:** every addon `tests/` directory on `maintenance/gramps60`
  contains an `__init__.py` (parity with gramps61), and the four addons' suites are
  discovered and run by `run-addon-unit.sh CORE_VERSION=6.0` (they execute, not skipped).
- **Invariant to restore:** an addon test directory is a proper Python **package** — it
  carries `__init__.py` — so its suite is importable/discoverable via the dotted path
  `<Addon>.tests.<module>`. Stated over the category (every addon test dir), not one
  addon. Source: doc 16 §Testing (addon test-packaging convention) + `docs/INTEGRATION.md`
  §3 ("addon = `tests/` package with `__init__.py`"); internal/project invariant (Tier C,
  `docs/principles.md` §5). SELF-TEST: could Do satisfy this by guarding one module? No —
  it is a structural parity rule across all gramps60 addon test dirs.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
  — the gap is **gramps60-only**; `maintenance/gramps61` already conforms — **do NOT
  touch gramps61** (the maintainer's cherry-pick-forward would no-op there).
- **Scope:** add the missing `tests/__init__.py` package markers for the four gramps60
  addons listed (empty markers, matching the gramps61 ones). / out of scope: gramps61
  (already conforms); moving `gi.require_version` pins *into* `__init__.py` (addons #38);
  any test-logic or production change.
- **Repro instruction:** on `addons-source` `maintenance/gramps60`:
  `comm -23 <(git ls-files '*/tests/test_*.py' | sed -E 's#/tests/.*#/tests/#' | sort -u)
  <(git ls-files '*/tests/__init__.py' | sed 's#__init__.py$##' | sort -u)` lists the four
  dirs above. `./engine/scripts/ubuntu/run-addon-unit.sh` with `CORE_VERSION=6.0` does not
  discover those four suites.
- **Test file:** no new `test_*.py` ships — this is a **structural/discovery** fix; the
  change is the four `tests/__init__.py` markers. Verify by discovery, not C4-verify:
  `CORE_VERSION=6.0 ./engine/scripts/ubuntu/run-addon-unit.sh` now runs e.g.
  `CalculateEstimatedDates.tests.test_calculate_estimated_dates` (red/skipped pre-fix →
  discovered/green post-fix). NOTE: the per-fix **C4-verify addon matrix is not the gate
  here** — it requires a shipped `test_*.py` and applies the patch to BOTH cores, but
  these files already exist on gramps61 so the 6.1 leg would fail to apply. Gate on
  `T3-addon-unit-60` (gramps60 leg only).
- **Citations expected:** Do cites the four created paths
  (`<Addon>/tests/__init__.py`) on `maintenance/gramps60`.
- **Prior-art check (triage cycles):** gramps61 already has all 23 `tests/__init__.py`
  (the reference). Related open item: addons-source #38 (move `require_version` pins into
  `tests/__init__.py` — assumes they exist). Prior fork branch `ci-validate/931-init-py`
  ("Add __init__.py to all unittest folders"). No Mantis ticket. No existing PR for the
  gramps60 gap.
- **Disposition hint:** likely-fix (structural parity; low risk — empty package markers,
  no code change).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
