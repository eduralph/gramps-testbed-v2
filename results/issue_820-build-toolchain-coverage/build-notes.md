# Build notes — 820-build-toolchain-coverage (iteration 4)

Withheld from the reviewer. Rationale for the iteration-3 substance (carried
forward, accepted as sound at sign-off) plus iteration-4's single job: clear the
C4 blocker by actually running the dockerised `run-verify.sh` red→green now that
the fork worktree exists.

## Iteration 4 — what changed vs iteration 3

The fix code is **unchanged** from iteration 3 (the iteration-3 sign-off, brief.md:77,
said "The patch approach itself looks sound — this iterate is to get the bundle
verified, not to redesign the fix"). The only difference is that the
`addons-source-6.0-fork` lane worktrees are now provisioned, so the C4 gate the
prior three iterations never executed could finally run.

**C4 ran and passed — exit 0.** `PDCA_BUNDLE=… ./engine/scripts/ubuntu/run-verify.sh`
against the fork verification base (`origin/feature/ci-cd-pipeline-upstream`,
gramps60 → addons-source-6.0-fork) reports:

```
→ green check (fix applied):   Ran 11 tests … OK
→ red check (production reverted, test kept):   FAILED (failures=3, errors=5)
C4-verify: green-with-fix=PASS / red-without-fix=PASS
EXIT=0
```

The red leg's 5 errors are `AttributeError: MOD_BUILD_PACKAGES` (gone when the
production `addon_system_deps.py` change is reverted) and the `unmapped()` 2-tuple
unpack; the 3 failures are the apt/conda `packages()`+CLI assertions and
`test_toolchain_not_purged` on the restored `RUN apt-get purge -y gcc …` line. This
is the genuine C4 contract — the test catches exactly the defect the fix resolves.

**T3 Sqlite delta** (`Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq`,
flagged in iterations 1–3): this patch touches only `.github/` CI tooling and
`tests/test_addon_system_deps.py`. It changes **no** Sqlite addon code and no
runtime/import path any addon suite exercises, so it cannot cause that failure —
it is pre-existing baseline noise, confirmed unchanged across iterations where the
patch body for Sqlite was identical (i.e. empty).

## What iteration 3 changes vs iteration 2

Iteration 2's substance was accepted as sound and is **carried forward unchanged**:
- apt lane: drop the Dockerfile `apt-get purge` (keep gcc/python3-dev/pkg-config),
  derive `libgraphviz-dev`/`libpq-dev` from `.gpr.py` via `MOD_BUILD_PACKAGES`,
  install them before the runtime pip step.
- conda lane: map the source-built mods to their prebuilt conda-forge packages
  (NOT `None`), so the Windows lane provisions them via `mamba install` and the
  suites run instead of silently skipping. (C5(a) — pygraphviz/psycopg2 resolve on
  conda-forge — was verified at the iteration-2 sign-off and is not re-litigated.)

Iteration 3 adds three things, each tied to a specific iteration-2 carry-forward
item (brief.md:68-73):

### 1. Closed the C5(b) category gap — `psycopg` (psycopg3) was missing

The carry-forward asked me to "confirm `_SOURCE_BUILT_MODS` covers every
source-built `requires_mod` the addons actually declare (scan the `.gpr.py` set),
so a newly-added one cannot silently skip."

I scanned every `*/*.gpr.py` on the current fork head
(origin/feature/ci-cd-pipeline-upstream @ `4fc07ba61`). The full declared
`requires_mod` set is **9 modules**:

| module            | declaring addon(s)                | kind          |
|-------------------|-----------------------------------|---------------|
| boto3             | S3MediaUploader                   | wheel-only    |
| dbf               | TMGimporter                       | wheel-only    |
| life_line_chart   | LifeLineChartView                 | wheel-only    |
| litellm           | ChatWithTree, GrampsChat          | wheel-only    |
| networkx          | NetworkChart                      | wheel-only    |
| svgwrite          | LifeLineChartView                 | wheel-only    |
| pygraphviz        | NetworkChart                      | source-built  |
| psycopg2          | PostgreSQL, SharedPostgreSQL      | source-built  |
| **psycopg**       | **PostgreSQLEnhanced**            | **source-built** |

`psycopg` (psycopg3, declared by `PostgreSQLEnhanced/postgresqlenhanced.gpr.py:46`,
hard-imported at `PostgreSQLEnhanced/connection.py:38`) was **absent** from
iteration-2's `_SOURCE_BUILT_MODS = ("pygraphviz", "psycopg2")` and from
`MOD_BUILD_PACKAGES`. It is exactly the silent-skip the invariant forbids: a plain
`pip install psycopg` is pure-Python but **links libpq at import** — without the
system libpq, `import psycopg` fails at CI runtime, gets swallowed by
`|| echo … (continuing)`, and PostgreSQLEnhanced's coverage degrades silently.

