# Check review — glade-setattr-name-mangling

Advisory, artifact-only review. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(`build-notes.md` withheld by design). Verdicts re-derived independently below.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:10 gives an unambiguous success criterion; defect, scope, and two-line fix spec (brief.md:9,12,16–24) are concrete and verified against `maintenance/gramps61`. |
| C2 — C2 Reproduction (red pre-fix) | PASS | No C2 gate configured, but reproduction is demonstrated by C4-verify `red-without-fix=PASS` (check-gates.json:37); matches brief repro (brief.md:13) — `_Glade__dirname` AttributeError pre-fix. |
| C3 — C3 Change | PASS | patch.diff:9–18 matches the brief fix spec verbatim (mangled whitelist + dropped duplicate `self`); only `__setattr__` and the new test touched, `__init__` untouched — in scope (brief.md:12). |
| C4 — C4 Verification (red→green) | PASS | check-gates.json:33–39 gating C4-verify `green-with-fix=PASS / red-without-fix=PASS`; new test (patch.diff:85–101) drives the real `Glade()` path per Iteration-1 ask (brief.md:39). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause of the AttributeError/TypeError is well-supported, but the fix is not shown causally adequate to the stated criterion "launch the GUI": T3-interface still reds with a NEW `setUpClass` failure (check-gates.json:100). Whether that residual is environmental or a real gap is contested — human must decide. |
| T1 — T1 Structure | N/A | Core-only change; no addons-source path in patch.diff and doc 16 §Structure is addon-only (check-gates.json:55). |
| T2 — T2 Shape | PASS | check-gates.json:64 — 1 file conforms to §Coding style; missing GPL header on the new test accepted as repo test-file convention, non-blocking (brief.md:39). |
| T3 — T3 Runtime | FAIL | T3-interface — the success-criterion smoke — still red: `1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)` (check-gates.json:100). T3-unit exited 133 / addon-60 / addon-61 also fail (check-gates.json:73,82,91). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (check-gates.json:109). |
| T5 — T5 Judgment | NEEDS-HUMAN | Code change is sound, minimal, in-scope and unit-green, yet the end-to-end criterion (GUI smoke) is unmet (T3-interface red). Accept/reject hinges on the contested setUpClass residual — reviewer+human sign-off (check-gates.json:114). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off. Brief success criterion "the T3-interface smoke launches the GUI" (brief.md:10) is not demonstrably met; fitness-to-purpose cannot be auto-asserted. |

## §6 — Items the human must clear

1. **C5 — causal adequacy / contested root-cause.** The `__setattr__` two-bug fix
   removes the AttributeError/TypeError, but T3-interface smoke still shows a NEW
   `setUpClass (interface.test_smoke.SmokeTest)` failure not in baseline. Determine
   whether this is an environmental headless-dogtail `setUpClass` failure or a real
   residual blocking GUI startup — exactly the open question carried forward from
   Iteration 1 (brief.md:39). Baseline re-promotion (brief.md:26) cannot proceed
   until it is green for the right reason.

2. **T5 — judgment.** Unit-level verification is green (C4), the real `Glade()`
   construction path is now exercised (addresses the Iteration-1 ask), and the diff
   is minimal/in-scope — but the brief's load-bearing success criterion is the GUI
   smoke, which is still red. Human to weigh whether the unit-green fix is acceptable
   despite the unmet end-to-end criterion.

3. **V — validation fitness-to-purpose.** Human at sign-off must confirm the fix
   actually restores GUI startup as intended, given T3-interface is not green.

## Notes (advisory, non-gating)

- T3-unit exited 133 with no parsed failures and no matching baseline signature
  (check-gates.json:73) and the addon matrices exited 1 (lines 82, 91). These read
  as runner/environment deltas rather than failures attributable to this two-line
  core change, but they are unexplained from the artifacts alone and should not be
  silently treated as pass. Only T3-interface bears directly on the success criterion.
- Positive: the new test (patch.diff:43–49, 85–101) deliberately loads a real,
  display-free `GtkListStore` `.glade` through the real `__init__`, directly answering
  the Iteration-1 request to stop relying on a synthetic `__setattr__` bypass.
