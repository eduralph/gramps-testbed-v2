# Result — issue 13864 / dashboard-column-count-crash-locks-tree

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: On the Dashboard, "Configure the active view" → "Gramplet Layout" → "Number of Columns:" set to a large value (reporter used **1000**) freezes Gramps ("Not responding"), then it disappears with no error; on restart the family tree is **locked**. (Mantis 13864; confirmed on 6.0.1, note 1.)
- Success criterion: Setting the Dashboard "Number of Columns" to any value the field accepts (including a large one such as 1000) does **not** crash Gramps and does **not** leave the family tree locked — the gramplet layout either applies a sane (clamped/validated) column count or rejects the input, and Gramps stays responsive.
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core).
- Scope (one logical fix) / out of scope: an extreme/large Dashboard column count crashes Gramps and locks the tree — make the column-count path survivable for any accepted value. / **out of scope:** redesigning the Gramplet-Layout UX or imposing a product-level max-columns policy (that is a UX-direction call — flag to the human if the only viable fix is a hard cap); the separate gramplet-placement defect in 13865 (verify whether one root cause covers both **before** writing a shared fix — the verdict says these likely differ).

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest) — raw runner o
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 13864 / dashboard-column-count-crash-locks-tree

Advisory, artifact-only review. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(`build-notes.md` withheld by design). Every Basis below is re-derived from the
artifacts, not copied from the gate output.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:10` states a concrete success criterion ("any value the field accepts … does not crash … does not leave the tree locked") and `brief.md:11` an invariant ("any accepted column value → no crash/lock"). Spec is present and testable. |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | The shipped test (`grampletconfig_test.py:92`) imports only `gramps.gui.grampletconfig`; it never exercises the real crash path (`GrampletPane` widget allocation). "Red pre-fix" is just the new module being absent (ImportError), not a reproduction of the freeze/lock. `brief.md:17` anticipated this and required a `PDCA-UNVERIFIABLE` flag — whether helper-only testing adequately reproduces the GUI defect is a human call. |
| C3 — C3 Change | PASS | Diff is coherent and bounded: new pure helper (`grampletconfig.py:42`) routed through all three column-count ingress points — kwarg default (`grampletpane.py` ~1019), `.ini` load (~1198), `set_columns` (~1387). `set_columns` previously had only a lower bound (`if num < 1`); now bounded both ends. Scoped to the column-count path; no unrelated edits. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | Gate reports `C4-verify` PASS (gating), but the gating test (`grampletconfig_test.py`) does not import `grampletpane.py`, so reverting the *production* fix (the clamp calls in grampletpane) leaves the test green — red→green is decoupled from the actual change and verifies only the helper. The real defect path is GUI-only and thus unverifiable headless; per `brief.md:17` this warrants a `PDCA-UNVERIFIABLE` flag the Do did not raise. Human must clear. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Clamp is applied at construction, `.ini` load, and `set_columns`, which plausibly covers all column-count ingress. But the config dialog spinner writes `"Gramplet View Options.column_count"` via `self._config.set` directly (`grampletpane.py` ~1639); whether every accepted value reaches a clamped setter (vs. a direct write that bypasses it) is not provable from the artifact. Oracle is reviewer + human sign-off. |
| T1 — T1 Structure | PASS | Core change (files under `gramps/gui/…`), correctly placed: helper + `test/` (singular) `*_test.py` suffix, both registered in `po/POTFILES.skip` per `brief.md:19`. The gate's `T1 ✗ no .gpr.py` is the addon-structure rule and is N/A to a core change — no `.gpr.py` is expected here. |
| T2 — T2 Shape | PASS | GPL header present on both new files (`grampletconfig.py:4`, `grampletconfig_test.py:60`); matches gate `T2 ✓`. Re-derived: headers and module docstrings conform to doc 16 §Coding style; no stray `print()`. |
| T3 — T3 Runtime | NEEDS-HUMAN | Gate shows a delta: 1 new unit-suite failure `setUpClass (interface.test_smoke.SmokeTest)` not in baseline, yet the dedicated interface-smoke run matches its recorded baseline (1 known red). The contradiction points to an environmental/setup failure rather than a patch regression, but that cannot be confirmed from the artifacts — human must confirm the new red is not caused by the added `grampletconfig` import. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (gate `T4 – N/A`); nothing to check against doc 16 §Commit messages. Consistent with `brief.md:26-28` STOP discipline (PR not ready pre-sign-off). |
| T5 — T5 Judgment | NEEDS-HUMAN | The patch imposes a hard `MAX_GRAMPLET_COLUMNS = 100` (`grampletconfig.py:39`). `brief.md:15` lists "imposing a product-level max-columns policy" as **out of scope** and a "UX-direction call — flag to the human if the only viable fix is a hard cap." A hard cap is exactly that, so judgment is reserved to the human. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Fitness against `brief.md:10` ("applies a sane/validated count OR rejects the input") is a human call: the patch silently clamps (only a helptext hint at ~1641, no rejection/user feedback), and the chosen ceiling of 100 is a product policy decision per `brief.md:15`. Oracle is human at sign-off. |

## §6 — Items the human must clear

1. **C2 / C4 — reproduction & verification fidelity.** The test exercises the
   extracted helper `clamp_column_count`, not the GUI crash path it protects;
   the gating red→green does not move when the production clamp calls in
   `grampletpane.py` are reverted. Decide whether the headless helper test is an
   acceptable substitute or whether a `PDCA-UNVERIFIABLE` flag + interface test
   is required (`brief.md:17`).
2. **C5 — causal completeness.** Confirm every path that can set
   `column_count` (including the config-dialog spinner writing config directly)
   ultimately flows through `clamp_column_count`, so the invariant holds for
   *any* accepted value, not just the three setters patched.
3. **T3 — runtime delta.** Confirm the new `interface.test_smoke.SmokeTest`
   `setUpClass` failure is environmental and not introduced by the new
   `grampletconfig` import.
4. **T5 / V — hard-cap scope/UX decision.** `MAX_GRAMPLET_COLUMNS = 100` is a
   product-level max-columns policy the brief routes to the human as a
   UX-direction call (`brief.md:15`). Accept the cap value and the
   silent-clamp behavior, or direct an alternative (reject-with-feedback).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C2 — C2 Reproduction (red pre-fix) — The shipped test (`grampletconfig_test.py:92`) imports only `gramps.gui.grampletconfig`; it never exercises the real crash path (`GrampletPane` widget allocation). "Red pre-fix" is just the new module being absent (ImportError), not a reproduction of the freeze/lock. `brief.md:17` anticipated this and required a `PDCA-UNVERIFIABLE` flag — whether helper-only testing adequately reproduces the GUI defect is a human call.
- [ ] C4 — C4 Verification (red→green) — Gate reports `C4-verify` PASS (gating), but the gating test (`grampletconfig_test.py`) does not import `grampletpane.py`, so reverting the *production* fix (the clamp calls in grampletpane) leaves the test green — red→green is decoupled from the actual change and verifies only the helper. The real defect path is GUI-only and thus unverifiable headless; per `brief.md:17` this warrants a `PDCA-UNVERIFIABLE` flag the Do did not raise. Human must clear.
- [ ] C5 — C5 Causal adequacy — Clamp is applied at construction, `.ini` load, and `set_columns`, which plausibly covers all column-count ingress. But the config dialog spinner writes `"Gramplet View Options.column_count"` via `self._config.set` directly (`grampletpane.py` ~1639); whether every accepted value reaches a clamped setter (vs. a direct write that bypasses it) is not provable from the artifact. Oracle is reviewer + human sign-off.
- [ ] T3 — T3 Runtime — Gate shows a delta: 1 new unit-suite failure `setUpClass (interface.test_smoke.SmokeTest)` not in baseline, yet the dedicated interface-smoke run matches its recorded baseline (1 known red). The contradiction points to an environmental/setup failure rather than a patch regression, but that cannot be confirmed from the artifacts — human must confirm the new red is not caused by the added `grampletconfig` import.
- [ ] T5 — T5 Judgment — The patch imposes a hard `MAX_GRAMPLET_COLUMNS = 100` (`grampletconfig.py:39`). `brief.md:15` lists "imposing a product-level max-columns policy" as **out of scope** and a "UX-direction call — flag to the human if the only viable fix is a hard cap." A hard cap is exactly that, so judgment is reserved to the human.
- [ ] V — Validation — fitness-to-purpose — Fitness against `brief.md:10` ("applies a sane/validated count OR rejects the input") is a human call: the patch silently clamps (only a helptext hint at ~1641, no rejection/user feedback), and the chosen ceiling of 100 is a product policy decision per `brief.md:15`. Oracle is human at sign-off.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): The shipped test (grampletconfig_test.py) exercises only the extracted helper clamp_column_count, not the GUI crash path in GrampletPane; revoking the production clamp calls in grampletpane.py leaves the test green — C4 red→green is decoupled from the actual fix. This is the second occurrence of this pattern. Do must: (1) remove the helper-only test; (2) add a PDCA-UNVERIFIABLE flag per brief.md:17 (GUI-crash path is headless-unverifiable); (3) ship an interface test in gramps-testbed (tests/interface/test_bug_13864_dashboard_columns.py) as the reproduction vehicle. C5 is confirmed clean (self._config.set always routes through set_columns via the registered setter). T3 delta is pre-existing/environmental. T5/V (MAX_GRAMPLET_COLUMNS=100, silent-clamp) to be raised with the maintainer in the PR.
- By / date: Eduard Ralph / 2026-06-20

## 10. Act candidates (hints for the next Act review)
- Recurring pattern (2nd occurrence): Do ships a helper-only unit test as a substitute for a GUI-crash reproduction, decoupling C4 red→green from the production change; consider adding a brief rule / Do skill note that helper tests for GUI-crash paths must be accompanied by a PDCA-UNVERIFIABLE flag and an interface test, not shipped alone.
