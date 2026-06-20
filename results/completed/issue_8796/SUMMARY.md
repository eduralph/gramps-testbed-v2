# Result — issue 8796 / viewmanager-empty-views-indexerror

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Hiding **all** view plugins ("Loaded Plugins") in the Plugin Manager makes Gramps crash at startup with `IndexError: list assignment index out of range`. With no view plugins available, `ViewManager.get_available_views()` returns `[]`, so `views_to_show([])` returns `(0, 0, [])` (`gramps/gui/viewmanager.py:1832` — `default_cat_views = [0] * len(views)` collapses to `[]`); `init_interface` sets `self.current_views = []` (`:641`) then calls `goto_page(0, 0)` (`:645`), which executes `self.current_views[cat_num] = view_num` on the empty list (`:927`) and raises. The same empty-view state then cascades into `__change_page` (`:1049-1051`) and `config_view` (`:1501`). Confirmed by reporter (4.2.0beta2) and re-confirmed by callmedave on 5.2.3; lines unchanged on the target branch.
- Success criterion: With zero available views (every view plugin hidden), Gramps initialises the main interface without raising any exception — the navigation path returns cleanly and the app opens with no active page instead of crashing. The shipped regression test drives the **production** startup/navigation path with an empty available-view set: pre-fix it raises `IndexError: list assignment index out of range`, post-fix it completes without raising.
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core fix; branch from `upstream/maintenance/gramps61`, forward-merged to `master` — INTEGRATION §2).
- Scope (one logical fix) / out of scope: Remove the startup crash that occurs when the available-view set is empty — the GUI must initialise its interface and open the main window with no active page instead of raising `IndexError` (and instead of the follow-on `__change_page` / `config_view` failures rooted in the same empty-view state). / out of scope: Plugin-Manager UX changes (e.g. warning the user before hiding the last view), forcing "at least one view always loaded", and any change to plugin-hiding semantics or to which views are registered — those are alternative designs raised in the thread, not part of restoring startup totality.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (confirmed/open; root cause verified on target branch; reproduces; localized behavioural fix).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (2 advisory)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: 7 new failure(s) not in baseline: gramps.plugins.test.imports_test.TestImports::test_imp_3_4
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 8796 / viewmanager-empty-views-indexerror (iteration 4)

> Advisory, artifact-only, decorrelated. Inputs: patch.diff, brief.md, check-gates.json
> (build-notes.md withheld by design). Verdicts re-derived from the artifacts, not
> read off the builder's notes.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | brief.md:10 states a concrete, falsifiable success criterion (zero available views → init interface raises nothing, opens with no active page) + an explicit totality invariant (brief.md:11). Scope/out-of-scope are bounded (brief.md:14). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Red confirmed: check-gates `C4-verify: red-without-fix=PASS`. Re-derived: pre-fix `views_to_show([])` returns `(0,0,[])` (old body, patch.diff:147-170), so `assertEqual(...,(None,None,[]))` (patch.diff:66,70) fails. Caveat: it asserts the *causal return value*, not the literal `IndexError` the success criterion names — the real-path IndexError repro is absent (routed to T5/V). |
| C3 — C3 Change | PASS | Single coherent change: extract `views_to_show` to GTK-free `viewmanagerutils.py` (patch.diff:228-268), re-import + drop in-file copy (patch.diff:83,143-170), guard navigation in `init_interface` (patch.diff:100-106), retain `__change_page`/`config_view` guards (patch.diff:114-121,130-135). No circular import (viewmanagerutils pulls only `gramps.gen.config`). Empty-set path is the only behavioural change; non-empty path byte-identical → minimal per §1.1. |
| C4 — C4 Verification (red→green) | PASS | Gating row green: check-gates `C4-verify: green-with-fix=PASS / red-without-fix=PASS`, `overall: pass`. Re-derived both directions on `views_to_show([])`: `(0,0,[])`→red, `(None,None,[])`→green. Both `use_last=False` and `use_last=True` cases hold (guard precedes the `if use_last` block, patch.diff:241-247). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause (`views_to_show([])` collapsing to `(0,0,[])`) is fixed by construction (patch.diff:241-247) + non-navigation guard — satisfies the iter-2/iter-3 by-construction directive. But two downstream guards are *retained* with reachability claims (`__change_page` via `_post_load_newdb_gui` viewmanager.py:1221 → `get_current_page()==-1`; `config_view` via action viewmanager.py:528) that artifact-only Check cannot verify against source. Keep-vs-remove (symptom-vs-by-construction) and reachability are a human call per the brief's C5 oracle. |
| T1 — T1 Structure | N/A | Core-only change; no addons-source path in patch.diff. §Structure is addon-only (matches check-gates T1-structure path_line). |
| T2 — T2 Shape | PASS | GPL header present on both new files (patch.diff:7-24, 182-202); check-gates `T2 ✓ shape: 1 file(s) conform … (2 advisory)`. No `print()` introduced. |
| T3 — T3 Runtime | NEEDS-HUMAN | Both advisory runtime gates FAIL: 7 new unit deltas (`imports_test::test_imp_3_4`, check-gates T3-unit) + 1 GUI-smoke delta (check-gates T3-interface). This patch carries **no** sys.modules stubbing / subprocess harness (cf. iter-1 leak), yet the same deltas persist byte-for-byte — corroborating the iter-1/2/3 environmental attribution (missing bsddb backend / Glade dirname / stale baseline). Artifact-only Check cannot confirm the attribution; human must accept these as environmental, not patch-induced. |
| T4 — T4 Contribution | N/A | No commit-msg.txt / pr-description.md in the bundle (draft-only per STOP discipline); matches check-gates T4-contribution path_line. |
| T5 — T5 Judgment | NEEDS-HUMAN | The clean unit test of the production `views_to_show` satisfies iter-3 ask #1, and reuses the real function (not a parallel re-impl, §3.4). But iter-3 ask #2 — a dogtail interface test driving the **real** `init_interface` entry, doubling as automated V — is undelivered. No automated test exercises `init_interface`→`goto_page` end-to-end, so the literal startup `IndexError` the success criterion names is never reproduced by CI. Whether the function-level test alone is sufficient gating coverage is a human judgment. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Manual GUI repro (hide every view plugin on maintenance/gramps61, restart, confirm no IndexError + app opens with no active page) is recorded unrun across iter-1/2/3 (brief.md:28,35,42) and no automated dogtail substitute ships this iteration. Always-human; must be run and accepted before sign-off. |

