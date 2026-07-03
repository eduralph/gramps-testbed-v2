Task under review: fix cairo print/PDF table pagination so a short wrapping table cell at a page boundary is not rendered blank or dropped, and add a regression test.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines a narrow cairo backend defect and success criterion: wrapped table-cell text at a page boundary must survive without dropped lines; scope excludes other backends and broad rewrites (brief.md:5, brief.md:11, brief.md:24). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added test is designed to fail on the pre-fix base by driving a page that holds filler rows plus only part of the wrapping row and asserting no torn row plus full `_plaintext` survival (patch.diff:316, patch.diff:329, patch.diff:347, patch.diff:357); check gate reports red-without-fix PASS (check-gates.json:33). |
| C3 — C3 Change | PASS | The patch changes only cairo table/table-row/table-cell division handling plus the required test/POTFILES entry, directly at the briefed root-cause surface (patch.diff:5, patch.diff:24, patch.diff:70, patch.diff:86, patch.diff:371). |
| C4 — C4 Verification (red→green) | PASS | Gate reports green-with-fix PASS and red-without-fix PASS (check-gates.json:33); I also applied the patch in `/tmp/pdca-gramps-check.br1lQq` and ran `env GRAMPS_RESOURCES=build/share PYTHONPATH=. python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test`, which returned `Ran 1 test ... OK`. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: accept the chosen behavioral repair as causally adequate: the base short-cell keep-together branch returns `(None, self), 0` (gramps/plugins/lib/libcairodoc.py:620) and the patch propagates that as “move the whole row/table onward” (patch.diff:39, patch.diff:47, patch.diff:81), but the human must decide whether moving the row intact is acceptable for the product expectation versus requiring an actual split at the boundary. |
| T1 — T1 Structure | N/A | No addon-source layout is touched; the bundle is a core cairo/test change, matching the gate’s addon-structure N/A (check-gates.json:51). |
| T2 — T2 Shape | PASS | Added test has the project GPL header and no translatable strings, and the new core test file is registered in `po/POTFILES.skip` as required (patch.diff:92, patch.diff:139, patch.diff:371). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: accept or rerun broader runtime coverage: the focused patched regression passes locally, but the configured whole-suite runtime gate failed before producing JUnit XML, reported as a pre-test crash rather than a test failure (check-gates.json:78). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this review bundle, so contribution-wrapper review is not applicable here (check-gates.json:87). |
| T5 — T5 Judgment | PASS | The patch is scoped to the cairo pagination call chain, avoids the rejected v1 blanket removal, asserts rendered `_plaintext`, and uses geometry matching the brief’s filler-row-plus-wrapping-row scenario (brief.md:60, patch.diff:126, patch.diff:245, patch.diff:329). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: product fitness remains human sign-off: the automated regression proves preservation/no torn row in a synthetic cairo pagination case, but a human must decide whether that sufficiently represents the user-visible Database Differences Report/PDF behavior described in the brief (brief.md:6, brief.md:31). |

§6 Human Clearances

1. C5 causal adequacy: decide whether moving the affected short wrapping row intact to the next page satisfies the intended cairo pagination behavior, or whether the product requires first-line-on-current-page splitting.
2. T3 runtime: decide whether the focused regression plus C4 gate are enough despite the configured whole-suite runner’s pre-test crash/no-JUnit result, or require a clean broader suite rerun.
3. V validation: decide whether the synthetic production-path pagination test is fit for purpose for the original PDF/report symptom, or require a manual Database Differences Report PDF check.
