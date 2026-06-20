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
