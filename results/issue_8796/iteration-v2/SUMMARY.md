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

# Check review — issue_8796 / viewmanager-empty-views-indexerror (iteration 2)

Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(`build-notes.md` withheld by design). Basis re-derived from the artifacts; the target-branch
source is outside my reachable dirs, so `viewmanager.py` anchors are re-derived from the patch
hunks + brief, not read on the branch.

## Verdict matrix (5 / 5 / 1)

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Brief is complete and testable: defect, load-bearing success criterion (`brief.md:10`), invariant (`:11`), in/out-of-scope split (`:14`), repro and test-file fields all present and self-consistent. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Test drives the **production** `goto_page` on the empty-view state (`patch.diff:184–189`); `check-gates.json:37` C4-verify `red-without-fix=PASS` confirms it raises the `IndexError` pre-fix — a genuine reproduction, not a stub. |
| C3 — C3 Change | PASS | Three localized totality guards added at exactly the three cascade sites the brief names: `goto_page` `if not self.views: return None` (`patch.diff:240`), `__change_page` `if not self.pages: return` (`patch.diff:255`), `config_view` `if self.active_page is None: return` (`patch.diff:270`). |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json:33–39` C4-verify gating gate green: `green-with-fix=PASS / red-without-fix=PASS`. Caveat: the C4 runner exercises the file **in isolation** (`run-verify.sh`), so it cannot see the whole-suite contamination that T3 reports — green C4 + red T3 is the known iter-1 pattern, not a contradiction. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Iter-1 gap is closed — `__change_page` is now guarded too (`patch.diff:255`), so all three brief-scope sites (goto_page `:927`, `__change_page` `:1049-1051`, config_view `:1501`) are covered and the state resolves to "no active page" per the invariant (`brief.md:11`). But three site-local symptom guards vs removing the upstream cause (init_interface navigating with zero views / `views_to_show` collapsing) is a §3.3 mechanism judgment; oracle is reviewer+human (`check-gates.json:46`). Advisory read: adequate to the stated invariant. |
| T1 — T1 Structure | N/A | Core-only change; no addons-source path in the patch, and doc 16 §Structure is addon-only (`check-gates.json:55`). |
| T2 — T2 Shape | PASS | New test file carries the GPL v2-or-later header (`patch.diff:7–24`); gate `T2 ✓` with 2 advisories, no `print()` in the diff (`check-gates.json:64`). |
| T3 — T3 Runtime | FAIL | Both runtime sub-gates red with deltas **byte-identical to iter-1**: unit suite `DELTA: 7 new failure(s)` incl. `imports_test::test_imp_3_4` (`check-gates.json:73`) and GUI smoke `DELTA: 1 new failure` `test_smoke.SmokeTest` (`check-gates.json:82`). The `mock.patch.dict` scoping in setUp/tearDownClass (`patch.diff:132–148`) restores the sys.modules *mapping* but not side effects on already-imported real modules mutated during the in-window import — a patch.dict-immune leak path consistent with the recurring `imports_test` failure. Advisory but a shared-suite regression is not acceptable per iter-1 sign-off. Re-run required to confirm leak-persists vs stale-gate (see §6). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` / `pr-description.md` in the bundle (`check-gates.json:91`). |
| T5 — T5 Judgment | NEEDS-HUMAN | The test reconstructs a ViewManager via `__new__` + hand-set attributes (`patch.diff:159–167`) instead of calling the real `init_interface`, so it validates the production *functions* with reconstructed inputs — a drift surface if `init_interface`'s setup diverges from `_empty_view_manager`. Also ~20 GUI submodules stubbed (`patch.diff:91–117`). Craftsmanship/judgment call; oracle reviewer+human (`check-gates.json:98`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Manual GUI repro on `maintenance/gramps61` (hide every view plugin, restart, confirm no IndexError, app opens with no active page) is still unrun/unaccepted per the iter-1 carry-forward (`brief.md:28`); nothing in the bundle evidences it. Oracle human at sign-off (`check-gates.json:107`). |

## §6 — items a human must clear before sign-off

