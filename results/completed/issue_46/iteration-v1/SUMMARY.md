# Result — issue 46 / graphview-import-raises-on-missing-deps

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: `GraphView/graphview.py` raises a bare `Exception` at **module import** when GooCanvas (`graphview.py:111-113`) or the `dot`/GraphViz binary (`:120-122`) is unavailable. These fire at top level, so the module is unimportable by any caller that has not first consulted the plugin's declared requirements — including the addon's own test collection: `GraphView/tests/test_graphview_dot_handles.py` does `from GraphView.graphview import DotSvgGenerator` at top level, so on a host without `dot` the test loader crashes during collection (traceback, 0 tests) instead of the suite running. The `.gpr.py` already declares `requires_gi=[("GooCanvas","2.0,3.0")]` and `requires_exe=["dot"]` (`graphview.gpr.py:16-17`), and Gramps' own plugin manager already gates loading on them — `Requirements.check_plugin()` (`gramps/gen/utils/requirements.py:129-133`) and `_pluginreg.scan_dir()` removing any plugin whose check fails (`gramps/gen/plug/_pluginreg.py:1478-1479`) — so it never imports the module when a requirement is absent. The module-level `raise` therefore duplicates a gate the framework already owns and breaks every direct importer. Reported and root cause verified on the target branch; the raises are present unchanged on `maintenance/gramps60` and `maintenance/gramps61`.
- Success criterion: On the target branch, importing the module — `import GraphView.graphview`, and `from GraphView.graphview import DotSvgGenerator` — completes **without raising** when GooCanvas / the `dot` binary are absent. The shipped regression test drives that import with the dependency unavailable: pre-fix it errors during import, post-fix it imports cleanly, so `GraphView/tests/` collects and runs on a host lacking `dot` instead of crashing collection. The plugin's missing-dependency behaviour for end users is unchanged — it remains gated by the registration-level `requires_*`.
- Repo + branch target: addons-source @ `maintenance/gramps60` (addons production — INTEGRATION §2; branch from `upstream/maintenance/gramps60`). Cherry-pick forward to `maintenance/gramps61` as a **separate** pick — the issue states the same code is on both branches; verify it remains correct there ("applies cleanly" is not "remains correct").
- Scope (one logical fix) / out of scope: Remove the import-time hard failure so the module imports when its declared GooCanvas/`dot` dependencies are absent. (Mechanism — pure removal of the raises vs. relocating any availability check — is left to Do; this brief names no probe/guard. Do prefers removing the cause over guarding it, principles §3.1/§3.3.) / out of scope: changing the missing-dependency UX for end users (already owned by `requires_gi`/`requires_exe` at registration), the bug-13832 DOT node-id quoting logic, and the GooCanvas API calls inside the view's runtime methods.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (open issue; root cause verified on target branch; reproduces; localized behavioural fix).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 ✓ structure: 1 addon(s) conform to doc 16 §Structure
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C5 — C5 Causal adequacy — Removing the raise is the brief's named fix and leaves the registration-layer `requires_*` gate as sole arbiter (`brief.md:11`). BUT the T3 E2E row introduces a NEW failure `setUpClass (interface.test_smoke.SmokeTest)` (`check-gates.json:100`) absent from baseline — raising the question of whether the raise was load-bearing at GUI-load time. Whether the fix is causally complete or merely shifts an import-time failure to a runtime one is a contested root-cause call. Oracle: reviewer + human sign-off.
- [ ] T5 — T5 Judgment — Overall-quality judgment cannot be cleared while the T3 deltas (esp. the new E2E `setUpClass` failure) are unexplained and build-notes.md is withheld; needs human adjudication of whether they are environmental or regression. Oracle: reviewer + human sign-off.
- [ ] V — Validation — fitness-to-purpose — Always-human at sign-off (`check-gates.json:125`); fitness of "module imports cleanly; end-user UX unchanged" against real-world intent is not machine-derivable.

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
- Iteration delta (if iterating): Reject: the regression test reimplements GTK load/version-pinning (test_graphview_import.py:80-82, top-level `import gi` + gi.require_version("Gtk","3.0")). GTK loading/pinning is already owned by gramps at runtime and by PR 950 in unit testing, so this machinery must not be in the addon test — it is redundant and is the likely cause of the two T3 addon-unit exit-2 collection aborts (6.0 and 6.1). Rebuild the test without any manual gi/Gtk pinning (rely on gramps / PR 950); keep the production change (removal of the two import-time raises) as-is. Re-run T3 addon-unit and E2E; confirm the E2E setUpClass (interface.test_smoke.SmokeTest) delta clears once the pin is gone.
- By / date: Eduard Ralph / 2026-06-13

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
