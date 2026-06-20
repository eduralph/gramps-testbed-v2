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
- C4 fix verified: test red pre-fix, green post-fix: fail — error: .github/workflows/ci.yml: No such file or directory
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

# Check review — 820-build-toolchain-coverage

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json` only (`build-notes.md` withheld). Every basis
> below is re-derived from those three artifacts.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md` is complete and unambiguous: defect (Dockerfile purges toolchain, source-built `requires_mod` silently swallowed — brief.md:8-17), success criterion (build or honest-skip, brief.md:18-22), invariant (brief.md:23-27), and a one-decision scope (a) bake/keep vs (b) declare-gate (brief.md:36-39). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added regression test encodes assertions that are red against the pre-fix tree by construction: `test_toolchain_not_purged` fails while the `apt-get purge … gcc …` line exists (patch.diff:233-246 vs the removed Dockerfile:9), and `test_packages_apt_includes_build_headers`/`test_cli_apt_emits_build_headers` error/fail with no `MOD_BUILD_PACKAGES` (patch.diff:185-210). Genuinely red→green by inspection. NB: not *executed* red here (see C4). |
| C3 — C3 Change | PASS | Coherent change implementing scope option (a): drops the purge (patch.diff:9), adds `MOD_BUILD_PACKAGES` (addon_system_deps.py:77-80), folds it into `packages()` so ci.yml derives it from the single `.gpr.py` source (line 90), and orders the install step before runtime pip (ci.yml:275-284). Scoped to `.github/` only; no out-of-scope Gramps-install changes. |
| C4 — C4 Verification (red→green) | FAIL | Gating gate failed: `run-verify.sh` → `error: .github/workflows/ci.yml: No such file or directory` (check-gates.json:33-39). Red→green was never demonstrated; the harness could not locate the file the patch edits (verify env appears to lack the addons-source checkout / path mismatch). Green post-fix is unproven. → §6. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Oracle is reviewer + human sign-off. Fix addresses both legs of the root cause on the **apt** lane (compiler kept + headers provisioned). But `MOD_BUILD_PACKAGES` sets `conda: None` (addon_system_deps.py:78-79); on the Windows/conda lane `pygraphviz`/`psycopg2` still fail to build and are swallowed by the same `|| echo … (continuing)` — the comment calls this "skips by necessity" but it is **not** an attributed honest-skip, so the invariant (brief.md:23-27, stated over the whole category) may not hold there. Contested adequacy → §6. |
| T1 — T1 Structure | N/A | Patch contains no addon (touches `.github/` only; brief surface = data, brief.md:31). Addon-layout rules (folder==id, `.gpr.py`, `target_version`) do not apply. The gate's `T1 ✗ .github: no .gpr.py` (check-gates.json:55) is a category mismatch, not a real defect. |
| T2 — T2 Shape | PASS | Only touched `.py` are CI tooling under `.github/scripts/` — outside the doc16 addon coding-style surface. No `print()` debug introduced; the new `test_addon_system_deps.py` uses `unittest`. Gate concurs (`N/A: no checkable .py path`, check-gates.json:64). Advisory: new test file carries no GPL header — acceptable for non-addon tooling, confirm against repo convention if desired. |
| T3 — T3 Runtime | FAIL | gramps61×core6.1 lane shows a new baseline delta: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (check-gates.json:82); 6.0 lane green (line 73). The patch touches no Sqlite addon and no runtime code (only `.github/`), so the delta is very likely pre-existing/flaky or environment-induced, not caused by this change — but the gate is red and must be cleared. → §6. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle to check against doc16 §Commit messages / §Contributor workflow (check-gates.json:91). Nothing to evaluate. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle is reviewer + human sign-off (check-gates.json:98). Always-human. → §6. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Oracle is human at sign-off (check-gates.json:109). Whether the fix truly restores honest coverage on the `eduralph/addons-source` fork (brief.md:22, 43-45) is human-validated only. → §6. |

## §6 — Items the human must clear

