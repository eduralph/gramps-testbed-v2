# Check review — issue 46 / graphview-import-raises-on-missing-deps

Advisory, artifact-only review. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(build-notes.md deliberately withheld). Verdicts below are re-derived independently,
not copied from the gate dispositions.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md:10` states a single load-bearing success criterion (`import GraphView.graphview` / `from … import DotSvgGenerator` completes without raising when GooCanvas/`dot` absent); invariant + scope + repro are all present and testable. |
| C2 — C2 Reproduction (red pre-fix) | PASS | `check-gates.json:37` gating C4-verify reports `red-without-fix=PASS` (suite ran red without the patch). Test drives it: `test_graphview_import.py:102-108` empties `PATH`, forcing `_DOT_FOUND` falsy → pre-fix `raise` at the old `graphview.py:120-122`. |
| C3 — C3 Change | PASS | `patch.diff:9-21` is pure removal of the two module-level `raise Exception(...)` guards (GooCanvas + GraphViz), exactly the mechanism the brief's scope permits (`brief.md:14`); nothing else in `graphview.py` touched. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json:33-39` — the only gating row — `result: pass`, `green-with-fix=PASS / red-without-fix=PASS`. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Removing the raise is the brief's named fix and leaves the registration-layer `requires_*` gate as sole arbiter (`brief.md:11`). BUT the T3 E2E row introduces a NEW failure `setUpClass (interface.test_smoke.SmokeTest)` (`check-gates.json:100`) absent from baseline — raising the question of whether the raise was load-bearing at GUI-load time. Whether the fix is causally complete or merely shifts an import-time failure to a runtime one is a contested root-cause call. Oracle: reviewer + human sign-off. |
| T1 — T1 Structure | PASS | `check-gates.json:55` — `T1 ✓ structure: 1 addon(s) conform to doc 16 §Structure`. New test sits at addon-convention `GraphView/tests/test_*.py` (`patch.diff:25`). |
| T2 — T2 Shape | PASS | `check-gates.json:63` — `T2 ✓ shape`. GPL header present on the only added file (`test_graphview_import.py:31-48`); `graphview.py` header untouched. |
| T3 — T3 Runtime | FAIL | Three non-gating T3 rows are red and attributed to this change by baseline delta: addon-unit ×6.0 and ×6.1 both `runner exited 2 … new failure mode` (`check-gates.json:73,82`), and addon E2E `1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)` (`check-gates.json:100`). Only GUI-interface smoke matched baseline (`:91`). Net new failures → FAIL, independent of the non-gating disposition. |
| T4 — T4 Contribution | N/A | `check-gates.json:109` — no `commit-msg.txt` or `pr-description.md` in the bundle, so the commit/PR-wrapper gate has nothing to assess. |
| T5 — T5 Judgment | NEEDS-HUMAN | Overall-quality judgment cannot be cleared while the T3 deltas (esp. the new E2E `setUpClass` failure) are unexplained and build-notes.md is withheld; needs human adjudication of whether they are environmental or regression. Oracle: reviewer + human sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off (`check-gates.json:125`); fitness of "module imports cleanly; end-user UX unchanged" against real-world intent is not machine-derivable. |

## §6 — items the human must clear

1. **C5 causal adequacy / contested root-cause.** The brief asserts the `requires_*`
   registration gate is the *sole* arbiter of plugin loading and that import is purely
   a side-effecting duplicate. The new E2E failure `setUpClass (interface.test_smoke.SmokeTest)`
   (`check-gates.json:100`) appearing only after the raises are removed is consistent with
   the addon now *loading* into the GUI on a host where it previously failed-fast and was
   gated out — which would mean the fix relocated an import-time failure to GUI-load time
   rather than eliminating it. Confirm against the target branch whether this E2E failure is
   pre-existing/environmental or a genuine regression introduced by the patch. build-notes.md
   was withheld from this review, so Do's own explanation has not been seen.

2. **T3 runtime regressions (gate says non-gating; reviewer flags anyway).** addon-unit on
   both 6.0 and 6.1 now exit 2 with "a new failure mode" not in baseline (`check-gates.json:73,82`).
   The brief's stated goal was that `GraphView/tests/` *collects and runs* on a host lacking
   `dot`; an exit-2 with no parsed failures is itself a collection/runner-level abort and is
   the opposite of that goal. Determine whether the new `test_graphview_import.py` (top-level
   `import gi` + `gi.require_version("Gtk","3.0")` at `:80-82`) is what aborts collection in the
   headless runner, vs. a pre-existing baseline gap. This must be resolved before sign-off
   despite `overall: "pass"`.

3. **Overall-disposition vs. matrix discrepancy.** `check-gates.json` reports `overall: "pass"`
   because only C4 is gating, yet three T3 rows are FAIL. The human should consciously accept
   or reject shipping with those non-gating runtime failures unresolved.

4. **T5 judgment** and **V validation fitness-to-purpose** — always-human; cannot be cleared by
   the reviewer.

## Note on cherry-pick (advisory)

The brief requires the gramps61 pick be verified to *remain correct*, not merely apply
(`brief.md:12`). Both T3 addon-unit matrices (6.0 and 6.1) are red here, so neither branch's
runtime is currently green in-bundle — the "remains correct on gramps61" obligation is not yet
demonstrated and folds into §6 item 2.
