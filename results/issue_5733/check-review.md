Review task: fix Gramps bug 5733 so ODT graphical descendant-chart draw text uses the same scaled font size as the scale-to-fit report/PDF path.

Target caveat: `$PDCA_TARGET` is readable but stale for this review (`/home/eddie/gramps/gramps` is on `master`, lacks the patch, and rejects only the `po/POTFILES.skip` context); affected source citations below are therefore grounded on `patch.diff` as instructed.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief gives a concrete defect, success criterion, invariant, surfaces, and out-of-scope constraints for ODT draw-text scaling parity (`brief.md:6`, `brief.md:12`, `brief.md:18`, `brief.md:26`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added test asserts scaled ODF font size and documents the old failure as emitted `BASE_SIZE` instead of `BASE_SIZE * SCALE` (`patch.diff:375`, `patch.diff:390`); the C4 gate records `red-without-fix=PASS` (`check-gates.json:33`). |
| C3 — C3 Change | PASS | The patch records initial `F<name>` text properties, compares them to current post-scale font properties, writes non-colliding override styles, and switches draw spans to those styles (`patch.diff:25`, `patch.diff:117`, `patch.diff:167`, `patch.diff:193`). |
| C4 — C4 Verification (red→green) | PASS | Gate evidence says green-with-fix and red-without-fix both passed (`check-gates.json:33`); I also applied the code/test hunks in a local shared clone and ran `GRAMPS_RESOURCES=... python3 -m unittest gramps.plugins.test.odfdoc_drawscale_test`, which ran 5 tests OK. |
| C5 — C5 Causal adequacy | PASS | The causal path matches the defect: fixed styles are written before report scaling, then draw-time spans now use a style derived from the current font size (`patch.diff:9`, `patch.diff:123`, `patch.diff:140`, `patch.diff:210`). |
| T1 — T1 Structure | N/A | This is a core-code/test change, not an addon layout change; the patch touches `gramps/plugins/docgen/odfdoc.py`, adds `gramps/plugins/test/odfdoc_drawscale_test.py`, and updates `po/POTFILES.skip` only (`patch.diff:1`, `patch.diff:231`, `patch.diff:471`). |
| T2 — T2 Shape | PASS | The new test has the existing GPL header shape and the new core Python file is registered in `POTFILES.skip` (`patch.diff:237`, `patch.diff:471`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: the configured whole-suite runtime gate exited before producing JUnit XML (`check-gates.json:78`), while the focused regression test passes; human must decide whether this non-gating environment/bootstrap gap is acceptable for sign-off. |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in the bundle, so contribution-wrapper review does not apply (`check-gates.json:87`). |
| T5 — T5 Judgment | PASS | The solution stays in the ODF backend rather than the explicitly out-of-scope `begin_report` restructuring and covers the prior-attempt KeyError and style-name collision regressions (`brief.md:9`, `brief.md:62`, `patch.diff:133`, `patch.diff:443`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: artifact and focused test evidence show emitted scaled font sizes, but a human must decide whether that satisfies the user-visible LibreOffice fitness criterion for scaled graphical descendant charts (`brief.md:34`). |

## §6 Human Decisions

1. T3 Runtime: decide whether to clear sign-off despite the whole-suite runner bootstrap failure, given the focused patched-clone test passed and the recorded C4 red-to-green gate passed.
2. Validation fitness-to-purpose: decide whether the emitted ODF font-size parity demonstrated by the test is sufficient, or whether a manual LibreOffice descendant-chart inspection is required before acceptance.
