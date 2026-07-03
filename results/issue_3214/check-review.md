Reviewing issue 3214: applying a default styled-text value, especially FONTSIZE=10, must clear any explicit tag so a note returns to the same stored state as an untouched note.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the defect, invariant, success criterion, scope, and expected test surface explicitly at brief.md:6, brief.md:13, brief.md:17, brief.md:27, and brief.md:38. |
| C2 — C2 Reproduction (red pre-fix) | PASS | The pre-fix target unconditionally reapplies str/int tags after removal at /home/eddie/gramps/gramps/gramps/gui/widgets/styledtextbuffer.py:476 and /home/eddie/gramps/gramps/gramps/gui/widgets/styledtextbuffer.py:480, while FONTSIZE defaults to 10 at /home/eddie/gramps/gramps/gramps/gen/lib/styledtexttagtype.py:99; the added test's 12-then-default assertion at patch.diff:110 would fail on that code. |
| C3 — C3 Change | PASS | The patch removes prior str/int tags and skips reapplying when the value equals STYLE_DEFAULT at patch.diff:7 and patch.diff:13, directly matching the requested invariant. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: The human must decide whether to accept the patch after rerunning verification on the intended maintenance/gramps61 worktree, because this target is on master at aef9f35 and full apply fails only in stale POTFILES context, while direct unittest execution here aborts before tests with ResourcePath.ERROR for missing build/share; this is an environment/target-state caveat, not observed patch failure. |
| C5 — C5 Causal adequacy | PASS | The change is at the causal write point reached by the public apply path: apply_style delegates to _apply_style_to_selection at /home/eddie/gramps/gramps/gramps/gui/widgets/styledtextbuffer.py:674 and /home/eddie/gramps/gramps/gramps/gui/widgets/styledtextbuffer.py:689, and the test drives apply_style then inspects StyledText tags at patch.diff:116 and patch.diff:123. |
| T1 — T1 Structure | N/A | No addon-source path is introduced; check-gates marks structure addon-only and N/A for this core-only change at check-gates.json:51. |
| T2 — T2 Shape | PASS | The new test has the project GPL header at patch.diff:27 and is registered in POTFILES.skip at patch.diff:164; automated gates report shape and potfiles pass at check-gates.json:60 and check-gates.json:69. |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: The human must decide whether the whole-suite runtime gate can be deferred or rerun in a valid lane, because check-gates reports a pre-test crash with no JUnit XML at check-gates.json:78 and check-gates.json:82, which does not identify a regression in this patch. |
| T4 — T4 Contribution | N/A | No commit-msg.txt or pr-description.md is present in the artifact bundle, and the contribution gate is explicitly N/A at check-gates.json:87. |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: The human must sign off that the localized guard plus focused regression tests are enough risk coverage for this core widget path, given no full-suite runtime result was obtained. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: The human must validate fitness-to-purpose for the Note editor/report workflow, because artifact review verifies the data-model invariant but does not manually confirm rendered report behavior in the application. |

## §6 Human Clearances

1. C4 Verification: rerun the added test on the intended maintenance/gramps61 target, or explicitly accept the static red/green evidence plus the target-state caveat.
2. T3 Runtime: rerun the core runtime suite in a valid lane, or explicitly waive the infrastructure pre-test crash reported by the gate.
3. T5 Judgment: decide whether the change/test scope is sufficient without broader runtime evidence.
4. V Validation: manually confirm the Note editor/report outcome if release confidence requires the rendered workflow, using: select note text, set font size 12, set it back to 10, save, and confirm stored StyledText has no FONTSIZE tag and report rendering matches an untouched note.