1. **T3 runtime regression (blocking-in-practice).** check-gates.json still reports the iter-1 deltas verbatim (7 unit + 1 smoke). The patch was rewritten specifically to kill these via `patch.dict` scoping. Re-run the whole unit suite + GUI smoke against *this* `patch.diff` to decide: (a) gate is stale → clears, or (b) the leak persists through a non-sys.modules side effect → the test isolation is still wrong (sandbox the import in a subprocess / `importlib` fresh interpreter rather than relying on `patch.dict`). Do not sign off while red.
2. **C5 causal adequacy / contested root-cause.** Confirm three site-local guards are the intended mechanism vs removing the upstream cause (init_interface unconditionally navigating with zero views). The cascade coverage is now complete; the open question is mechanism choice under §3.3, not coverage.
3. **T5 judgment — test fidelity.** Accept or reject driving the production functions through a hand-built `__new__` ViewManager rather than the real `init_interface` entry; weigh the drift risk against the impracticality of launching GTK headless.
4. **V validation — manual GUI repro.** Run the hide-all-views restart repro and confirm clean startup with no active page before release.

## Net

Fix logic (C1–C4) is sound and the iter-1 `__change_page` cascade gap is closed. **Not acceptable
for sign-off**: T3 is red with the same shared-suite regression that rejected iter-1, and four items
(C5, T5, V, plus the T3 re-run) require human resolution.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C5 — C5 Causal adequacy — Iter-1 gap is closed — `__change_page` is now guarded too (`patch.diff:255`), so all three brief-scope sites (goto_page `:927`, `__change_page` `:1049-1051`, config_view `:1501`) are covered and the state resolves to "no active page" per the invariant (`brief.md:11`). But three site-local symptom guards vs removing the upstream cause (init_interface navigating with zero views / `views_to_show` collapsing) is a §3.3 mechanism judgment; oracle is reviewer+human (`check-gates.json:46`). Advisory read: adequate to the stated invariant.
- [ ] T5 — T5 Judgment — The test reconstructs a ViewManager via `__new__` + hand-set attributes (`patch.diff:159–167`) instead of calling the real `init_interface`, so it validates the production *functions* with reconstructed inputs — a drift surface if `init_interface`'s setup diverges from `_empty_view_manager`. Also ~20 GUI submodules stubbed (`patch.diff:91–117`). Craftsmanship/judgment call; oracle reviewer+human (`check-gates.json:98`).
- [ ] V — Validation — fitness-to-purpose — Manual GUI repro on `maintenance/gramps61` (hide every view plugin, restart, confirm no IndexError, app opens with no active page) is still unrun/unaccepted per the iter-1 carry-forward (`brief.md:28`); nothing in the bundle evidences it. Oracle human at sign-off (`check-gates.json:107`).

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
- Iteration delta (if iterating): Rejected: the fix uses three site-local downstream guards (goto_page / __change_page / config_view). Per the human's principle — a fix that keeps future changes proof against the same bug is superior to symptom repair — fix the empty-view state upstream / by construction instead: have init_interface not navigate with zero available views and/or stop views_to_show([]) collapsing to (0,0,[]), so the whole navigation chain is total over the empty set rather than each consumer being guarded (and an (N+1)th consumer left to crash). T3 (7 unit + 1 smoke deltas, byte-identical to iter-1) is expected to resolve via the upstream redo: a source-level fix should not need the heavy ~20-module sys.modules stubbing + patch.dict isolation that is the suspected leak path. Confirm T3 is green against the new patch. T5: move the regression test toward the real init_interface entry point as the upstream fix allows, shrinking the reconstructed-__new__-input drift surface and the GUI stubbing. V: manual GUI repro on maintenance/gramps61 (hide every view plugin, restart, confirm no IndexError and app opens with no active page) still unrun — run and accept before release.
- By / date: Eduard Ralph / 2026-06-08

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
- issue_8796: codify a ruleset principle — prefer fixing an invalid state at its upstream source over guarding each downstream consumer; one source fix makes the whole chain total by construction, whereas N site-local guards leave the (N+1)th consumer to fail the same way (C5 mechanism choice).
- issue_8796 (generalized): a fix that keeps *future* changes proof against the same bug is superior to one that only repairs today's symptom — prefer making the invalid state unrepresentable / robust-by-construction so later code cannot reintroduce the defect. Weigh this future-proofing as a first-class factor in C5 mechanism judgment.
