# Build notes — 820-build-toolchain-coverage (iteration 2)

Withheld from the reviewer. Rationale, the iteration-2 conda-lane change, and the
C4-runner oracle-fit caveat.

## What iteration 2 changes vs iteration 1

Iteration 1 was signed off as "Option (a) completed on the apt lane only". The
**only** disputed item carried forward (brief.md:61) was the **conda lane**:

> MOD_BUILD_PACKAGES maps pygraphviz/psycopg2 to `{"conda": None}`. That is the
> silent-skip the invariant forbids over the whole category. Populate the conda
> side — look pygraphviz/psycopg2 up in conda-forge and install them — instead of
> None. The conda lane must provision-or-FAIL honestly … No silent green. Drop
> the "skips by necessity, exactly as the GI libs do" comment.

Carried forward unchanged (explicitly "not in dispute"): the apt-lane fix (drop
the purge; derive `libgraphviz-dev`/`libpq-dev` from `.gpr.py`; install before
the runtime pip step). I kept it byte-for-byte.

### The conda-lane fix

`addon_system_deps.MOD_BUILD_PACKAGES` (addon_system_deps.py, new table after
`EXE_PACKAGES`) now reads:

```python
MOD_BUILD_PACKAGES = {
    "pygraphviz": {"apt": "libgraphviz-dev", "conda": "pygraphviz"},
    "psycopg2":   {"apt": "libpq-dev",       "conda": "psycopg2"},
}
```

The two platforms carry *different kinds* of package, by design:

* **apt** — pip has no wheel, so it compiles the C extension; the value is the
  `-dev` header it links against (and the compiler toolchain stays in the image).
* **conda** — conda-forge ships the whole binding prebuilt, so the value is the
  module's own conda-forge package. The existing conda step
  (`ci.yml` "Install addon system deps", run `mamba install -y -c conda-forge
  $pkgs`) now installs `pygraphviz`/`psycopg2`, and the later `pip install`
  finds them already satisfied → **the suites run on Windows**, they no longer
  skip.

**Verified against conda-forge** (not recalled): I downloaded
`https://conda.anaconda.org/conda-forge/win-64/repodata.json` and confirmed both
packages are present with builds for current Python — `pygraphviz` up to 1.14
(py310–py314), `psycopg2` up to 2.9.12 (py310–py314). So the conda side resolves;
it is not a name that would make `mamba install` fail.

**Provision-or-FAIL honesty.** `mamba install -y -c conda-forge $pkgs` aborts the
job if a mapped package cannot be resolved — there is no `|| echo … (continuing)`
on the system-deps step (that swallow is only on the *pip runtime* step, which
this now front-runs). So a future source-built `requires_mod` whose conda value
is wrong/absent fails the lane loudly rather than degrading to a silent green. I
dropped the misleading "skips by necessity, exactly as the GI libs do" framing
from both the map comment and the conda ci.yml step comment; the GI-libs-skip
note remains only where it is still true (the GI typelibs genuinely are not on
conda-forge).

### Why install the full conda package, not a `-dev` header + pip build on conda

conda-forge has no separate `graphviz-dev`/`libpq-dev`-style split the way apt
does, and its `pygraphviz`/`psycopg2` are first-class prebuilt packages. Mapping
conda → the full package is the smallest change that makes the lane provision the
dep, costs no new ci.yml logic (the conda step already installs
`packages("conda")`), and gives real Windows coverage. Mapping conda → a library
and forcing a pip source build on Windows would re-introduce exactly the
compiler-availability fragility this bundle removes — and conda has the binary
already.

## Why option (a), not (b) (unchanged from iteration 1, still in force)

The brief offers (a) make them build / install, or (b) declare-and-gate an honest
skip. (a) is the reference fix (the testbed `Dockerfile.ubuntu` bakes
`libgraphviz-dev libpq-dev`), restores **real** coverage on *both* lanes (the
suites run, strictly better than skipping), and carries no cross-bundle
dependency. (b)'s honest-skip backstop would only be needed for a dep that is
genuinely unprovisionable on a platform — neither pygraphviz nor psycopg2 is, on
either apt or conda-forge — so (a) fully restores the invariant here without it.
I deliberately did **not** touch `addon_satisfiable_on` or the `|| echo …
(continuing)` swallow — that is (b)'s territory and out of scope.

## The honest-skip safety net still holds for a future None

If someone later adds a source-built `requires_mod` that genuinely is not on a
platform and maps it to `None` there, the dep is not installed, the addon's
suite all-skips, and `run_addon_tests._classify` reports a **hard FAILURE** (an
all-skip with `addon_satisfiable_on == True`, run_addon_tests.py:149-153) — i.e.
red, not a silent green. So the category invariant ("never silent green") is held
even outside the two modules fixed here.

