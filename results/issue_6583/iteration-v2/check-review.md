# Check Review

Target caveat: `$PDCA_TARGET` is readable at `/home/eddie/workspace/gramps`, but it is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` with unrelated dirty files. The submitted patch applies cleanly there, and the affected pre-patch labels are present in that target state, so this is not a C4 blocker.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | NEEDS-HUMAN | DECISION OWED: the brief starts as verification/no-patch against `gramps/gui/views/listview.py`, but carry-forward orders a text fix across view files and matching menu labels; human must confirm that broader scope is intended because the patch changes more than the initial verification surface (brief.md:12, brief.md:23, brief.md:54). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The target red state contains the reported inconsistency: Add/Edit/Merge-family labels carry trailing `...` while Delete does not in the same UI definition (gramps/plugins/view/citationtreeview.py:365, gramps/plugins/view/citationtreeview.py:381, gramps/plugins/view/citationtreeview.py:493). |
| C3 — C3 Change | PASS | The patch removes trailing `...` from Add/Edit/Merge-family toolbar/menu labels across the affected view files and adds a regression test enumerating those files (patch.diff:365, patch.diff:388, patch.diff:215, patch.diff:257). |
| C4 — C4 Verification (red→green) | PASS | Automated fix verification reports `green-with-fix=PASS / red-without-fix=PASS`; the missing GUI-specific repro is non-gating/unverifiable rather than a failed verification (check-gates.json:33, check-gates.json:37, check-gates.json:42, check-gates.json:47). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: the mechanical cause is literal trailing-ellipsis label strings, but the UX root cause was contested as dialog-openers versus toolbar/menu label consistency; human must confirm the maintainer/HIG rule controls because the patch removes ellipses from commands that still open dialogs (brief.md:17, brief.md:54, gramps/plugins/view/relview.py:414). |
| T1 — T1 Structure | N/A | Addon structure rules do not apply because the patch is a core source/test change with no `addons-source` path, matching the gate's N/A rationale (check-gates.json:60, check-gates.json:64). |
| T2 — T2 Shape | PASS | The new test has the project GPL header and the new core Python test is registered in `po/POTFILES.skip`; shape and POTFILES gates both pass (patch.diff:167, patch.diff:997, check-gates.json:69, check-gates.json:82). |
| T3 — T3 Runtime | PASS | Core unit baseline and GUI smoke gates pass, with only recorded-baseline/tree-drift caveats rather than new failures (check-gates.json:87, check-gates.json:91, check-gates.json:96, check-gates.json:100). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this advisory bundle, and the contribution gate explicitly treats that as N/A (check-gates.json:105, check-gates.json:109). |
| T5 — T5 Judgment | PASS | The patch is text-only for UI labels and the regression test reads source strings headlessly instead of importing GTK-heavy modules, which is proportionate for this cosmetic label invariant (patch.diff:198, patch.diff:211, patch.diff:244, patch.diff:270). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human sign-off must confirm the patched UI actually satisfies the issue's fitness target for list-view toolbar/control labels, including whether matching popup/menu label changes are acceptable for users (brief.md:28, brief.md:34, check-gates.json:123, check-gates.json:125). |

## §6 Human Decisions

1. C1 — Scope: decide whether the carry-forward instruction supersedes the original "verification only" wording and authorizes changing all listed view toolbar and matching menu labels, not just checking `listview.py`.
2. C5 — Root cause: decide whether the accepted policy is "toolbar/menu labels corresponding to these actions omit trailing ellipses" even when the command opens a dialog, resolving the prior WONTFIX-style interpretation.
3. V — Fitness: manually confirm the patched Gramps UI on the intended branch no longer presents the inconsistent Add/Edit/Merge/Remove trailing-ellipsis toolbar/control labels and that the resulting text is suitable for release.
