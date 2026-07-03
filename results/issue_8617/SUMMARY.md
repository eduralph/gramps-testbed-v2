# Result — issue 8617 / bottombar-filter-gramplet-ignored

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The Filter gramplet filters the list view only while the sidebar filter is
- Success criterion: After the fix, applying a filter from the Filter gramplet in the
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: In `ListView.build_tree`, the choice between the gramplet's `generic_filter`

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): pass — C4-verify-interface: green-with-fix=PASS / red-without-fix=PASS
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: restore Bottombar Filter gramplet filtering so a set `view.generic_filter` is applied even when the sidebar is hidden and the Search bar is visible.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect, success criterion, invariant, scope, and repro target for issue 8617 (`brief.md:5`, `brief.md:12`, `brief.md:17`, `brief.md:26`, `brief.md:34`). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | DECISION OWED: the static pre-fix path is present in the target (`gramps/gui/views/listview.py:335`, `gramps/gui/views/listview.py:786`), but the promised AT-SPI repro is withheld/not runnable here (`brief.md:38`, `check-gates.json:15`). |
| C3 — C3 Change | PASS | The diff changes both filter-selection sites so `generic_filter` wins when set, covering initial rebuild and sort-triggered model rebuild (`patch.diff:9`, `patch.diff:19`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: `git apply --check /tmp/pdca-review-d5tot6_v/patch.diff` passed on `$PDCA_TARGET`, but no local red-green runner or repro file is available here (`brief.md:38`, `check-gates.json:33`, `check-gates.json:42`). |
| C5 — C5 Causal adequacy | PASS | The gramplet stores the filter then calls `build_tree` (`gramps/plugins/gramplet/filter.py:76`), while `build_tree` passes only `filter_info` into the model (`gramps/gui/views/listview.py:354`, `gramps/gui/views/listview.py:361`); the patch changes exactly the branch that was dropping `generic_filter` when the Search bar was visible (`patch.diff:9`). |
| T1 — T1 Structure | N/A | No addon structure is touched; `patch.diff` modifies only `gramps/gui/views/listview.py` (`patch.diff:1`). |
| T2 — T2 Shape | PASS | The patch is a local boolean-condition change in an existing GPL-covered source file and adds no new files, imports, strings, or formatting pattern (`patch.diff:1`, `patch.diff:9`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: gate output reports runtime runners failing before usable JUnit output, which is an infrastructure/runner state to clear rather than source evidence from this two-line patch (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message, PR description, or contribution wrapper is present in the artifact bundle, and no contribution-surface file is changed (`check-gates.json:105`, `patch.diff:1`). |
| T5 — T5 Judgment | PASS | The change is narrowly scoped to the two shared `ListView` filter-selection paths, matching the brief's all-`ListView` invariant rather than special-casing one view (`brief.md:21`, `patch.diff:5`, `patch.diff:14`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: final fitness depends on a human/user-visible GUI check that Bottombar filtering behaves as intended and that Search-bar precedence remains acceptable under the out-of-scope combination case (`brief.md:12`, `brief.md:30`). |

## §6 Human Decisions Owed

1. C2 red reproduction: confirm the pre-fix GUI defect with the stated manual path or the withheld AT-SPI test. Manual steps: on `maintenance/gramps61`, open People view, add the Filter gramplet to the Bottombar, hide the sidebar from the View menu, enter/select a filter in the gramplet, press Find, and confirm rows remain unchanged before the patch.
2. C4 red-to-green verification: rerun the committed interface repro in an environment with the testbed available. Expected result: unpatched tree red with unchanged visible rows; patched tree green with reduced visible rows. I verified only that the patch applies cleanly to `$PDCA_TARGET`.
3. T3 runtime: clear the runner state that produced no JUnit XML for unit/interface baselines, then decide whether any remaining runtime failures are attributable to this patch.
4. V fitness-to-purpose: decide whether the restored precedence, `generic_filter` over Search-bar value when set, is the desired user-visible behavior for this fix, given the brief explicitly defers combined Search-bar text plus gramplet-filter design.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C2 — C2 Reproduction (red pre-fix) — cleared: interface gate ran red-without-fix=PASS on unpatched tree, confirming the pre-fix defect.
- [x] C4 — C4 Verification (red→green) — cleared: interface gate ran green-with-fix=PASS / red-without-fix=PASS.
- [x] T3 — T3 Runtime — cleared: runner failure was a known environment issue, not attributable to this patch.
- [x] V — Validation — fitness-to-purpose — cleared by human: generic_filter precedence over Search bar when set is the intended behaviour; combined case remains out of scope per brief.
- [x] C4 fix verified: test red pre-fix, green post-fix — cleared: interface oracle (C4-verify-interface PASS) is the appropriate vehicle for this GUI-layer change; no headless unit test is meaningful here.

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
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