## Tests

`/.github/scripts/tests/test_addon_system_deps.py` — pure stdlib, **no `gi` /
`gramps.gui` imports** (headless-safe). It drives the production derivation path
(`deps.packages(...)` and `deps.main(["--platform", ...])` — the exact calls
ci.yml makes), not a copy. New in iteration 2: `test_packages_conda_provisions_
source_built_mods` and `test_cli_conda_emits_source_built_mods` assert the conda
side is provisioned (not `None`), and `test_every_declared_source_built_mod_is_
provisioned_on_both_lanes` is the category/drift guard over BOTH lanes.

Red→green proven directly against the `addons-source-6.0-fork` worktree
(`feature/ci-cd-pipeline-upstream`):

* **Green with fix:** `Ran 8 tests … OK`.
* **Red with the production files reverted (test kept):** `FAILED (failures=3,
  errors=3)` — the 3 errors are `AttributeError: MOD_BUILD_PACKAGES` (table
  absent); the 3 failures are the apt CLI/packages assertions, the conda CLI
  assertion, and `test_toolchain_not_purged` on the `apt-get purge -y gcc …`
  line.

## C4-runner caveat — oracle-fit gap (carried forward, now isolated)

The brief's `Verification base` now drives run-verify to the
`addons-source-6.0-fork` worktree, which **does** carry the `.github/` files —
so iteration 1's `error: .github/workflows/ci.yml: No such file or directory`
(the patch failing to apply) is **gone**: the patch now applies cleanly to the
fork worktree.

What remains is a single irreducible limitation: run-verify derives the unittest
module name from the test *path* with `tr '/' '.'`, giving
`.github.scripts.tests.test_addon_system_deps` — a name with a **leading dot**,
which `python3 -m unittest` rejects with `ValueError: Empty module name`. A
`.github/`-rooted test path simply cannot be expressed as an importable Python
module, and there is no real addon dir to relocate it under (addon-mode
convention is `<Addon>/tests/test_*.py`). Both the green and red legs fail for
this *same* module-load reason (see `check`/`/tmp/verify-820.log`), so the runner
prints `green-with-fix=FAIL` — not a failure of the fix, but the harness being
unable to load the test at all.

This is exactly the case the runner's own `PDCA-UNVERIFIABLE` (exit 77) path
names — "a prose / ci.yml / fork-CI-verified change" (run-verify.sh:135) — but
that path only triggers when *no* `test_*.py` is shipped; shipping one (per the
human's "keep the test, it runs green directly") makes the runner attempt the
unloadable module instead. Per the carry-forward this is accepted as an
oracle-fit gap, not a fix defect. The authoritative verification the brief names
is on the fork: rebuild the `gramps-ci` image (toolchain kept) and run the
pipeline — `pip install pygraphviz`/`psycopg2` then succeed on apt (header +
compiler present) and conda-forge installs them on Windows, so the affected
suites run instead of silently skipping.

## Commit-readiness

* `black --check` clean on both Python files; `py_compile` OK; no trailing
  whitespace (the lint job's `git grep -P '[ \t]+$'` gate). ruff
  `--select=E9,F63,F7,F82` has nothing to flag.
* Patch applies cleanly to `feature/ci-cd-pipeline-upstream`
  (`git apply --check` → clean; diffstat: 4 files, +286/−25).
* POTFILES: N/A — addons-source has no top-level `po/POTFILES.in`/`.skip`, and
  the touched files are CI tooling under `.github/`, not a core module or an
  addon module.

## Citations (target branch `feature/ci-cd-pipeline-upstream`)

* Defect: `.github/docker/gramps-ci/Dockerfile:111` (the purge); pip-step swallow
  at `.github/workflows/ci.yml:262` (apt), `:468` (conda), `:614` (plugin-reg).
* Conda silent-skip fixed: `addon_system_deps.py` `MOD_BUILD_PACKAGES` conda side
  (was the iteration-1 `conda: None`); conda install step `ci.yml:433-446`
  (`mamba install -c conda-forge $pkgs`).
* Single-source rule the fix respects: `Dockerfile:77-81`; GI/exe derivation
  `addon_system_deps.py:138-146` (`packages()`), `ci.yml:209`/`:440`/`:592`.
* Declarations driving the fix: `NetworkChart/NetworkChart.gpr.py:39`
  (`pygraphviz`), `PostgreSQL/postgresql.gpr.py:34` /
  `SharedPostgreSQL/sharedpostgresql.gpr.py:34` (`psycopg2`).
