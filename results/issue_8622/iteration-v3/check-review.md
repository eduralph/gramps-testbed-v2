Reviewing issue 8622: filtered "Select Source or Citation" searches must keep existing citation children reachable under any source retained by the selector search.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines the defect and success criterion as keeping citation children reachable under a matched source in the selector search, while preserving standalone tree-view behavior (`brief.md:6`, `brief.md:12`, `brief.md:31`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added test is constructed to fall back to pre-fix `CitationTreeModel` and fail on the semantic child-row assertion rather than on a missing symbol (`patch.diff:276`, `patch.diff:416`, `patch.diff:433`). |
| C3 — C3 Change | PASS | The patch routes only `SelectCitation` to `CitationTreeSelectorModel`, leaving the plain `CitationTreeModel` available for standalone views (`patch.diff:9`, `patch.diff:17`, `patch.diff:146`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: the automated C4 gate did not verify behavior because its runner refused a dirty/untracked lane (`check-gates.json:33`), and my temporary rerun was blocked by the available `$PDCA_TARGET` being `master` plus a GTK import mismatch before tests executed; human must rerun the focused red→green test on a clean `maintenance/gramps61` target to clear verification. |
| C5 — C5 Causal adequacy | PASS | The existing root cause is secondary search using the same column/text independently for citation rows (`gramps/gui/views/treemodels/treebasemodel.py:467`, `gramps/gui/views/treemodels/treebasemodel.py:472`, `gramps/gui/views/treemodels/treebasemodel.py:480`), and the patch groups selector search by source for both primary and secondary rows (`patch.diff:63`, `patch.diff:181`, `patch.diff:190`). |
| T1 — T1 Structure | N/A | Core-only patch; no addon structure is touched, matching the gate's N/A result (`check-gates.json:60`). |
| T2 — T2 Shape | PASS | The new test has the project GPL header and the new core Python test is registered in `po/POTFILES.skip` in the patch (`patch.diff:211`, `patch.diff:557`); target `master` has a different `POTFILES.skip` layout, so that hunk's local apply miss is target-state drift. |
| T3 — T3 Runtime | PASS | The configured broader runtime gates report the core unit baseline and GUI smoke as passing or baseline-matching, with noted baseline drift not attributed to this patch (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this check bundle, so contribution-wrapper review does not apply (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: the patch intentionally widens selector text search so a citation-page match exposes all sibling citations under that source (`patch.diff:63`, `patch.diff:455`); human must decide that this grouped selector behavior is the desired scope tradeoff and not an over-broad selector result. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: fitness requires a human/manual confirmation that the actual dialog lets a searched source expand and select an existing citation instead of creating a new one, because no GUI per-fix repro exists in the bundle (`check-gates.json:42`). |

§6 Human Clearances

1. C4 verification: rerun the focused regression on a clean `maintenance/gramps61` target with the patch applied, including the red pre-fix and green post-fix legs for `gramps.gui.views.treemodels.test.citationtreemodel_search_test`.
2. T5 judgment: confirm that selector search should group by source and expose sibling citations when any citation under that source matches the search text.
3. Validation fitness: manually open Source Citations -> Add Existing Citation..., search for a source title, click Find, expand the retained source, and confirm an existing citation child can be selected without creating a new citation.
