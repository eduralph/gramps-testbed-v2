# Result — issue 820-pluginloading-gate / 820-pluginloading-gate

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: in `tests/test_plugin_registration.py`,
- Success criterion: the test either `self.fail`s on non-dependency
- Repo + branch target: gramps-project/addons-source @ `maintenance/gramps60` via
- Scope (one logical fix) / out of scope: the gating decision in `test_load_all_addon_modules`. / out of scope: the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (small; one gating decision + a proving test).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — error: tests/test_plugin_registration.py: No such file or directory
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures)
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 820-pluginloading-gate

> Advisory, artifact-only review. Inputs: `patch.diff`, `brief.md`,
> `check-gates.json`. `build-notes.md` deliberately withheld — so the
> builder's own repro/verification narrative is **not** available to me, and
> every "was it demonstrated red→green" question is answered from artifacts
> alone.

## Cross-cutting note (read before the table)

The gating C4 oracle (`run-verify.sh`) failed with
`error: tests/test_plugin_registration.py: No such file or directory`, and the
T1/T2 gates likewise report the patch's files as absent ("no .gpr.py", "no
checkable .py path in patch.diff"). The patch *modifies* that exact existing
file and *adds* `tests/plugin_load_gate.py`. The consistent file-not-found
signature means the verify harness ran against a checkout that did not contain
the addon's `tests/` tree — so the mechanical T1/T2/C4 results reflect a path
/ checkout problem, not the patch's content. I therefore re-derive T1/T2 from
`patch.diff` directly and treat C4 verification as **never executed**.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md` is a complete, human-authored spec: defect, success criterion (gate **or** documented-advisory), invariant, scope/out-of-scope, repro instruction all present (`brief.md:8-44`). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No repro gate configured (`check-gates.json:15-21`), and the withheld `build-notes.md` is the only place a red-pre-fix run would be recorded. Structural doubt: the new test exercises only the new helper `hard_load_failure_message` (`patch.diff:140-159`), not the defective production path `test_load_all_addon_modules`; pre-fix it would error on a missing import, not go red on the silent-pass defect itself. Human must confirm a genuine red-pre-fix repro exists. |
| C3 — C3 Change | PASS | `patch.diff` is present and coherent: replaces the silent `LOG.warning` with `self.fail(gating_message)` (`patch.diff:104-112`) routed through an extracted policy helper, and updates the docstring to declare the gate (`patch.diff:86-95`). Caveat: adds a new module `tests/plugin_load_gate.py` beyond the brief's stated "edits `tests/test_plugin_registration.py`" surface — defensible refactor-for-testability, see §6 scope item. |
| C4 — C4 Verification (red→green) | FAIL | Sole gating row failed: `run-verify.sh` → `tests/test_plugin_registration.py: No such file or directory` (`check-gates.json:33-40`), driving `overall: fail`. red→green was never demonstrated; verification did not run against the patched tree. |
| C5 — C5 Causal adequacy | PASS | Root cause (named failure class `hard_failures` only `LOG.warning`-ed, sole assertion `assertGreater(len(plugins),0)`) is uncontested and the diff directly restores the invariant: hard failures now yield a message → `self.fail` (`patch.diff:64-67`, `104-112`); dependency-skip / crash classification kept as advisory per scope. Formal oracle is human sign-off. |
| T1 — T1 Structure | N/A | T1 checks addon layout (folder==id, `target_version`, `.gpr.py`, no `__init__.py`). This patch touches only `tests/` (a CI test + helper), not an addon — addon-structure conformance does not apply. Gate's "fail (no .gpr.py)" is the rule misfiring on a test-only change (`check-gates.json:51-57`). |
| T2 — T2 Shape | PASS | Re-derived from the diff (gate's "no checkable .py path" is the checkout problem above): new file carries the full GPL header (`patch.diff:7-24`), a module docstring and reST-typed function docstring, `from __future__ import annotations`, and no stray `print()`. |
| T3 — T3 Runtime | NEEDS-HUMAN | Baseline-green on gramps60×core6.0, but three DELTA failures recorded: gramps61×6.1 `Sqlite…ExportSQLTestCase::test_export_sq` and GUI/addon-E2E `setUpClass (interface.test_smoke.SmokeTest)` (`check-gates.json:78-102`). A plugin-load *gating* change in `tests/` cannot plausibly break Sqlite export or GUI display-server smoke; these read as environmental/baseline drift, but causation vs. this patch needs human triage. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle, so commit-message / contributor-workflow conformance cannot be checked (`check-gates.json:105-111`). |
| T5 — T5 Judgment | NEEDS-HUMAN | Holistic judgment is an always-human item (oracle: reviewer + human sign-off, `check-gates.json:114-120`). The standing judgment calls: helper-only regression coverage vs. end-to-end gating proof, and the scope expansion (§6). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off (`check-gates.json:123-129`). Whether the chosen gate (vs. the brief's alternative documented-advisory contract) is the right disposition for the named invariant is the human's call. |

## §6 — Items the human must clear

1. **C2 — reproduction adequacy (red-pre-fix not demonstrable from artifacts).**
   The regression test (`TestPluginLoadingGate`, `patch.diff:125-159`) unit-tests
   the *newly added* helper `hard_load_failure_message` — it never drives the
   production `test_load_all_addon_modules` path that held the defect. Pre-fix,
   the helper did not exist, so the test would fail on import (collection error),
   not go red on the silent-pass behaviour the brief targets. The brief's repro
   path (synthetic always-failing module detected → test fails, `brief.md:33-39`)
   appears unmet. Confirm a true red-pre-fix demonstration exists (likely in the
   withheld `build-notes.md`), or require one.

2. **C4 — verification never executed (gating failure).** The only gating gate
   failed because the harness could not find `tests/test_plugin_registration.py`.
   red→green is unproven. The patch must be re-verified in a checkout that
   actually contains the addons-source `tests/` tree before sign-off.

3. **T3 — unexplained runtime deltas.** Three new failures (Sqlite export on the
   6.1 matrix; `SmokeTest.setUpClass` on GUI + addon-E2E). Determine whether they
   are pre-existing/environmental (display-server, baseline drift) or — implausibly
   — attributable to this change. If environmental, the baselines need refreshing.

4. **Scope (C3 / T5) — new file beyond stated edit surface.** The brief scopes
   the work to "edits `tests/test_plugin_registration.py`" and the gating decision
   inside `test_load_all_addon_modules` (`brief.md:27-32`). The patch adds a new
   module `tests/plugin_load_gate.py`. This is a reasonable extract-for-testability
   move, but it is an ambiguous-scope call the human must accept or reject.

5. **T5 / V — disposition & fitness.** The builder chose the *gate* contract over
   the brief's permitted *documented-advisory* alternative. Confirm the gate is the
   intended disposition and that it fits the invariant ("a CI test that names a
   failure class gates on it"), and clear the holistic judgment / fitness sign-off.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C2 — C2 Reproduction (red pre-fix) — No repro gate configured (`check-gates.json:15-21`), and the withheld `build-notes.md` is the only place a red-pre-fix run would be recorded. Structural doubt: the new test exercises only the new helper `hard_load_failure_message` (`patch.diff:140-159`), not the defective production path `test_load_all_addon_modules`; pre-fix it would error on a missing import, not go red on the silent-pass defect itself. Human must confirm a genuine red-pre-fix repro exists.
- [ ] T3 — T3 Runtime — Baseline-green on gramps60×core6.0, but three DELTA failures recorded: gramps61×6.1 `Sqlite…ExportSQLTestCase::test_export_sq` and GUI/addon-E2E `setUpClass (interface.test_smoke.SmokeTest)` (`check-gates.json:78-102`). A plugin-load *gating* change in `tests/` cannot plausibly break Sqlite export or GUI display-server smoke; these read as environmental/baseline drift, but causation vs. this patch needs human triage.
- [ ] T5 — T5 Judgment — Holistic judgment is an always-human item (oracle: reviewer + human sign-off, `check-gates.json:114-120`). The standing judgment calls: helper-only regression coverage vs. end-to-end gating proof, and the scope expansion (§6).
- [ ] V — Validation — fitness-to-purpose — Always-human at sign-off (`check-gates.json:123-129`). Whether the chosen gate (vs. the brief's alternative documented-advisory contract) is the right disposition for the named invariant is the human's call.

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
- Iteration delta (if iterating): Rejected: the gating C4 never ran and the C2 repro is inadequate — both fail. Carry-forward for the next Do: - C4 (verification gap): run-verify.sh failed with `tests/test_plugin_registration.py: No such file or directory`. The patch targets addons-source and the verify harness ran against a checkout without that tests/ tree, so red→green was never executed. Rebuild/verify in a checkout that actually contains the addons-source tests/ tree (re-sync first, as with the sibling #820 bundles). Until then C4 is unproven. - C2 (repro inadequacy — the substantive one): the regression test TestPluginLoadingGate only unit-tests the NEW helper hard_load_failure_message; it never drives the defective production path test_load_all_addon_modules. Pre-fix the helper did not exist, so the test would error on collection/import, not go red on the silent-pass defect. The brief's repro (synthetic always-failing module → test_load_all_addon_modules fails) is unmet. The next attempt must prove the gate end-to-end on the actual production path, not just the extracted helper. - T5 / scope: the patch adds a new module tests/plugin_load_gate.py beyond the brief's stated edit surface (tests/test_plugin_registration.py). Defensible extract-for-testability, but call it out and confirm it is in-scope. - T5 / disposition: builder chose the *gate* contract over the brief's permitted *documented-advisory* alternative — confirm gate is intended in the next pass. - T3 deltas (Sqlite 6.1 export; SmokeTest.setUpClass on GUI-smoke + addon-E2E) are decorrelated from a tests/ gating change — environmental/baseline drift, no need to chase.
- By / date: Eduard Ralph / 2026-06-10

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
- issue_820-pluginloading-gate: update/re-sync testbed-gramps-v2 before the next iteration; the C4 re-verify depends on the refreshed checkout.
