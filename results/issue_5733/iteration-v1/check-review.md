Task under review: fix Gramps issue 5733 so ODF graphical descendant-chart output scales draw-text font sizes when "scale tree to fit" scales the boxes.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the defect, success criterion, invariant, and scope for ODT draw-text scaling parity with PDF/cairo at brief.md:5, brief.md:12, brief.md:18, and brief.md:26. |
| C2 — C2 Reproduction (red pre-fix) | PASS | I restored the production file to pre-fix in a temp clone and the added test failed red with 16.00pt emitted vs 8.00pt expected; the failing assertions are the scaled box and center-text checks at patch.diff:338 and patch.diff:372. |
| C3 — C3 Change | PASS | The patch records init-time F-style text properties, computes current draw-time properties, serializes scaled overrides, and switches draw_text/draw_box/center_text spans to that style at patch.diff:23, patch.diff:78, patch.diff:140, patch.diff:162, patch.diff:182, and patch.diff:194. |
| C4 — C4 Verification (red→green) | PASS | Focused verification in a patched temp clone passed green (`python3 -m unittest gramps.plugins.test.odfdoc_drawscale_test`: 3 tests OK) after the same test failed red pre-fix; the configured C4 gate failure is an unavailable worktree caveat at check-gates.json:33, not a patch defect. |
| C5 — C5 Causal adequacy | PASS | The target old code writes fixed F styles from init-time font sizes and draw spans reference those fixed names at /home/eddie/gramps/gramps/gramps/plugins/docgen/odfdoc.py:651 and /home/eddie/gramps/gramps/gramps/plugins/docgen/odfdoc.py:1884, while the patch reads current font props and overrides only when changed at patch.diff:113. |
| T1 — T1 Structure | N/A | Core-only patch with no addon layout surface; the conformance gate also reports addon structure N/A at check-gates.json:51. |
| T2 — T2 Shape | PASS | The new test has the project GPL header at patch.diff:210 and is registered in POTFILES.skip at patch.diff:402; check-gates reports both shape and potfiles pass at check-gates.json:60 and check-gates.json:69. |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: the whole-suite runtime gate crashed before producing JUnit at check-gates.json:78, so a human must decide whether the focused red/green test is sufficient or rerun the full core suite in a working Gramps test lane before merge. |
| T4 — T4 Contribution | N/A | No commit-msg.txt or pr-description.md is present in the artifact bundle, matching the T4 N/A gate result at check-gates.json:87. |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: because /home/eddie/gramps/gramps is on stale/different `master` and the patch targets maintenance/gramps61, a human must accept the target-state caveat and the backend-wide ODF draw-text override scope before sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: XML-level red/green is verified, but a human must confirm LibreOffice-rendered ODT output visually meets the user-facing "text fits scaled boxes like PDF" criterion from brief.md:12. |

§6 Human Clearances

1. T3 Runtime: decide whether to waive the whole-suite runner crash or rerun the Gramps core suite in a valid lane; the focused test was verified red-to-green, but the full runtime gate did not execute tests.
2. T5 Judgment: decide whether the stale `master` target caveat is acceptable for this artifact review and whether applying the fix at the ODF draw backend level is the intended scope for maintenance/gramps61.
3. V Validation: perform the manual fitness check from brief.md:34: generate a graphical Descendant Chart to ODT on letter/portrait with "scale tree to fit", open it in LibreOffice, and compare to PDF; clear only if the ODT box text visibly scales down and fits the scaled boxes.
