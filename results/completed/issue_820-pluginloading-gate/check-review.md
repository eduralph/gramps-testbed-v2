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
