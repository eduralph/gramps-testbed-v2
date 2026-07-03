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
