# Result — issue 820-build-toolchain-coverage / 820-build-toolchain-coverage

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: PR #820's `.github/docker/gramps-ci/Dockerfile` purges the build
- Success criterion: source-built addon deps either **build** in PR #820 CI (the
- Repo + branch target: gramps-project/addons-source @ `maintenance/gramps60` via
- Scope (one logical fix) / out of scope: decide and implement one of: (a) keep `libgraphviz-dev`/`libpq-dev` (and

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix — carries one decision (bake headers vs declare-and-
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: worktree /home/eddie/workspace/addons-source-6.0-fork-lane0 missing — run 'make worktrees LANES=N'.
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ .github: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures)
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 — C4 Verification (red→green) — Configured oracle `run-verify.sh` FAILED — gating (check-gates C4: worktree missing; harness patches a core/addon worktree, not a `.github/` CI-infra change). Oracle-fit gap, not shown to be a fix defect; red→green for a CI-infra patch can only be demonstrated by running #820 CI on the fork. Human must verify.
- [ ] C5 — C5 Causal adequacy — Apt-lane causal story is sound (purged compiler + missing `-dev` headers → swallowed source-build failure → silent green; fix restores both). Unverifiable from artifacts: that conda-forge actually ships `pygraphviz`/`psycopg2` prebuilt and `mamba install` fails honestly (`patch.diff:80-88,359-367`), and that the hand-kept category `_SOURCE_BUILT_MODS` (`patch.diff:162`) is complete. Oracle = human sign-off.
- [ ] T5 — T5 Judgment — Holistic judgment, oracle = reviewer + human sign-off. Approach is well-reasoned and single-source-of-truth; residual judgment calls: completeness of the `_SOURCE_BUILT_MODS` category, the unverified conda-forge availability/honest-fail claim, and the missing GPL header.
- [ ] V — Validation — fitness-to-purpose — Always-human. The observable (GraphView's suite RUNS post-fix, or is reported as a named expected-skip) must be confirmed on the `eduralph/addons-source` fork's #820 CI (brief.md:18-22,45-47) — not derivable from artifacts.

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): issue_820-build-toolchain-coverage — rejected: the fix has never been exercised on the real #820 pipeline, so C4 (build red→green), C5(b) (category completeness) and V (GraphView's suite actually runs) are unverified. The whole point of this fix is that CI silently lied about coverage, so it must be proven on the live pipeline, not just by the in-tree test. What to change / do next (per human): - Push the patch onto a branch cut from the CURRENT head of the fork's #820 branch (eduralph/addons-source @ feature/ci-cd-pipeline-upstream) and run #820 CI on the fork. The builder leaf is permitted to push a draft branch for this; the fix is currently on NO branch of the fork (MOD_BUILD_PACKAGES absent, test file 404, code search 0 hits — confirmed at sign-off), so there is nothing for fork CI to exercise yet. STOP discipline still applies: draft branch only, do not mark ready / merge. - Attach the CI result as the C4/V evidence: both lanes green AND an addon needing pygraphviz/psycopg2 (e.g. GraphView) shows its unit suite RUNNING (or a named, declared expected-skip) — not a swallowed "× … (continuing)" silent green. - C5(b): confirm _SOURCE_BUILT_MODS covers every source-built requires_mod the addons actually declare (scan the .gpr.py set), so a newly-added one cannot silently skip. Not in dispute (carry forward as-is, do NOT re-litigate): - C5(a) verified at sign-off: pygraphviz (1.14) and psycopg2 (2.9.12) both resolve on conda-forge incl. win-64, so the conda lane's mamba install provisions them (the iteration-1 conda:None silent-skip objection is resolved). Keep the conda mapping. - The apt-lane fix (drop the Dockerfile purge, derive libgraphviz-dev/libpq-dev from .gpr.py via MOD_BUILD_PACKAGES, install before the runtime pip step) is sound. - T1 ✗ (.github no .gpr.py) is a false positive — addon-structure rule on non-addon paths. T3-61 ExportSQLTestCase::test_export_sq delta is unrelated baseline noise (patch touches no Sqlite/runtime code).
- By / date: Eduard Ralph / 2026-06-17

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