1. **C4 (gating) — verification did not run.** `run-verify.sh` failed with
   `.github/workflows/ci.yml: No such file or directory` (check-gates.json:37).
   This reads as a harness/path mismatch (the verify environment did not have the
   addons-source `.github/workflows/ci.yml` present), not necessarily a fix
   defect — but **no red→green was demonstrated**. The change cannot sign off
   until C4 executes green on the fork (brief.md:18-22).

2. **C5 — causal adequacy on the conda lane.** Root cause is addressed on apt,
   but `pygraphviz`/`psycopg2` map to `conda: None` (addon_system_deps.py:78-79)
   and the conda lane still swallows the failed build via the same
   `|| echo … (continuing)`. The brief's invariant is stated over the *whole*
   category of source-built `requires_mod` (brief.md:23-27); on conda this is a
   silent-by-necessity skip, not an attributed honest-skip. Human to decide
   whether that is acceptable (in-scope as "skips like the GI libs") or whether
   option (b)'s honest-skip backstop must also cover the conda lane.

3. **T3 — gramps61×core6.1 baseline delta.** New failure
   `Sqlite…test_export_sq` (check-gates.json:82). The patch touches no Sqlite or
   runtime code, so confirm this is a pre-existing/flaky/environment delta
   unrelated to the change (and, if so, rebaseline) rather than a regression
   before sign-off.

4. **T5 — judgment** and **V — validation fitness-to-purpose**: always-human.
   Confirm on the `eduralph/addons-source` fork that GraphView's suite either
   runs post-fix or is reported as a named expected-skip (brief.md:43-45), i.e.
   the green check now means what it says.

## Disposition

Advisory result: **do not sign off yet.** One gating gate (C4) is unmet and one
non-gating runtime gate (T3-61) is red; C5/T5/V are human-only. The change itself
(C1/C2/C3) is sound and well-scoped — the blocker is unexecuted verification, not
a flawed diff.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C5 — C5 Causal adequacy — Oracle is reviewer + human sign-off. Fix addresses both legs of the root cause on the **apt** lane (compiler kept + headers provisioned). But `MOD_BUILD_PACKAGES` sets `conda: None` (addon_system_deps.py:78-79); on the Windows/conda lane `pygraphviz`/`psycopg2` still fail to build and are swallowed by the same `
- [ ] T5 — T5 Judgment — Oracle is reviewer + human sign-off (check-gates.json:98). Always-human. → §6.
- [ ] V — Validation — fitness-to-purpose — Oracle is human at sign-off (check-gates.json:109). Whether the fix truly restores honest coverage on the `eduralph/addons-source` fork (brief.md:22, 43-45) is human-validated only. → §6.

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
- Iteration delta (if iterating): Option (a) was only completed on the apt lane. The conda lane exists to test Windows and provision its own dependencies, so it must mirror the Debian behavior — NOT silently skip. What to change: - MOD_BUILD_PACKAGES maps pygraphviz/psycopg2 to {"conda": None}. That is the silent-skip the invariant (brief.md:23-27, stated over the whole category) forbids: on conda the source build still fails and is swallowed by ci.yml's "|| echo … (continuing)". Populate the conda side — look pygraphviz/psycopg2 up in conda-forge and install them — instead of None. - The conda lane must provision-or-FAIL honestly (look it up in conda's repository, fail if not found), exactly as the apt lane does. No silent green. - Drop the "skips by necessity, exactly as the GI libs do" comment — that reasoning does not hold for this category; the conda lane is meant to install these deps, not skip them. Not in dispute (carry forward as-is): - The apt-lane fix (drop the purge, derive libgraphviz-dev/libpq-dev from .gpr.py, install before runtime pip) is sound — keep it. - C4 FAILED only because run-verify.sh cannot verify a .github/ CI-infra change (it patches a gramps-core/addon worktree); the shipped test runs green directly. Oracle-fit gap, not a fix defect. - T3-61 Sqlite test_export_sq delta is unrelated flaky/baseline noise (patch touches no Sqlite/runtime code).
- By / date: Eduard Ralph / 2026-06-10

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