Iteration 3 adds it on both lanes:
`"psycopg": {"apt": "libpq-dev", "conda": "psycopg"}` (addon_system_deps.py:88).
I verified `psycopg` resolves on conda-forge **win-64** (3.2.x) by downloading
`conda-forge/win-64/repodata.json` — same method the iteration-2 notes used for
pygraphviz/psycopg2 (re-confirmed here: pygraphviz ≤1.9 win-64, psycopg2 2.9.x
win-64). On apt, `libpq-dev` (which `psycopg2` already needs) provides libpq, so
the pure-Python `psycopg` import is satisfied with no extra cost.

### 2. Made the category guard *enforced in production*, not just declared

To honour "a newly-added one cannot silently skip," I extended the production
drift guard so a future unclassified `requires_mod` fails CI rather than slipping
through:
- `WHEEL_ONLY_MODS` (addon_system_deps.py) — an explicit allowlist of the six
  pure-Python wheels.
- `scan_modules()` + a third element in `unmapped()` — every declared
  `requires_mod` that is in **neither** `WHEEL_ONLY_MODS` **nor**
  `MOD_BUILD_PACKAGES` is reported as drift, and `--unmapped` exits 1 on it.
- ci.yml's existing "Validate addon system deps are mapped" step already runs
  `--unmapped .` and fails on a non-zero exit, so the gate now also catches a new
  unclassified module. Its error message is updated to mention `requires_mod`.

This is the smallest change that makes the invariant hold *over the category and
over the future*, not just for today's three modules. `unmapped()`'s only caller
is `main()` (confirmed by grep over the branch — `run_addon_tests.py` uses only
`addon_satisfiable_on`/`PLATFORMS`), so widening it to a 3-tuple is safe.

I deliberately did **not** touch `addon_satisfiable_on`: leaving it mod-unaware
keeps the honest-skip backstop strict — a future mod mapped to `None` on a lane
would all-skip and `run_addon_tests` reports that as a hard FAILURE (red), not a
silent green. That backstop ships out-of-band per brief.md:36-37.

### 3. Relocated the test so C4 can actually run it (the iteration-1/2 oracle-fit gap)

Iterations 1 and 2 both failed C4 not on substance but because the test lived at
`.github/scripts/tests/test_addon_system_deps.py`. `run-verify.sh:137` derives the
unittest module from the path with `tr '/' '.'`, giving
`.github.scripts.tests.test_addon_system_deps` — a **leading dot**, which
`python3 -m unittest` rejects (`ValueError: Empty module name`). So neither the
green nor the red leg could even load the test.

Fix: ship the test at **`tests/test_addon_system_deps.py`** — the repo's real test
package (it already holds `test_plugin_load_gate.py`, `test_plugin_registration.py`
and a headless-safe `__init__.py`). The runner now computes
`MODULE = tests.test_addon_system_deps`, which is importable. The test stays
import-light (pure stdlib; it adds `.github/scripts` to `sys.path` and imports
`addon_system_deps` — no `gi`/`gramps.gui`), so it runs under the headless C4
runner. It drives the **production** path: `deps.packages(...)`,
`deps.unmapped(...)`, and `deps.main(["--platform", ...])` / `["--unmapped", ...]`
— the exact calls ci.yml makes — not a copy.

## Red→green evidence

In iteration 4 the dockerised `run-verify.sh` was run directly (the fork worktrees
now exist) and passed — see the iteration-4 section above for the captured output
(`C4-verify: green-with-fix=PASS / red-without-fix=PASS`, exit 0). The test ships
at `tests/test_addon_system_deps.py`, so the runner derives the loadable module
name `tests.test_addon_system_deps` (iterations 1–2 failed only because the
`.github/`-rooted path yielded a leading-dot module name; iteration 3 fixed the
path but the gate never executed for lack of a worktree). The test is pure-stdlib
(adds `.github/scripts` to `sys.path`, imports `addon_system_deps`; no
`gi`/`gramps.gui`), so it runs under the headless C4 runner, and it drives the
**production** path — `deps.packages(...)`, `deps.unmapped(...)`,
`deps.main(["--platform", ...])` / `["--unmapped", ...]` — the exact calls ci.yml
makes, not a copy.

## The one item I could NOT complete, and why — surfaced for sign-off

The iteration-2 sign-off (brief.md:69) requires the fix be **exercised on the live
#820 fork pipeline** (both lanes green; an addon needing pygraphviz/psycopg2/
psycopg shows its suite RUNNING, not a swallowed `× … (continuing)`), and asks the
builder to **push a draft branch** to the fork for that.

This run's operating instructions explicitly state **"Do NOT push, open, or mark
any PR ready."** That directly conflicts with the carry-forward's push request. Per
builder STOP discipline I honoured the explicit instruction: **nothing was
pushed.** The fix is committed locally on the fork worktree branch
`fix/bug-820-build-toolchain-coverage` (1 commit, `070604f9a`, cut from the current
fork head `4fc07ba61`), ready to push — `git log origin/feature/ci-cd-pipeline-
upstream..HEAD` shows it, and `git branch -r` confirms no remote branch was
created.

