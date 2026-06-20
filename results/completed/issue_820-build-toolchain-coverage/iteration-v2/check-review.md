# Check review — 820-build-toolchain-coverage (iteration 2)

Advisory, artifact-only. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(build-notes.md deliberately withheld). Each Basis below is re-derived from the
diff/brief, not copied from the builder's narrative.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Change implements brief scope option (a): toolchain kept (`patch.diff:9-21`), `-dev` headers provisioned from `.gpr.py` via `MOD_BUILD_PACKAGES` (`patch.diff:85-88`), installed before runtime pip (ci.yml comment `patch.diff:334-336`). Matches success criterion (build-or-honest-skip) over the category (brief.md:18-27). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Red pre-fix is structural: the new test references `deps.MOD_BUILD_PACKAGES` (`patch.diff:201,221,263`), absent pre-patch → AttributeError; `test_toolchain_not_purged` (`patch.diff:285-298`) asserts no `apt-get purge … gcc` line, which existed pre-patch (`patch.diff:9`). No gate configured (check-gates C2 "none"); reproduction not mechanically run. |
| C3 — C3 Change | PASS | One logical change — restore source-built `requires_mod` coverage: un-purge toolchain, add single-source `MOD_BUILD_PACKAGES` + wire into `packages()` (`patch.diff:98`), update three ci.yml install steps + new regression test. On-scope, no unrelated edits. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | Configured oracle `run-verify.sh` FAILED — gating (check-gates C4: worktree missing; harness patches a core/addon worktree, not a `.github/` CI-infra change). Oracle-fit gap, not shown to be a fix defect; red→green for a CI-infra patch can only be demonstrated by running #820 CI on the fork. Human must verify. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Apt-lane causal story is sound (purged compiler + missing `-dev` headers → swallowed source-build failure → silent green; fix restores both). Unverifiable from artifacts: that conda-forge actually ships `pygraphviz`/`psycopg2` prebuilt and `mamba install` fails honestly (`patch.diff:80-88,359-367`), and that the hand-kept category `_SOURCE_BUILT_MODS` (`patch.diff:162`) is complete. Oracle = human sign-off. |
| T1 — T1 Structure | N/A | Addon-layout gate (folder==id, `.gpr.py`, no `__init__.py`) does not apply — patch ships no addon; it touches `.github/` CI infra + `.github/scripts/`. The gate's FAIL ("`.github`: no `.gpr.py`", check-gates T1) is a false positive from running an addon-structure rule on non-addon paths. |
| T2 — T2 Shape | PASS | No addon `.py` path to check (check-gates T2 N/A). Advisory: new `test_addon_system_deps.py` carries a shebang+docstring but no GPL header (`patch.diff:108-134`); if doc16 §Coding-style applies to CI-script `.py`, add one. Not gating. |
| T3 — T3 Runtime | PASS | Patch touches zero runtime/addon code (only `.github/**` + a CI-script test), so it cannot cause a Sqlite regression. 6.0 lane green (check-gates T3-60); the 6.1 `ExportSQLTestCase::test_export_sq` delta (check-gates T3-61) is non-attributable baseline/flaky noise. Human may confirm against baseline flakiness. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` / `pr-description.md` in the bundle (check-gates T4) — no commit/PR wrapper to evaluate. |
| T5 — T5 Judgment | NEEDS-HUMAN | Holistic judgment, oracle = reviewer + human sign-off. Approach is well-reasoned and single-source-of-truth; residual judgment calls: completeness of the `_SOURCE_BUILT_MODS` category, the unverified conda-forge availability/honest-fail claim, and the missing GPL header. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. The observable (GraphView's suite RUNS post-fix, or is reported as a named expected-skip) must be confirmed on the `eduralph/addons-source` fork's #820 CI (brief.md:18-22,45-47) — not derivable from artifacts. |

## §6 — items the human must clear

1. **C4 — verification could not run.** `run-verify.sh` (gating) failed: it expects
   a core/addon worktree and cannot exercise a `.github/` CI-infra patch. Confirm
   red→green by running #820 CI on the fork, or accept the in-tree
   `test_addon_system_deps.py` as the standing oracle and record the oracle-fit gap.
2. **C5 — causal adequacy / category completeness.** Verify (a) `pygraphviz` and
   `psycopg2` resolve on conda-forge so `mamba install` provisions (not skips), and
   (b) `_SOURCE_BUILT_MODS` covers every source-built `requires_mod` the addons
   declare — a new source-built mod absent from this hand-kept list would still
   silently skip, the exact failure mode the invariant forbids.
3. **T5 — judgment sign-off.** Clears with C5; also decide whether the new CI-script
   test needs a GPL header (T2 advisory).
4. **V — fitness-to-purpose.** Confirm on the fork that an addon needing
   `pygraphviz`/`psycopg2` (e.g. GraphView) actually runs its suite or shows a named
   declared expected-skip — the brief's sole observable.
