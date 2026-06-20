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
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures)
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue_820-build-toolchain-coverage (advisory, artifact-only)

Reviewer inputs: `patch.diff`, `brief.md`, `check-gates.json`. `build-notes.md`
withheld by design — verdicts below are re-derived from the patch and gate
record, not from the builder's narrative.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md:18-22` states a checkable success criterion (build *or* attributed honest-skip), an invariant over the whole source-built `requires_mod` category (`brief.md:23-27`), and a resolved scope decision (a vs b). Spec is well-formed and decorrelatable. |
| C2 — C2 Reproduction (red pre-fix) | PASS | `check-gates.json:37` C4-verify `red-without-fix=PASS` — the shipped test is demonstrably red without the patch. Reproduction is the in-tree oracle (`tests/test_addon_system_deps.py` asserting the purge is absent / map populated), not the live #820 image; that gap is a V concern, not a C2 defect. |
| C3 — C3 Change | PASS | `patch.diff` is one coherent change implementing scope option (a): drop the Dockerfile purge (`patch.diff:9-21`), derive `libgraphviz-dev`/`libpq-dev` from `.gpr.py` via `MOD_BUILD_PACKAGES` (`addon_system_deps.py` hunk, lines 92-96), order system-dep install before the runtime pip step (`ci.yml` hunk, lines 206-215), and mirror it on the conda lane (lines 257-269). |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json:34-39` C4 (gating) = pass: `green-with-fix=PASS / red-without-fix=PASS`. Whole suite green-with-fix implies the category-completeness test (`test_every_declared_requires_mod_is_classified`, patch line 503) also passed against the current addon set. Oracle is the in-tree `run-verify.sh`; live-pipeline proof deferred to V (and acknowledged in iteration-1 carry-forward as an oracle-fit limitation, not a fix defect). |
| C5 — C5 Causal adequacy | PASS | Mechanism re-derived from the patch and is sound over the category: removing the purge restores gcc/pkg-config (`patch.diff:9-21`); `MOD_BUILD_PACKAGES` supplies the per-module `-dev`/libpq header on apt and the prebuilt conda-forge package on conda (lines 92-96); `WHEEL_ONLY_MODS` + `--unmapped` drift guard (lines 105-114, 153-166, 186-188) forces every future `requires_mod` to be classified or fail CI — closing recurrence. C5(a) conda resolvability resolved in brief iteration-2 carry-forward. The "does it run on live #820" half is V, below. |
| T1 — T1 Structure | N/A | `check-gates.json:51-57` T1 ✗ "tests: no .gpr.py" is a false positive: the addon-structure rule fires on a non-addon path. This patch ships no addon — it touches `.github/*` CI infra and `tests/` (the repo's existing test package, alongside `test_plugin_load_gate.py`, per patch line 348). No `.gpr.py` is expected or appropriate. |
| T2 — T2 Shape | PASS | New `tests/test_addon_system_deps.py` carries the GPL header (`patch.diff:297-314`); production edits to `addon_system_deps.py` are comments + table additions. `print()` calls are the CLI's legitimate stdout contract (lines 181-187), not stray debug. (Gate's "no checkable .py" note is conservative; re-derived directly from the diff here.) |
| T3 — T3 Runtime | PASS | gramps60 green (`check-gates.json:73`). gramps61 reports 1 delta — `Sqlite…ExportSQLTestCase::test_export_sq` (line 82). Causally isolated: the patch touches only `.github/*` and `tests/test_addon_system_deps.py` — no Sqlite addon, no core export, no runtime code — so it cannot produce this failure. Pre-existing baseline/flake noise (consistent across all three prior iterations). Advisory, non-gating; not attributable to this change. |
| T4 — T4 Contribution | N/A | `check-gates.json:91` — no `commit-msg.txt` or `pr-description.md` in the bundle to check against doc 16 §Commit/§Contributor workflow. |
| T5 — T5 Judgment | PASS | Engineering judgment is sound and re-derivable: the fix extends the existing single-source `GI_PACKAGES`/`EXE_PACKAGES` map pattern rather than hand-listing, classifies the whole `requires_mod` category, and each non-obvious choice is justified in-comment (toolchain-kept rationale `patch.diff:10-21`; conda-mirror rationale 257-269; why the test lives in `tests/` 345-352). Advisory PASS; fitness in production is V. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human, and the live #820 evidence the brief demands (iteration-2/3 carry-forward, `brief.md:69-70`, `brief.md:77`) is NOT derivable from these artifacts: that an addon needing pygraphviz/psycopg2 (e.g. GraphView) shows its unit suite **RUNNING** (or a named declared expected-skip) on the real fork pipeline with **both lanes green** — not a swallowed "× … (continuing)" silent green. The in-tree test proves the map/Dockerfile shape; it does not prove the live pipeline restores honest coverage. See §6. |

## §6 — items the human must clear

1. **V — live-pipeline fitness (the standing iteration-2/3 blocker).** Confirm
   the patch has been pushed to a draft branch cut from the current head of
   `eduralph/addons-source @ feature/ci-cd-pipeline-upstream` and that #820 CI
   ran on the fork, with attached evidence that **(a)** both the apt (Linux) and
   conda (Windows) lanes are green and **(b)** an addon whose `requires_mod`
   includes pygraphviz/psycopg2 has its unit suite *running* (or reported as a
   named, declared expected-skip), never the swallowed `× … (continuing)` silent
   green. The artifacts in this bundle prove only the in-tree `run-verify.sh`
   red→green; the brief's success criterion is the live result. STOP discipline
   applies — draft branch only, not ready/merge (`brief.md:57-58`).

## Reviewer notes (non-gating)

- C4 is PASS on the configured (in-tree) oracle, but the human should read it
  together with §6: a green in-tree test and a proven-on-#820 pipeline are
  different claims, and only the former is in the bundle.
- The gramps61 T3 delta (`test_export_sq`) and the T1 `.github`/`tests` false
  positive recur from prior iterations; both are re-derived here as
  not-attributable to this patch and should not block sign-off.
- C5's category-completeness leg (every declared `requires_mod` classified) is
  machine-enforced for the *current* addon set via the `--unmapped` guard and
  was exercised by the green suite; its durability for *future* additions rests
  on that guard staying gating in `ci.yml` ("Validate addon system deps are
  mapped", `patch.diff:227-245`).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] V — Validation — fitness-to-purpose — Always-human, and the live #820 evidence the brief demands (iteration-2/3 carry-forward, `brief.md:69-70`, `brief.md:77`) is NOT derivable from these artifacts: that an addon needing pygraphviz/psycopg2 (e.g. GraphView) shows its unit suite **RUNNING** (or a named declared expected-skip) on the real fork pipeline with **both lanes green** — not a swallowed "× … (continuing)" silent green. The in-tree test proves the map/Dockerfile shape; it does not prove the live pipeline restores honest coverage. See §6.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-18

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