**Action for the human at sign-off** (the two-step CI orchestration, documented so
it can be run as-is):
1. Push the branch: `git -C addons-source-6.0-fork push origin
   fix/bug-820-build-toolchain-coverage`.
2. The apt-lane fix needs the **gramps-ci image rebuilt** from the new Dockerfile:
   the CI workflow *pulls* `ghcr.io/eduralph/addons-source/gramps-ci:gramps60`; it
   does not build the Dockerfile inline. `docker-build.yml` rebuilds+pushes the
   image on push to `maintenance/gramps**` or via `workflow_dispatch`. Without the
   rebuild the apt lane still has gcc purged, so `pip install pygraphviz`/`psycopg2`
   would still fail even with the `-dev` headers present. So: trigger
   `docker-build.yml` (workflow_dispatch for gramps60) to publish the new image,
   then run #820 CI (open a draft PR to the fork's `maintenance/gramps60`, which is
   what the workflow's `on: pull_request` triggers on) and confirm both lanes green
   with the affected suites running. STOP: draft only — do not mark ready/merge.

I flag this as the carry-forward asking the builder to push while the run forbids
it — a brief/run-config conflict, not a fix defect. The substance the sign-off
disputed (the conda mapping, and now the `psycopg` C5(b) gap) is resolved in code.

## Why option (a), not (b) (unchanged, still in force)

The brief offers (a) provision the deps or (b) declare-and-gate an honest skip. (a)
is the reference fix (the testbed `Dockerfile.ubuntu` bakes `libgraphviz-dev
libpq-dev`), restores **real** coverage on both lanes (suites run, strictly better
than skipping), and carries no cross-bundle dependency. All three source-built mods
are provisionable on both apt and conda-forge, so (b)'s backstop is not needed to
restore the invariant here. I did not touch the `|| echo … (continuing)` swallow or
`addon_satisfiable_on` — that is (b)'s territory and out of scope.

### Cost of the rejected sub-alternative (conda → header + pip source build)

Mapping `conda` to a libpq/graphviz *library* and forcing a pip source build on
Windows (instead of the prebuilt conda-forge package) would re-introduce the exact
compiler-availability fragility this bundle removes, on a platform where
conda-forge already ships the binary. It would also need new ci.yml logic (a
Windows compiler toolchain + a separate build step) — vs. **0 new ci.yml lines**
for the chosen approach, since the conda step already installs `packages("conda")`.

## Commit-readiness

- `black --check` clean on both Python files (`2 files would be left unchanged`).
- `py_compile` OK on both; `ci.yml` parses as YAML.
- No trailing whitespace in either touched file (the lint job's `git grep -P
  '[ \t]+$'` gate); the pre-existing ArchiveAssist hits are unrelated and in an
  excluded/other addon.
- POTFILES: N/A — addons-source has no top-level `po/POTFILES.in`/`.skip` (its
  `po/` holds only `.pot`/`.po`); the existing `tests/*.py` are likewise
  unregistered. The touched files are CI tooling under `.github/` plus a test, none
  with translatable strings.
- Committed without `--no-verify`; the repo's pre-commit hook is disabled
  (`addons-source/.git/hooks/pre-commit.disabled`), consistent with the publish
  flow.

## Citations (target branch feature/ci-cd-pipeline-upstream @ 4fc07ba61)

- Defect: `.github/docker/gramps-ci/Dockerfile:111` (`RUN apt-get purge -y gcc
  python3-dev pkg-config …`); the swallow at `.github/workflows/ci.yml:262` (apt
  runtime), `:468` (conda runtime), `:614` (plugin-reg runtime).
- Fix — Dockerfile: drop the purge (patch.diff hunk 1).
- Fix — `addon_system_deps.py`: `MOD_BUILD_PACKAGES` (pygraphviz/psycopg2/psycopg),
  `WHEEL_ONLY_MODS`, `scan_modules`, `packages()` includes the new table,
  `unmapped()` reports mod drift, `main()` emits `mod:` + exits 1.
- Fix — `ci.yml`: the three "Install addon system deps" steps now cover source-built
  `requires_mod` (run before the runtime pip step on each lane); the "Validate addon
  system deps are mapped" error mentions `requires_mod`.
- New `psycopg` declaration driving the C5(b) fix:
  `PostgreSQLEnhanced/postgresqlenhanced.gpr.py:46`; hard import
  `PostgreSQLEnhanced/connection.py:38`.
- Other declarations: `NetworkChart/NetworkChart.gpr.py` (pygraphviz, networkx);
  `PostgreSQL/postgresql.gpr.py`, `SharedPostgreSQL/sharedpostgresql.gpr.py`
  (psycopg2).
- Single-source rule the fix respects: `Dockerfile:77-81`; GI/exe/mod derivation
  `addon_system_deps.py` `packages()`; ci.yml install steps at `:209`/`:443`/`:595`.
