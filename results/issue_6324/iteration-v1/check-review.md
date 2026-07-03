Review task: fix Gramps cairo PDF/print table pagination so a short wrapping table-cell paragraph at a page break is not silently dropped.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines a cairo table-cell page-boundary content-loss defect and success criterion for full text preservation across pages (brief.md:5, brief.md:11). |
| C2 — C2 Reproduction (red pre-fix) | PASS | I ran the added test against the old `libcairodoc.py`; it failed at `gramps/plugins/test/cairodoc_table_pagination_test.py:177` because pagination did not terminate, matching the pre-fix no-progress/drop mechanism described by the removed shortcut in `$PDCA_TARGET/gramps/plugins/lib/libcairodoc.py:618`. |
| C3 — C3 Change | PASS | The patch removes the cell-only `<4 line` move-to-next-page shortcut and leaves the generic first-line-fit/split path to handle the case (patch.diff:17, patch.diff:21). |
| C4 — C4 Verification (red→green) | PASS | In a patched temp copy, `GRAMPS_RESOURCES=/tmp/pdca-check-target/build/share python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v` passed; the same test failed red on old code, and the official gate failure in check-gates.json is a missing-lane runner issue, not evidence against the patch (check-gates.json:33). |
| C5 — C5 Causal adequacy | PASS | The regression drives `CairoDoc.paginate` and the production table/cell/paragraph classes (patch.diff:67), and asserts both termination and every word surviving pagination (patch.diff:210, patch.diff:220). |
| T1 — T1 Structure | N/A | Core-only change; addon structure rules do not apply, matching the configured gate's N/A basis (check-gates.json:51). |
| T2 — T2 Shape | PASS | The new test has the project GPL header (patch.diff:38) and the new core test file is listed in `po/POTFILES.skip` as required by the brief (patch.diff:242). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: focused red→green runtime and `git diff --check` pass, but the broader T3 suite crashed before producing JUnit; a human must decide whether to accept this environment caveat or rerun the full suite in a working lane (check-gates.json:78). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this check bundle, so contribution-wrapper review does not apply (check-gates.json:87). |
| T5 — T5 Judgment | PASS | The patch is narrowly scoped to cairo paragraph division and one regression test, with no broad backend rewrite or unrelated file churn beyond POTFILES registration (patch.diff:1, patch.diff:32, patch.diff:234). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because the automated test proves the pagination no-progress case but does not visually inspect a generated PDF, a human must decide whether this is sufficient fitness evidence for the user-facing print/PDF report defect. |

## §6 Human Decisions

1. T3 — T3 Runtime: clear whether the focused red→green run plus clean diff check is enough while the full runner is unavailable, or rerun the whole suite in a working lane.
2. V — Validation — fitness-to-purpose: clear whether the red→green production-path regression is enough, or require a manual PDF/report check that a wrapped table cell at the page boundary visibly renders all text across pages.

Target-state caveat: `$PDCA_TARGET` is readable but on `master`, not the brief's `maintenance/gramps61`; `git apply --check patch.diff` succeeds there, and patch-content citations above therefore use `patch.diff` where the target source does not yet contain the change.
