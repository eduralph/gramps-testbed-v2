# Build notes — 820-build-toolchain-coverage

Withheld from the reviewer. Rationale, alternatives, and the C4-runner caveat.

## Root cause (two sentences)

PR #820's CI image purges the build toolchain — `RUN apt-get purge -y gcc
python3-dev pkg-config && apt-get autoremove -y`
(`.github/docker/gramps-ci/Dockerfile:111` on `feature/ci-cd-pipeline-upstream`)
— after the Gramps install, while addon `requires_mod` are pip-installed at CI
runtime (`.github/workflows/ci.yml:262` "Install addon runtime deps"). So a
source-built `requires_mod` (no wheel for the image's Python/arch) has neither a
compiler nor its `-dev` header at install time, fails to build, and the failure
is swallowed by the step's `|| echo "× $mod failed to install (continuing)"`
(`ci.yml:262`, mirrored at `:468` and `:614`) — leaving the addon's suite to
skip while the job stays green.

Concretely (brief repro): `pip install pygraphviz` fails for *two* missing
pieces — no `gcc` (purged) **and** no `graphviz/cgraph.h` (the `libgraphviz-dev`
header was never installed anywhere); `psycopg2` likewise needs `libpq-dev` /
`pg_config`. NetworkChart declares `requires_mod=["networkx", "pygraphviz"]`
(`NetworkChart/NetworkChart.gpr.py:39`); PostgreSQL and SharedPostgreSQL declare
`requires_mod=["psycopg2"]` (`PostgreSQL/postgresql.gpr.py:34`,
`SharedPostgreSQL/sharedpostgresql.gpr.py:34`).

## Decision: option (a) — make them build (toolchain + headers present)

The brief offers (a) keep the toolchain/headers so deps build, or (b) declare
the skip and gate it honestly. I chose **(a)**:

- It is the **reference fix**: the testbed `engine/docker/Dockerfile.ubuntu`
  bakes `libgraphviz-dev libpq-dev` precisely to avoid this (brief prior-art /
  review finding C3).
- It restores **real coverage** (the affected suites *run*), which is strictly
  better than honestly skipping them.
- It carries **no cross-bundle dependency**: the brief notes (b) must sequence
  after `testbed-honest-skip` (T1) so the honest-skip backstop exists; (a) does
  not.

The fix has two halves, split by *which* dependency is generic vs addon-specific
— mirroring the existing architecture where the generic GTK runtime is baked in
the image but addon-declared system deps are derived from `.gpr.py`:

1. **Generic compiler toolchain → stays in the image.** Removed the purge
   (`Dockerfile:111`). gcc / python3-dev / pkg-config are not addon-specific;
   they are what *any* C-extension build needs, so they belong in the image and
   must survive to CI runtime when `requires_mod` are compiled.

2. **Per-package `-dev` headers → derived from the single source of truth.**
   Added `MOD_BUILD_PACKAGES` to `.github/scripts/addon_system_deps.py`
   (`pygraphviz→libgraphviz-dev`, `psycopg2→libpq-dev`) and included it in
   `packages()`. The existing "Install addon system deps" step
   (`ci.yml:201`, `:577`) already runs `addon_system_deps.py --platform apt` and
   `apt-get install`s the result, so it now provisions these headers **before**
   the requires_mod pip step — with no new install logic. Keeps `.gpr.py` the
   single source of truth, exactly as the Dockerfile's own comment
   (`Dockerfile:77-81`) and the `requires_gi`/`requires_exe` handling already
   insist.

`ci.yml` step *names/comments* were updated (the two apt jobs) so the step that
now also installs requires_mod build headers says so — keeping the workflow
honest about what it does. No behavioural ci.yml change was needed.

### Why headers go in the deps-map, not hard-baked in the Dockerfile

The brief's literal wording for (a) is "keep libgraphviz-dev/libpq-dev … in the
image." I put them in `addon_system_deps.py` (installed at CI runtime) instead,
because:

- The Dockerfile **explicitly forbids** baking addon-derived deps into the image
  (`Dockerfile:77-81`: "Addon runtime deps … are NOT baked in here … Keeps
  .gpr.py the single source of truth"). Hard-coding `libgraphviz-dev`/`libpq-dev`
  by name in the image would re-introduce exactly the parallel hand-kept list
  that file's design eliminated.
- `requires_gi`/`requires_exe` system deps are **already** derived at CI runtime
  this way (`ci.yml:201-216`); routing the requires_mod build headers through the
  same map is the consistent, drift-guardable home for them.
- It gives a **headless, production-routed test seam**: the test calls the very
  `packages()`/CLI that `ci.yml` consumes — not a copy.

The generic toolchain still lives in the image (half 1), so "the needed
headers/toolchain are present" (Success criterion) holds.

## Alternatives considered and rejected

- **Pure Dockerfile bake (literal option a).** Add `libgraphviz-dev libpq-dev`
  to the image `apt-get install` (`Dockerfile:58-75`) and drop the purge —
  ~3 lines, smallest diff. Rejected: it violates the Dockerfile's stated
  single-source-of-truth rule (`:77-81`), has **no drift guard** (a future
  source-built `requires_mod` needing a new header is silently uncovered again),
  and leaves **nothing headlessly testable** (a Dockerfile string is the only
  artifact). Cost of my choice over it: +1 small map table + `packages()` gains
  one entry in its loop tuple (1 token: `, MOD_BUILD_PACKAGES`) — measured, not
  "heavier".

- **Option (b): declare-and-gate the skip (honest-skip).** Make the requires_mod
  install failure an *attributed expected-skip* rather than swallowed. Rejected
  per the brief's sequencing: (b) must run after `testbed-honest-skip` (T1), and
  it yields **no coverage** (GraphView/NetworkChart/PostgreSQL suites would skip,
  honestly, but skip). (a) makes them run. I deliberately did **not** also touch
  the `|| echo … (continuing)` swallow or the "Validate requires_mod …" step's
  `pip-install failed earlier, skipping` branch (`ci.yml:303`) — that is option
  (b)'s territory, and the brief says implement *one*.

- **Wiring requires_mod into `addon_satisfiable_on` / the honest-skip runner.**
  Would extend `run_addon_tests.py`'s expected-skip accounting to requires_mod.
  Rejected as scope creep into (b) and as risk to the existing GI/exe
  honest-skip behaviour; not needed once the deps build.

## Tests

`/.github/scripts/tests/test_addon_system_deps.py` — pure stdlib, **no `gi` /
`gramps.gui` imports** (headless-safe). It exercises the production derivation
path (`deps.packages("apt")` and `deps.main(["--platform","apt"])` — the exact
call `ci.yml` makes), plus a category/drift guard (every source-built
`requires_mod` an addon actually declares must be mapped and surfaced) and a
Dockerfile-content invariant (the toolchain is installed and not purged).

Red→green proven directly against the feature-branch worktree (see caveat below
for why the engine runner cannot do it here):

- **Green with fix:** `Ran 6 tests … OK`.
- **Red with production reverted (test kept):** `FAILED (failures=2, errors=2)`
  — `test_cli_apt_emits_build_headers` / `test_packages_apt_includes_build_headers`
  fail (no `libgraphviz-dev`/`libpq-dev`; `MOD_BUILD_PACKAGES` absent) and
  `test_toolchain_not_purged` fails on the `apt-get purge -y gcc …` line.

## C4-runner caveat — surfaced for Check sign-off

`./engine/scripts/ubuntu/run-verify.sh` **cannot** validate this bundle, by
construction, and this is a brief/harness mismatch worth recording (not a defect
in the patch):

- The bundle's target is `addons-source @ feature/ci-cd-pipeline-upstream` — the
  branch that *introduces* the entire `.github/` CI pipeline (Dockerfile, ci.yml,
  `addon_system_deps.py`). None of these files exist on `upstream/maintenance/
  gramps60` or `gramps61`.
- run-verify's **addon mode** mounts the clean upstream maintenance worktrees
  (`addons-source-6.0` = `upstream/maintenance/gramps60`, etc.) and `git apply`s
  the patch there. Observed output:
  `error: .github/docker/gramps-ci/Dockerfile: No such file or directory` (×3,
  both legs) — the CI files aren't on those branches.
- Even with the files present, run-verify derives the test module from the path
  as `.github.scripts.tests.test_addon_system_deps` — an invalid module name
  (leading dot; `.github` is not an importable package). Its addon-mode
  convention is `<Addon>/tests/test_*.py → Addon.tests.test_x`, which does not
  fit a `.github/scripts/` CI-tooling test.

So the red→green evidence above is via direct `python3 -m unittest` against a
worktree of `feature/ci-cd-pipeline-upstream` (host, pure-stdlib, instant — not a
hand-rolled `docker run`, no hang risk). The **authoritative** verification the
brief itself names is on the fork: rebuild the `gramps-ci` image from the patched
Dockerfile and run the pipeline — `pip install pygraphviz`/`psycopg2` then
succeed (toolchain + headers present) and the affected addons' suites run instead
of silently skipping.

## Commit-readiness

- `black --check` clean on both Python files; no trailing whitespace (the lint
  job's `git grep -P '[ \t]+$'` gate); `py_compile` OK. ruff
  `--select=E9,F63,F7,F82` has nothing to flag (the module imports and runs).
- Patch applies cleanly to a pristine `feature/ci-cd-pipeline-upstream`
  (`git apply --check` → clean).

## Citations (target branch `feature/ci-cd-pipeline-upstream`)

- Defect: `.github/docker/gramps-ci/Dockerfile:111` (the purge); swallow at
  `.github/workflows/ci.yml:262` (`:468`, `:614` mirror it).
- Install ordering: system deps `ci.yml:201`/`:577` run before requires_mod pip
  `ci.yml:230`/`:444`/`:592`.
- Single-source rule the fix respects: `Dockerfile:77-81`; existing GI/exe
  derivation `addon_system_deps.py:138-146` (`packages()`), `ci.yml:209`.
- Declarations driving the fix: `NetworkChart/NetworkChart.gpr.py:39`,
  `PostgreSQL/postgresql.gpr.py:34`, `SharedPostgreSQL/sharedpostgresql.gpr.py:34`.
