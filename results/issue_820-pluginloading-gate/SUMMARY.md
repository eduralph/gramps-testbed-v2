# Result — issue 820-pluginloading-gate / 820-pluginloading-gate

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: on the PR #820 branch, `TestPluginLoading.test_load_all_addon_modules`
- Success criterion: a non-dependency hard load failure makes
- Repo + branch target: gramps-project/addons-source @ `maintenance/gramps60` via
- Scope (one logical fix) / out of scope: make `test_load_all_addon_modules` fail on non-dependency hard load

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (small; one gating decision + the seam C4 requires,
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
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — 820-pluginloading-gate

Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`,
`check-gates.json` (build-notes.md withheld by design). Every verdict below is
re-derived from those artifacts, not from the builder's narrative.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | Brief carries a concrete success criterion (red→green: synthetic hard failure makes the real method raise `failureException`, brief.md:22-28), a category-level invariant (brief.md:29-34) and a settled disposition (gate, brief.md:35-39). Spec is unambiguous. |
| C2 — C2 Reproduction (red pre-fix) | PASS | The regression is constructed red against pre-fix behavior: pre-fix the method only `LOG.warning`s and returns, so `_run_load_test_with` returns `None` (patch.diff:218-238) and `assertIsInstance(None, failureException)` (patch.diff:253-258) fails. `check-gates.json` C4 `red-without-fix=PASS` confirms a red leg executed. (Fidelity of the red *mechanism* → C5.) |
| C3 — C3 Change | PASS | Change matches brief scope exactly: hard-failure `LOG.warning` block replaced by `self.fail(hard_load_failure_message(...))` (patch.diff:104-112); helper extracted to a non-test unit (patch.diff:53-68); `dep_skips`/`crash_failures` advisory warnings left intact (patch.diff:100-102); `_get_addon_plugins` (the parked 820-review-nits region) untouched. No scope creep. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` C4 is the sole gating row and is `pass`: `green-with-fix=PASS / red-without-fix=PASS` (rule C4-verify, run-verify.sh). Machine red→green satisfied. Mechanism caveat raised under C5. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Oracle is reviewer+human. Root cause (silent `LOG.warning` vs `self.fail`) is addressed, but the C4 red leg reverts the non-test file `plugin_load_gate.py` (run-verify:130) — removing the helper breaks `from tests.plugin_load_gate import …` (patch.diff:77) with an ImportError. So red→green binds to *helper presence*, not to the original silent-pass behavior, which lives in the un-reverted `test_*.py` file. Human must confirm the red faithfully reproduces the defect rather than an import break. |
| T1 — T1 Structure | N/A | `check-gates.json` T1 FAIL ("no .gpr.py") is misapplied: the patch adds `tests/*.py` modules (patch.diff:1,116), not an addon package — the doc16 §Structure addon-packaging rule (folder==id, .gpr.py, target_version) does not apply to test-tree files. Non-gating; no structural defect re-derivable. |
| T2 — T2 Shape | PASS | Both new files carry the full GPL header (patch.diff:7-25, :122-140) and consistent module style (`from __future__ import annotations`, section banners). `check-gates.json` T2 "N/A: no checkable .py path" reflects the gate scoping to addon paths only; re-derived shape of the touched test `.py` files is compliant. |
| T3 — T3 Runtime | NEEDS-HUMAN | Mixed and ambiguous. Interface-smoke matches baseline (PASS), but addon-unit-60, addon-unit-61 and addon-interface all report **new-failure deltas** vs baseline ("runner exited 2 … no matching baseline signature"; "1 new failure: setUpClass interface.test_smoke.SmokeTest"). Brief.md:72-73 itself warns the now-live gate fails on environmental addon-load gaps (missing GTK icon theme, `stock_link`) on the minimal image. Cannot determine from artifacts whether these deltas are pre-existing env flakiness or introduced by making the gate live — human triage required. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` / `pr-description.md` in the bundle (`check-gates.json` T4). Brief.md:88-90 waives the T4 Mantis-trailer MUST for this addons-source follow-up. Nothing to check. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle reviewer+human. Reviewer read: fix is small, in-scope, drives the real production method (addresses the iteration-1 reject), and restores the stated invariant. Open judgment items it cannot self-clear: the C5 red-leg-fidelity question and the T3 runtime deltas. Defer overall judgment to human sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Whether gating (not advisory) is the right contract, and whether this fix is fit for the PR #820 CI purpose, is the human's call at sign-off (brief.md:35-39 settles the disposition but validation is reserved to the human). |

## §6 — Items the human must clear

1. **C5 — red-leg causal fidelity.** Confirm that the C4 red is a genuine
   reproduction of the silent-pass defect and not an artifact of reverting the
   extracted helper (which breaks the import at `tests/test_plugin_registration.py`
   import of `hard_load_failure_message`, patch.diff:77). The behavioral change
   (`self.fail` vs `LOG.warning`) lives in a `test_*.py` file that run-verify does
   not revert, so the red leg flips on helper-presence rather than on the original
   warn-only behavior. Decide whether that is an acceptable C4 demonstration for a
   defect whose change site is itself a test file.

2. **T3 — runtime deltas.** Triage the new-failure deltas on addon-unit-60,
   addon-unit-61 and addon-interface (`check-gates.json` T3 rows). Determine whether
   they are pre-existing minimal-image/environmental gaps (as brief.md:72-73
   anticipates for the now-live real `test_load_all_addon_modules`) or a regression
   introduced by this patch. The brief's own flakiness warning makes this an
   ambiguous, human-only call.

3. **T5 — overall judgment.** Reviewer+human sign-off on whether the bundle is
   accepted, contingent on items 1 and 2.

4. **V — fitness-to-purpose.** Human validation that the gate (not advisory)
   contract fits the PR #820 CI intent and the invariant in brief.md:29-34.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Oracle is reviewer+human. Root cause (silent `LOG.warning` vs `self.fail`) is addressed, but the C4 red leg reverts the non-test file `plugin_load_gate.py` (run-verify:130) — removing the helper breaks `from tests.plugin_load_gate import …` (patch.diff:77) with an ImportError. So red→green binds to *helper presence*, not to the original silent-pass behavior, which lives in the un-reverted `test_*.py` file. Human must confirm the red faithfully reproduces the defect rather than an import break.
- [x] T3 — T3 Runtime — Mixed and ambiguous. Interface-smoke matches baseline (PASS), but addon-unit-60, addon-unit-61 and addon-interface all report **new-failure deltas** vs baseline ("runner exited 2 … no matching baseline signature"; "1 new failure: setUpClass interface.test_smoke.SmokeTest"). Brief.md:72-73 itself warns the now-live gate fails on environmental addon-load gaps (missing GTK icon theme, `stock_link`) on the minimal image. Cannot determine from artifacts whether these deltas are pre-existing env flakiness or introduced by making the gate live — human triage required.
- [x] T5 — T5 Judgment — Oracle reviewer+human. Reviewer read: fix is small, in-scope, drives the real production method (addresses the iteration-1 reject), and restores the stated invariant. Open judgment items it cannot self-clear: the C5 red-leg-fidelity question and the T3 runtime deltas. Defer overall judgment to human sign-off.
- [x] V — Validation — fitness-to-purpose — Always-human. Whether gating (not advisory) is the right contract, and whether this fix is fit for the PR #820 CI purpose, is the human's call at sign-off (brief.md:35-39 settles the disposition but validation is reserved to the human).

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
- By / date: Eduard Ralph / 2026-06-16

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
- INTEGRATION.md: document that when C4 can't be verified (test-fixes-test / test-only patch with no non-test file for run-verify's red leg), the right approach is to flag C4 as unverifiable and have the human accept it — NOT to manufacture a non-`test_` "production" module solely to give run-verify a file to revert (issue_820-pluginloading-gate).
- Follow-up on the shipped fix: this bundle was accepted as-is, but the harness-driven helper `tests/plugin_load_gate.py` should be dropped from the contribution — inline the `self.fail(...)` in `test_plugin_registration.py` and keep the regression test `tests/test_plugin_load_gate.py`. The helper exists only to give run-verify's C4 red leg a file to revert; once INTEGRATION.md allows flagging C4 unverifiable, it is no longer warranted.
