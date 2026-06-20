# Brief — issue 820-build-toolchain-coverage / source-built requires_mod silently skip

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Decomposed from `results/issue_pr820-ci-checkin/` (convergence C3). Tracks
> addons-source PR #820.

- **Slug:** 820-build-toolchain-coverage
- **Defect:** PR #820's `.github/docker/gramps-ci/Dockerfile` purges the build
  toolchain — `RUN apt-get purge -y gcc python3-dev pkg-config && apt-get autoremove
  -y` — after the Gramps install, and addon `requires_mod` are pip-installed at **CI
  runtime** (`ci.yml`, "Install addon runtime deps"). So `requires_mod` packages with
  no wheel that compile from source (`pygraphviz` → needs `libgraphviz-dev`;
  `psycopg2` → needs `libpq-dev` / `pg_config`) fail to build and are swallowed by the
  step's `|| echo "× … (continuing)"`. An addon that hard-imports them (e.g.
  GraphView) then runs a **silently degraded** unit suite that still reports green.
  The testbed's `engine/docker/Dockerfile.ubuntu` bakes `libgraphviz-dev libpq-dev`
  precisely to avoid this.
- **Success criterion:** source-built addon deps either **build** in PR #820 CI (the
  needed headers/toolchain are present) **or** their skip is **explicitly declared and
  reported as an attributed expected-skip** (honest-skip), never a silent green — an
  addon needing `pygraphviz`/`psycopg2` either runs its suite or is shown skipping for
  a named, declared reason. Verified on the `eduralph/addons-source` fork.
- **Invariant to restore:** declared addon dependencies are *honestly satisfied or
  honestly skipped* — a missing build toolchain must not turn into silent coverage
  loss reported as success. Stated over the category (every source-built
  `requires_mod`). Source: `docs/principles.md` (a green check must mean what it says);
  ties to the honest-skip backstop (testbed issue `testbed-honest-skip`).
- **Repo + branch target:** gramps-project/addons-source @ `maintenance/gramps60` via
  `feature/ci-cd-pipeline-upstream`; image rebuilt + tested on the
  `eduralph/addons-source` fork.
- **Verification base:** origin/feature/ci-cd-pipeline-upstream
- **Onto branch:** origin/feature/ci-cd-pipeline-upstream
- **Surfaces:** data.
- **Depends on:** 820-converge-requires-mod-dedup
  (C3 edits the same `.github/workflows/ci.yml` requires_mod install step as C2 (the chain
  head), so it must stack after C2 on the #820 branch, never concurrently. The honest-skip
  backstop the *declare-and-gate-skip* option (b) would need is already shipped out-of-band
  as a testbed change, so it is not a bundle dependency here.)
- **Scope:** decide and implement one of: (a) keep `libgraphviz-dev`/`libpq-dev` (and
  the minimal toolchain) in the image so source-built deps build (match the testbed),
  or (b) declare which `requires_mod` are expected to skip and gate the skip honestly.
  / out of scope: the PyPI-first / SHA-pinned-git Gramps-install layer (correct as-is).
- **Repro instruction:** in the PR #820 image, `pip install pygraphviz` fails (no
  `gcc`/`graphviz/cgraph.h`); the `ci.yml` install step prints `× pygraphviz failed …
  (continuing)` and GraphView's unit suite skips while the job stays green.
- **Test file:** verify on the fork that GraphView's suite either runs post-fix or is
  reported as a named expected-skip by the honest-skip backstop; no new addon
  `test_*.py` required (coverage/honesty is the observable).
- **Citations expected:** Do cites the Dockerfile `apt-get purge` line and the `ci.yml`
  `requires_mod` install "continuing" branch on the PR branch.
- **Prior-art check (triage cycles):** the testbed `Dockerfile.ubuntu` bakes the build
  headers (the reference fix); review finding C3. No prior fix on #820.
- **Disposition hint:** likely-fix — carries one decision (bake headers vs declare-and-
  gate the skip).

## STOP discipline

