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

# Check review — issue 8796 / viewmanager-empty-views-indexerror

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json` (build-notes.md deliberately withheld; no gramps
> checkout available, so line anchors are taken from the brief/patch, not
> re-confirmed against the target branch). Every Basis was re-derived here.

## Headline

The fix logic is minimal and correct for the **startup** crash: `goto_page` gains
an early `if not self.views: return None` guard (patch.diff:191–198) and
`config_view` gains an `if self.active_page is None: return` guard
(patch.diff:206–209). The regression test passes in isolation (C4-verify gate =
PASS). **But** the test performs global `sys.modules` mutation at *module import
time* with no teardown (patch.diff:117 → `_install_import_stubs()` calling
`sys.modules.setdefault(...)` for `gi`, `gramps.repository`, ~20 `gramps.gui.*`
modules, `gramps.cli.grampscli`, `gramps.gui.managedwindow`). Under
`unittest discover -p "*_test.py"` (one shared process), `gramps.gui.test.viewmanager_test`
sorts before `gramps.plugins.test.imports_test`, so its mocks leak into later
tests — the most likely cause of the T3 delta **7 new unit failures** (e.g.
`imports_test::test_imp_3_4`). C4 ran the file in isolation and is clean; the
whole-suite run is not. This is the central concern for sign-off.

## Verdict matrix (5/5/1)

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:10 states a falsifiable success criterion (empty available-view set → init without raising) and brief.md:11 a sourced totality invariant; scope/out-of-scope are explicit (brief.md:14). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix `goto_page(0,0)` with `current_views=[]` reaches `self.current_views[cat_num]=view_num` (brief.md:9, :927) → IndexError; corroborated by gate C4-verify `red-without-fix=PASS` (check-gates.json:37). |
| C3 — C3 Change | PASS | Localized two-hunk guard to `gramps/gui/viewmanager.py` (patch.diff:191–198, 206–209) + new test; no collateral edits — matches §1.1 minimal-delta (principles.md:24). |
| C4 — C4 Verification (red→green) | PASS | Gating gate C4-verify = PASS: `green-with-fix=PASS / red-without-fix=PASS` (check-gates.json:33–39). Caveat: this is an **isolated** file run; see T3 for the whole-suite contradiction. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause (empty-list indexing) is sound and the immediate crash site is guarded, but brief.md:14 puts the `__change_page` (:1049–1051) cascade *in scope* and the patch guards only `goto_page`/`config_view` — `__change_page` is unguarded. Whether it is reachable once `goto_page` returns early (no page added → no switch-page signal) cannot be settled from artifacts. Contested completeness → human. |
| T1 — T1 Structure | PASS | New test is `gramps/gui/test/viewmanager_test.py` — core `test/` (singular) package + `<module>_test.py` suffix per INTEGRATION.md:104–113; addon §Structure is N/A (no addons-source path), consistent with gate T1 (check-gates.json:55). |
| T2 — T2 Shape | PASS | New file carries the GPL header (patch.diff:7–24); no `print()` in the diff; matches gate T2 `1 file conform … (2 advisory)` (check-gates.json:64). |
| T3 — T3 Runtime | FAIL | Gate reports 7 new unit failures (e.g. `imports_test::test_imp_3_4`) + 1 new GUI-smoke failure not in baseline (check-gates.json:73, :82). Independently derived likely cause: the test's import-time global `sys.modules` mutation with no teardown (patch.diff:117, 58–110) leaks mocks across the shared `unittest discover` process. Non-gating per config, but a real regression signal. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle to evaluate against doc 16 §Commit/§Contributor (check-gates.json:91); nothing to check. |
| T5 — T5 Judgment | NEEDS-HUMAN | Fix code is clean/minimal/well-commented, but the test's global-state mutation without setUp/tearDown isolation (patch.diff:58–117) is a quality defect that the C4-in-isolation pass masks; whether it blocks sign-off as-is is a human judgment. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | The only end-to-end confirmation (restart after hiding every view plugin → no crash, opens with no active page; brief.md:13,15) is a manual GUI repro that cannot be automated in this harness. Human must run/accept it. |

## §6 — Items the human must clear (each NEEDS-HUMAN / FAIL above)

1. **C5 causal completeness — the `__change_page` cascade.** brief.md:14 names
   `__change_page` (:1049–1051) as part of the in-scope failure set, but the
   patch does not guard it. Confirm on the target branch whether `__change_page`
   is reachable with zero views once `goto_page` returns early (it likely is not,
   since no notebook page is added → no switch-page signal), or whether it needs
   its own guard. If unreachable, record why; if reachable, the fix is incomplete.

2. **T3 / T5 — test contaminates the shared suite (root finding).** The test calls
   `_install_import_stubs()` at module top-level (patch.diff:117), which does
   `sys.modules.setdefault(...)` for `gi`, `gramps.repository`, the `gramps.gui.*`
   tree, `gramps.cli.grampscli`, and `gramps.gui.managedwindow` (patch.diff:73–110)
   and never restores them. `unittest discover` imports all `*_test.py` in one
   process and `gramps.gui.test.viewmanager_test` sorts before
   `gramps.plugins.test.imports_test`, so the mocks persist into later tests — the
   most plausible cause of the 7 new unit failures (check-gates.json:73). C4-verify
   is green only because it runs the file in isolation. Human action: confirm the
   T3 deltas trace to this leak, and require the stubbing be confined (setUp/
   tearDown with `sys.modules` snapshot-restore, or a subprocess/`importlib`
   sandbox) before sign-off. Also confirm the separate GUI-smoke delta
   (check-gates.json:82) is pre-existing vs. introduced.

3. **V — manual GUI validation.** Run brief.md:15 repro on `maintenance/gramps61`
   (hide every view plugin, restart) and confirm Gramps opens with no active page
   and no `IndexError`. This fitness-to-purpose check is human-only.

## Note on the guard predicate (advisory, not a gate)

`goto_page` guards on `self.views` (patch.diff:191) while the actual IndexError is
on `self.current_views[cat_num]` (brief.md:9). These are empty together in the
modelled startup path (`views_to_show([]) → (0,0,[])`, brief.md:9), so the proxy
is correct for the reported defect. If a future caller could leave `current_views`
shorter than `views`, the guard would miss it; a `cat_num >= len(self.current_views)`
check would bound the exact failing operation. Not required by the brief's scope.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C5 — C5 Causal adequacy — Root cause (empty-list indexing) is sound and the immediate crash site is guarded, but brief.md:14 puts the `__change_page` (:1049–1051) cascade *in scope* and the patch guards only `goto_page`/`config_view` — `__change_page` is unguarded. Whether it is reachable once `goto_page` returns early (no page added → no switch-page signal) cannot be settled from artifacts. Contested completeness → human.
- [ ] T5 — T5 Judgment — Fix code is clean/minimal/well-commented, but the test's global-state mutation without setUp/tearDown isolation (patch.diff:58–117) is a quality defect that the C4-in-isolation pass masks; whether it blocks sign-off as-is is a human judgment.
- [ ] V — Validation — fitness-to-purpose — The only end-to-end confirmation (restart after hiding every view plugin → no crash, opens with no active page; brief.md:13,15) is a manual GUI repro that cannot be automated in this harness. Human must run/accept it.

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
- Iteration delta (if iterating): Rejected (issue_8796): the regression test regresses the shared unit suite. The fix logic (goto_page `if not self.views: return None`; config_view `if self.active_page is None: return`) is accepted as minimal and correct — keep it. What to change next (Do): - Confine the test's import stubbing. `_install_import_stubs()` mutates global `sys.modules` at module-import time with no restore (patch.diff:58–117), and under `unittest discover` (one shared process) those mocks leak into later tests — the cause of the T3 delta (7 new unit failures, e.g. imports_test::test_imp_3_4, + 1 GUI-smoke failure). C4 was green only because it ran the file in isolation. Snapshot/restore `sys.modules` in setUp/tearDown (or sandbox the import in a subprocess/importlib) so the whole-suite run shows no new failures. A change that introduces unit-test failures is not acceptable. - C5 must be settled before release: the brief puts the `__change_page` (:1049–1051) cascade in scope but the patch guards only goto_page/config_view. Either demonstrate `__change_page` is unreachable once goto_page returns early (no page added → no switch-page signal) and record why, or add its guard. - V (manual GUI repro on maintenance/gramps61: hide every view plugin, restart, confirm no IndexError, opens with no active page) still needs to be run/accepted before release.
- By / date: Eduard Ralph / 2026-06-08

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
