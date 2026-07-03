Review task: fix cairo/PDF table pagination so wrapping table-cell text at a page break is preserved instead of rendering a blank/torn cell.

Target-state caveat: `$PDCA_TARGET` is readable but stale for this patch: it is on `master` at `aef9f35ec64b67f5912c5d19543060d43f270a9a`, lacks the added test file, and still has the old cairo pagination code. A temporary copy of `$PDCA_TARGET` accepted `patch.diff` cleanly, so affected citations below are grounded on `patch.diff` rather than treating target staleness as a patch defect.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the exact cairo/PDF defect, success criterion, invariant, and out-of-scope boundaries for wrapped table cells across page breaks (`brief.md:5`, `brief.md:11`, `brief.md:16`, `brief.md:24`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Applying only the new test file to the stale target and running `python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v` failed all 3 cases on old code: torn last-cell row, torn split-sibling row, and non-terminating taller-than-page guard (`patch.diff:517`, `patch.diff:567`, `patch.diff:620`). |
| C3 — C3 Change | PASS | The patch changes the production divide chain to report no-content cells, move whole rows when no rowmate has split, force split when progress is otherwise impossible, and guard empty-page requeue loops (`patch.diff:9`, `patch.diff:77`, `patch.diff:120`, `patch.diff:164`, `patch.diff:234`). |
| C4 — C4 Verification (red→green) | PASS | In a patched temporary copy with minimal `GRAMPS_RESOURCES`, `python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v` ran 3 tests and returned OK; the same test red-failed against old code, so the focused red→green is demonstrated (`patch.diff:517`, `patch.diff:567`, `patch.diff:620`). |
| C5 — C5 Causal adequacy | PASS | The old drop point is the cell truncation path after a child returns `(None, self)` (`/home/eddie/gramps/gramps/gramps/plugins/lib/libcairodoc.py:995`, `/home/eddie/gramps/gramps/gramps/plugins/lib/libcairodoc.py:1015`), and the patch redirects that exact no-progress signal to row/table/paginator decisions instead of silently emptying the cell (`patch.diff:176`, `patch.diff:133`, `patch.diff:247`). |
| T1 — T1 Structure | N/A | No addon structure is touched; this is a core library/test/POTFILES change only (`patch.diff:1`, `patch.diff:262`, `patch.diff:652`). |
| T2 — T2 Shape | PASS | The added core test has the project GPL header and the new Python test is registered in `po/POTFILES.skip` as required by the brief (`patch.diff:268`, `patch.diff:652`). |
| T3 — T3 Runtime | NEEDS-HUMAN | Decision owed: the focused regression passes, but the configured whole-suite runtime gate did not execute because its lane worktree was missing, so a human must decide whether focused red→green is enough now or require a repaired whole-suite run before sign-off (`check-gates.json:78`, `check-gates.json:82`). |
| T4 — T4 Contribution | N/A | The bundle contains no commit message or PR description artifact for contribution-wrapper review (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | NEEDS-HUMAN | Decision owed: acceptability turns on whether the patch's forced-split/overflow policy for impossible-to-fit cells is the right product behavior versus merely preventing the loop; artifacts show termination and no dropped words, but final policy judgment is human-owned (`patch.diff:47`, `patch.diff:203`, `patch.diff:226`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Decision owed: a human must clear real PDF fitness-to-purpose, especially visual row/border appearance across an actual report page break; artifact tests inspect paginated text structure, not rendered PDF output (`brief.md:11`, `patch.diff:470`). |

§6 Human Clearance Items

1. T3 Runtime: repair or waive the missing whole-suite lane gate. I verified the focused regression independently: old code plus the new test failed 3/3; patched code passed 3/3.
2. T5 Judgment: decide whether forced placement/overflow for elements that cannot fit even an empty page is acceptable as the no-progress policy.
3. V Validation: run or inspect an actual cairo/PDF report with a wrapping table cell at a page break and confirm the rendered PDF preserves the text with acceptable row and border appearance.
