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
> `brief.md`, `check-gates.json` (build-notes.md withheld by design). Every Basis
> below is re-derived from those artifacts, not copied from the gate text.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Brief carries a concrete, load-bearing success criterion (`brief.md:10`: empty available-view set → init without raising, opens with no active page; red→green contract stated) and an explicit totality invariant (`brief.md:11`). Spec is well-formed and testable. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Test drives the **real** `views_to_show` / `init_interface` / `__change_page` / `config_view` on the genuine `gramps.gui.viewmanager` module (`patch.diff:218-253`); `check-gates.json` `C4-verify` records `red-without-fix=PASS`. Caveat: red is demonstrated with the test file run in isolation, not under whole-suite discovery (see C4/T3). |
| C3 — C3 Change | PASS | Source-level fix: `views_to_show` returns `(None, None, [])` for the empty set (`patch.diff:58-65`); `init_interface` unpacks the 3-tuple and only navigates when `current_cat is not None` (`patch.diff:11-24`). Non-empty path is byte-equivalent to the prior `defaults[0/1/2]` unpack. Citations present in-comment; diff is clean and localized. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` `C4-verify`: `green-with-fix=PASS / red-without-fix=PASS` (gating row, the only one). BUT this is the narrow mechanical green — it runs the new file alone. The whole-suite signal (T3) **contradicts** it with a non-empty regression delta, so C4-green ≠ "change is clean under the suite." |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Always-human (contested root-cause). The root-cause *approach* was rejected twice: iter-1 (test leaks into shared suite) and iter-2 (use a by-construction upstream fix, not site-local downstream guards). This patch is a hybrid — it fixes the source (`views_to_show` `patch.diff:58-65`) but **retains 2 of 3 downstream guards** (`__change_page` `patch.diff:32-38`, `config_view` `patch.diff:47-50`) instead of demonstrating their unreachability post-fix. Whether that satisfies the iter-1 ask ("prove `__change_page` unreachable or guard it") and the iter-2 ask (by-construction totality) is a human judgment. |
| T1 — T1 Structure | N/A | Core-only change (`gramps/gui/viewmanager.py` + `gramps/gui/test/viewmanager_test.py`); no addons-source path in `patch.diff`. §Structure (doc 16) is addon-only. Matches gate `T1-structure`. |
| T2 — T2 Shape | PASS | New test file carries the GPL header (`patch.diff:75-92`); only advisory is `print("REPRO_OK")` in the child program (`patch.diff:253`), which is the test's pass-marker, not production output. Matches gate `T2-shape` (1 conform, 2 advisory). |
| T3 — T3 Runtime | FAIL | `check-gates.json` records **both** runtime rows `fail`: `T3-unit` DELTA 7 new failures (`imports_test::test_imp_3_4`) and `T3-interface` DELTA 1 new failure (`SmokeTest setUpClass`) — **byte-identical to the iter-1 and iter-2 carry-forwards** (`brief.md:29-30, 36-37`). The rewritten subprocess-per-scenario harness prevents `sys.modules` leakage but not disk side-effects from importing real `gramps.*` in the child (plugin/config cache under the gramps home), nor a stale/environmental baseline — an identical delta surviving a fully rewritten test points at one of those. iter-2's explicit "Confirm T3 is green against the new patch" is **unmet**. Advisory (gating:false), but it is the exact basis on which both prior iterations were rejected. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle. Matches gate `T4-contribution`. |
| T5 — T5 Judgment | NEEDS-HUMAN | Reviewer+human. Test drives production methods (good) but still **reconstructs the post-`__init__` state via `ViewManager.__new__` + hand-set attributes** (`patch.diff:193-215`) and stubs `__build_tools_menu`/`__build_report_menu` — exactly the "reconstructed-`__new__`-input drift surface" iter-2 T5 asked to shrink by moving toward the real `init_interface` entry point. That ask appears unaddressed; subprocess-per-scenario is heavy. Test-design fitness is a judgment call. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. The manual GUI repro on `maintenance/gramps61` (hide every view plugin, restart, confirm no `IndexError`, app opens with no active page) was unrun in iter-1 and iter-2 (`brief.md:28, 35`) and there is no artifact evidencing it was run for this iteration. Must be run and accepted before release. |

## §6 — items the human must clear

1. **C5 — contested root-cause / scope.** Decide whether the hybrid (source fix in
   `views_to_show` + `init_interface` guard, but retained `__change_page` and
   `config_view` downstream guards) satisfies the iter-2 "by-construction, total
   over the empty set" directive, or whether the two remaining guards must be shown
   unreachable post-fix and removed. (`patch.diff:32-38`, `:47-50`.)
2. **T5 — test-design judgment.** Accept or reject the `__new__`-reconstructed
   ViewManager + subprocess harness given iter-2's request to move the regression
   toward the real `init_interface` entry and shrink the reconstruction drift
   surface (`patch.diff:193-215`).
3. **V — manual GUI validation unrun.** Execute the brief's repro and confirm the
   no-active-page outcome before sign-off.

## Blocking flag (not a §6 human-judgment item — a re-run/diagnosis task)

- **T3 is RED and identical to both rejected iterations.** Overall gate reads
  `pass` only because T3 is advisory and C4 (isolation-only) is the lone gating row
  — but T3 is the precise basis on which iter-1 and iter-2 were rejected, and the
  carry-forward set "confirm T3 green" as a release precondition. The byte-identical
  delta across three different test implementations suggests the failures are **not
  prevented by the subprocess `sys.modules` isolation** — re-derive whether they are
  a filesystem/cache side-effect of importing real `gramps.*` in the child, a stale
  gate artifact, or a contaminated/flaky baseline, before treating this as
  releasable. As it stands, the artifacts do **not** show a clean whole-suite run.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C5 — C5 Causal adequacy — Always-human (contested root-cause). The root-cause *approach* was rejected twice: iter-1 (test leaks into shared suite) and iter-2 (use a by-construction upstream fix, not site-local downstream guards). This patch is a hybrid — it fixes the source (`views_to_show` `patch.diff:58-65`) but **retains 2 of 3 downstream guards** (`__change_page` `patch.diff:32-38`, `config_view` `patch.diff:47-50`) instead of demonstrating their unreachability post-fix. Whether that satisfies the iter-1 ask ("prove `__change_page` unreachable or guard it") and the iter-2 ask (by-construction totality) is a human judgment.
- [ ] T5 — T5 Judgment — Reviewer+human. Test drives production methods (good) but still **reconstructs the post-`__init__` state via `ViewManager.__new__` + hand-set attributes** (`patch.diff:193-215`) and stubs `__build_tools_menu`/`__build_report_menu` — exactly the "reconstructed-`__new__`-input drift surface" iter-2 T5 asked to shrink by moving toward the real `init_interface` entry point. That ask appears unaddressed; subprocess-per-scenario is heavy. Test-design fitness is a judgment call.
- [ ] V — Validation — fitness-to-purpose — Always-human. The manual GUI repro on `maintenance/gramps61` (hide every view plugin, restart, confirm no `IndexError`, app opens with no active page) was unrun in iter-1 and iter-2 (`brief.md:28, 35`) and there is no artifact evidencing it was run for this iteration. Must be run and accepted before release.

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
- Iteration delta (if iterating): Why rejected (issue_8796): the fix logic is accepted (keep views_to_show([]) -> (None, None, []) and the init_interface `if current_cat is not None` guard), but the test design and validation are not. T5: the regression still fabricates a ViewManager via __new__ + ~15 hand-set attributes and ~20 stubbed gramps.gui modules in a subprocess harness (patch.diff:188-215) — the leak from iter-1 is solved, but iter-2's ask to shrink the reconstruction drift surface / move toward the real init_interface entry is unmet. V: the manual GUI repro is still unrun. What to change next (Do): - Keep a CLEAN unit test of the source fix as the C4 gating regression: call the real module-level views_to_show([], use_last=False) and assert (None, None, []). No GTK stubbing, no __new__ reconstruction. This alone carries C4 red->green. - Replace the heavy __new__-reconstructed init_interface/__change_page/config_view subprocess scenarios with a dogtail interface test under engine/interface/ (subclass GrampsInterfaceTestCase): seed [plugin] hiddenplugins with every view plugin (via LAUNCH_ENV GRAMPSHOME->prepared gramps.ini, or LAUNCH_CONFIG -c), set TREE_REQUIRED=False (precedent: test_bug_0014100), launch real gramps, assert the window appears with NO active page. Pre-fix this crashes/times out (red); post-fix it opens cleanly (green). This drives the REAL init_interface entry (no reconstruction drift) and doubles as automated V — so V is no longer "unrun". Note: the dogtail test lands in the advisory T3-interface gate, not C4 — that is why the clean views_to_show unit test is still needed for the gating row. - C5: with the real-entry dogtail test in hand, decide the two retained downstream guards (__change_page patch.diff:32-38, config_view :47-50) per iter-2's by-construction directive — prefer demonstrating they are unreachable once init_interface no longer navigates on the empty set and removing them, or keep only the one(s) shown still reachable, with the reachability evidence recorded. - Do NOT chase the T3 reds: confirmed this cycle to be environmental, not this patch — interface = Glade _Glade__dirname (testbed #1, now fixed on essential branch + PR #2356); unit = 5x missing-bsddb backend + 2x web-report, unmasked by the segfault fix and stale-baselined (tracked eduralph/gramps#15). A clean whole-suite delta is not required of this patch.
- By / date: Eduard Ralph / 2026-06-08

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
- issue_8796: run-unit.json baseline is stale — it recorded the headless discovery segfault; now that the segfault fix unmasks the suite, 7 pre-existing reds (5× missing-bsddb, 2× web-report) surface as a delta. Refresh the baseline / add a bsddb-availability skip-guard (see eduralph/gramps#15).
- issue_8796: t3_baseline.py classify() reports a per-test id as a delta even when a run_level_signature already documents that red (interface _ErrorHolder/_Glade__dirname read as "delta" not "baseline") — consult signatures before flagging per-test new failures, or record the per-test id in known_failures.