Draft only until Check sign-off. The PR MUST NOT be marked ready before sign-off
accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Option (a) was only completed on the apt lane. The conda lane exists to test Windows and provision its own dependencies, so it must mirror the Debian behavior — NOT silently skip. What to change: - MOD_BUILD_PACKAGES maps pygraphviz/psycopg2 to {"conda": None}. That is the silent-skip the invariant (brief.md:23-27, stated over the whole category) forbids: on conda the source build still fails and is swallowed by ci.yml's "|| echo … (continuing)". Populate the conda side — look pygraphviz/psycopg2 up in conda-forge and install them — instead of None. - The conda lane must provision-or-FAIL honestly (look it up in conda's repository, fail if not found), exactly as the apt lane does. No silent green. - Drop the "skips by necessity, exactly as the GI libs do" comment — that reasoning does not hold for this category; the conda lane is meant to install these deps, not skip them. Not in dispute (carry forward as-is): - The apt-lane fix (drop the purge, derive libgraphviz-dev/libpq-dev from .gpr.py, install before runtime pip) is sound — keep it. - C4 FAILED only because run-verify.sh cannot verify a .github/ CI-infra change (it patches a gramps-core/addon worktree); the shipped test runs green directly. Oracle-fit gap, not a fix defect. - T3-61 Sqlite test_export_sq delta is unrelated flaky/baseline noise (patch touches no Sqlite/runtime code).
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — error: .github/workflows/ci.yml: No such file or directory
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ .github: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: issue_820-build-toolchain-coverage — rejected: the fix has never been exercised on the real #820 pipeline, so C4 (build red→green), C5(b) (category completeness) and V (GraphView's suite actually runs) are unverified. The whole point of this fix is that CI silently lied about coverage, so it must be proven on the live pipeline, not just by the in-tree test. What to change / do next (per human): - Push the patch onto a branch cut from the CURRENT head of the fork's #820 branch (eduralph/addons-source @ feature/ci-cd-pipeline-upstream) and run #820 CI on the fork. The builder leaf is permitted to push a draft branch for this; the fix is currently on NO branch of the fork (MOD_BUILD_PACKAGES absent, test file 404, code search 0 hits — confirmed at sign-off), so there is nothing for fork CI to exercise yet. STOP discipline still applies: draft branch only, do not mark ready / merge. - Attach the CI result as the C4/V evidence: both lanes green AND an addon needing pygraphviz/psycopg2 (e.g. GraphView) shows its unit suite RUNNING (or a named, declared expected-skip) — not a swallowed "× … (continuing)" silent green. - C5(b): confirm _SOURCE_BUILT_MODS covers every source-built requires_mod the addons actually declare (scan the .gpr.py set), so a newly-added one cannot silently skip. Not in dispute (carry forward as-is, do NOT re-litigate): - C5(a) verified at sign-off: pygraphviz (1.14) and psycopg2 (2.9.12) both resolve on conda-forge incl. win-64, so the conda lane's mamba install provisions them (the iteration-1 conda:None silent-skip objection is resolved). Keep the conda mapping. - The apt-lane fix (drop the Dockerfile purge, derive libgraphviz-dev/libpq-dev from .gpr.py via MOD_BUILD_PACKAGES, install before the runtime pip step) is sound. - T1 ✗ (.github no .gpr.py) is a false positive — addon-structure rule on non-addon paths. T3-61 ExportSQLTestCase::test_export_sq delta is unrelated baseline noise (patch touches no Sqlite/runtime code).
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — run-verify.sh: worktree /home/eddie/workspace/addons-source-6.0-fork-lane0 missing — run 'make worktrees LANES=N'.
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ .github: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 3 — carry-forward (from the previous attempt)
- Sign-off rationale: Bundle is not verifiable as-is. Before the next Do/Check: - C4 never ran: run-verify failed because worktree /home/eddie/workspace/addons-source-6.0-fork-lane0 was missing ('make worktrees LANES=N'). Provision the worktree so the red->green test (tests/test_addon_system_deps.py) actually executes — no evidence yet that it fails pre-fix / passes post-fix. - Advisory review never produced (reviewer leaf crashed, non-zero exit). Re-run the Check reviewer; bundle cannot be accepted without one. - T3 gramps61 delta: 1 new failure not in baseline, Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq. Confirm whether it is caused by this change or pre-existing noise. The patch approach itself looks sound — this iterate is to get the bundle verified, not to redesign the fix.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — run-verify.sh: worktree /home/eddie/workspace/addons-source-6.0-fork-lane0 missing — run 'make worktrees LANES=N'.
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Full previous attempt preserved in `iteration-v3/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
