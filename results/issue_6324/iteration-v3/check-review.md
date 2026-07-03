Task under review: fix cairo/PDF table pagination so a wrapping table-cell paragraph at a page break is preserved instead of rendering a blank/torn cell.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | brief.md defines the cairo/PDF defect, invariant, scope, test path, and required production pagination path at brief.md:6, brief.md:16, brief.md:24, and brief.md:35. |
| C2 — C2 Reproduction (red pre-fix) | PASS | With the new test kept and the production patch reversed, `python3 -m unittest -v gramps.plugins.test.cairodoc_table_pagination_test` failed both cases with `wrap_page != label/tall_page`, matching the pre-fix blank/torn-row behavior asserted at patch.diff:433 and patch.diff:486. |
| C3 — C3 Change | PASS | The base root cause is present where short cell paragraphs return `(None, self)` at gramps/plugins/lib/libcairodoc.py:620 and table cells then truncate children at gramps/plugins/lib/libcairodoc.py:1015; the patch adds row-level move-whole/force-split handling at patch.diff:34, patch.diff:64, and patch.diff:128. |
| C4 — C4 Verification (red→green) | PASS | check-gates.json reports green-with-fix and red-without-fix pass at check-gates.json:33, and I independently observed the focused test pass after applying the patch in `/tmp/pdca-check-6324` with 2 tests OK. |
| C5 — C5 Causal adequacy | PASS | The test drives `CairoDoc.paginate` and imports the production `GtkDocTable`/`GtkDocTableRow`/`GtkDocTableCell`/`GtkDocParagraph` classes at patch.diff:219 and patch.diff:326, while assertions inspect rendered `_plaintext` at patch.diff:351 and patch.diff:381. |
| T1 — T1 Structure | N/A | This is a core-library/test change, not an addon layout change; the configured T1 gate also reports no `addons-source` path at check-gates.json:51. |
| T2 — T2 Shape | PASS | The added test has the project GPL header at patch.diff:154 and the new core test file is registered in `po/POTFILES.skip` at patch.diff:506; gates report T2 shape and potfiles pass at check-gates.json:59 and check-gates.json:68. |
| T3 — T3 Runtime | PASS | Runtime gate reports the core unit baseline matches recorded known reds at check-gates.json:77, and the focused patched-temp-clone run of `python3 -m unittest -v gramps.plugins.test.cairodoc_table_pagination_test` passed both tests. |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is in the review bundle, so contribution-wrapper checks do not apply; the gate records this as N/A at check-gates.json:86. |
| T5 — T5 Judgment | PASS | Reviewer judgment: the current patch addresses the prior iteration objections by preserving keep-together when no sibling split exists at patch.diff:64, testing `_plaintext` at patch.diff:351, and covering the earlier-column split branch at patch.diff:442. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a maintainer/user must decide whether the tested pagination behavior is acceptable for real cairo/PDF reports on the intended `maintenance/gramps61` branch, because final output fitness and visual page composition are human sign-off criteria beyond artifact-only review. |

Target-state caveat: `$PDCA_TARGET` is readable and the patch applies cleanly, but the checkout reports branch `master` rather than the brief's `maintenance/gramps61`; I grounded base-code citations on the target source where present and changed/new-code citations on `patch.diff`.

§6 Human Clearance Items

1. V — Validation — fitness-to-purpose: run or inspect a representative cairo/PDF table report on the intended `maintenance/gramps61` integration branch and confirm that wrapped cell text appears across the page break with acceptable table borders/page composition. Artifact checks and the focused headless test are green, but final PDF fitness is a human acceptance decision.