## §6 — items the human must clear (NEEDS-HUMAN)

1. **C5 — causal adequacy / retained guards.** Confirm the two downstream guards
   (`__change_page` patch.diff:114-121, `config_view` patch.diff:130-135) are
   genuinely reachable on the empty-view set independently of `init_interface`
   (the recorded entry points: `_post_load_newdb_gui` → `__change_page(get_current_page()==-1)`
   at viewmanager.py:1221; the ConfigView accelerator at viewmanager.py:528). If
   reachable, retention is justified; if not, iter-2's by-construction directive
   asks for their removal. Reachability is asserted in comments but unverifiable from
   the artifacts alone.

2. **T3 — advisory runtime reds.** Accept (or reject) the attribution that the 7 unit
   deltas + 1 smoke delta are environmental and not caused by this patch. Supporting
   evidence re-derived here: this iteration removed the sys.modules stubbing that was
   the suspected iter-1 leak, yet the deltas persist unchanged — consistent with a
   stale baseline / missing backend rather than the patch. Confirmation needs the
   build/run environment, which is outside the Check bundle.

3. **T5 — test coverage judgment.** Decide whether the function-level
   `views_to_show([])` unit test is adequate gating coverage given the absence of the
   iter-3-requested real-entry (dogtail) test. The shipped test never drives
   `init_interface`/`goto_page`, so the actual startup `IndexError` and the no-active-page
   end state are not asserted by any automated test.

4. **V — fitness-to-purpose.** Run the manual GUI repro on maintenance/gramps61 and
   confirm: no `IndexError` at startup, main window opens with no active page. Unrun to
   date; with no automated dogtail test landing this iteration, manual validation is the
   only V evidence available and must precede release.

## Reviewer note (advisory, non-gating)

C2/C4 are GREEN at the unit level and the source fix is minimal and well-targeted. The
open risk is **coverage altitude**, not the fix logic: every iteration's gating
regression has stopped at the `views_to_show` return value, while the success
criterion (brief.md:10) and iter-3's directive both call for a test that drives the
real navigation path and observes the `IndexError` going away. Until that test exists
or V is run manually, "no startup crash" is verified only by inference from the
function's return value, not by exercising the crash site (`goto_page`
`self.current_views[cat_num]=view_num`).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Root cause (`views_to_show([])` collapsing to `(0,0,[])`) is fixed by construction (patch.diff:241-247) + non-navigation guard — satisfies the iter-2/iter-3 by-construction directive. But two downstream guards are *retained* with reachability claims (`__change_page` via `_post_load_newdb_gui` viewmanager.py:1221 → `get_current_page()==-1`; `config_view` via action viewmanager.py:528) that artifact-only Check cannot verify against source. Keep-vs-remove (symptom-vs-by-construction) and reachability are a human call per the brief's C5 oracle.
- [x] T3 — T3 Runtime — Both advisory runtime gates FAIL: 7 new unit deltas (`imports_test::test_imp_3_4`, check-gates T3-unit) + 1 GUI-smoke delta (check-gates T3-interface). This patch carries **no** sys.modules stubbing / subprocess harness (cf. iter-1 leak), yet the same deltas persist byte-for-byte — corroborating the iter-1/2/3 environmental attribution (missing bsddb backend / Glade dirname / stale baseline). Artifact-only Check cannot confirm the attribution; human must accept these as environmental, not patch-induced.
- [x] T5 — T5 Judgment — The clean unit test of the production `views_to_show` satisfies iter-3 ask #1, and reuses the real function (not a parallel re-impl, §3.4). But iter-3 ask #2 — a dogtail interface test driving the **real** `init_interface` entry, doubling as automated V — is undelivered. No automated test exercises `init_interface`→`goto_page` end-to-end, so the literal startup `IndexError` the success criterion names is never reproduced by CI. Whether the function-level test alone is sufficient gating coverage is a human judgment.
- [x] V — Validation — fitness-to-purpose — Manual GUI repro (hide every view plugin on maintenance/gramps61, restart, confirm no IndexError + app opens with no active page) is recorded unrun across iter-1/2/3 (brief.md:28,35,42) and no automated dogtail substitute ships this iteration. Always-human; must be run and accepted before sign-off.

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
- By / date: Eduard Ralph / 2026-06-08

## 10. Act candidates (hints for the next Act review)
- This cycle exposed T3-mechanism masking risks (subtree-collapse blind spot in
  `t3_baseline.classify()`, unpinned substrate, unguarded `--update`) and a
  `merged-wider`-vs-upstream gap on the glade-setattr / headless-ut-segfault fixes.
  Recorded as candidates in `process/act-log.md` (Act review 2026-06-09). Also: the
  iterate-to-Do loop here was structural (all-human/environmental §6 routed back to Do).
