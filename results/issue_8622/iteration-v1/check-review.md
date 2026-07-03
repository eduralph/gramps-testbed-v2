Reviewing issue 8622: searched "Select Source or Citation" results must keep existing citation children reachable under matched source rows.

Target caveat: `$PDCA_TARGET` is readable but on `master` (`aef9f35ec6`) rather than the brief's `maintenance/gramps61`; the Python hunks apply cleanly, but `po/POTFILES.skip` context is stale, so changed-line citations below are grounded on `patch.diff` where necessary.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines the defect and success criterion: search currently hides citation children and must keep them expandable/selectable under a matched source (`brief.md:6`, `brief.md:12`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The unpatched target builds independent primary/secondary text filters from the same column/text, which reproduces the child-drop condition for source-title searches (`/home/eddie/gramps/gramps/gramps/gui/views/treemodels/treebasemodel.py:471`). |
| C3 — C3 Change | PASS | The patch scopes the behavior to the citation selector by adding selector model kwargs and passing `match_child_via_parent=True`, while default model behavior remains opt-in (`patch.diff:20`, `patch.diff:36`, `patch.diff:102`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: in a correctly provisioned Gramps 6.1 lane, confirm the new focused test runs red before and green after; local run reached import setup but aborted on GTK/API environment mismatch (`Gtk.IconSize.MENU`) before assertions. |
| C5 — C5 Causal adequacy | PASS | The wrapper retains a citation if either the citation filter matches or the parent source filter matches, directly addressing the same-column secondary-filter cause (`patch.diff:80`, `patch.diff:137`). |
| T1 — T1 Structure | N/A | Core-only change with no addon layout surface, matching the gate's N/A assessment (`check-gates.json:60`). |
| T2 — T2 Shape | PASS | Added Python test has GPL header and the new core test is registered in `POTFILES.skip`; `git diff --check` on the patched temp clone produced no whitespace errors (`patch.diff:153`, `patch.diff:375`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: runtime health must be judged in a valid lane because configured unit/interface gates failed before producing JUnit, and my focused retry was blocked by local GTK/resource setup rather than a test assertion (`check-gates.json:87`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this review bundle, so contribution-wrapper review does not apply (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: accept whether the selector-only opt-in is the right product boundary, since the brief calls the selector-vs-shared-model locus a judgment call and the patch intentionally preserves standalone tree-view search semantics (`brief.md:35`, `patch.diff:187`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must validate the actual GUI workflow preserves the intended user outcome: after searching, an existing citation can be selected rather than forcing new citation creation (`brief.md:12`). |

## §6 Human Clearance Items

1. C4: On a correct `maintenance/gramps61` lane, apply the patch and run `python3 -m unittest gramps.gui.views.treemodels.test.citationtreemodel_search_test`; clear only if the new selector test fails on the unpatched baseline and passes with the patch.
2. T3: Rerun the configured core unit and GUI smoke gates in a provisioned lane; clear only if failures are unrelated baseline/tooling failures or the patched tree-model path passes.
3. T5: Decide whether selector-only `match_child_via_parent=True` is the intended scope, leaving standalone Citation Tree View searches unchanged.
4. V: Manually exercise Gramps: open a person, go to Source Citations, choose Add Existing Citation, search for a source, expand the matched source, and confirm an existing citation child is selectable and added without creating a new citation.
