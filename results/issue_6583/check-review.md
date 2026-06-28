# Check Review

Target-state caveat: `$PDCA_TARGET` is readable and pre-patch; `git apply --check patch.diff` succeeds there. The target checkout has local dirt, including patch-touched paths, so citations for proposed/new lines use `patch.diff` while current-source citations use the target checkout; I do not treat target dirt as a C4 blocker.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | NEEDS-HUMAN | DECISION OWED: original success wording says Add/Edit/Merge/Remove controls should not carry the reported ellipsis, while the latest carry-forward says Add/Merge keep ellipses and only Edit drops them; human must decide which scope controls because it changes patch fitness (brief.md:12, brief.md:60). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Target source still has pre-fix `Edit...` labels in affected toolbar/menu locations, e.g. `gramps/plugins/lib/libpersonview.py:271` and `gramps/plugins/lib/libpersonview.py:348`, and the gate records red-without-fix=PASS (check-gates.json:33). |
| C3 — C3 Change | PASS | The patch changes Edit labels from `Edit...`/`_Edit...` to `Edit`/`_Edit` while leaving Add/Merge ellipses intact, and adds a regression test for Edit-label ellipses (patch.diff:9, patch.diff:18, patch.diff:100, patch.diff:161). |
| C4 — C4 Verification (red→green) | PASS | The configured C4 gate reports green-with-fix=PASS and red-without-fix=PASS; the GUI per-fix repro is unavailable but non-gating, not a patch failure (check-gates.json:33, check-gates.json:42). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: root-cause policy is contested; human must affirm that Edit is a state/info opener while Add/Merge are input-required, because that determines whether dropping only Edit is causally adequate (brief.md:60, `gramps/plugins/lib/libpersonview.py:457`). |
| T1 — T1 Structure | N/A | No addons-source path is touched, so the addon-layout structure rule does not apply and the gate marks it N/A (check-gates.json:60). |
| T2 — T2 Shape | PASS | The new test carries the GPL header and is registered in `POTFILES.skip`; T2 and T2-potfiles both pass (patch.diff:69, patch.diff:464, check-gates.json:69). |
| T3 — T3 Runtime | PASS | Unit baseline matches the recorded baseline and GUI smoke is green; the noted baseline tree drift is advisory rather than a failed runtime gate (check-gates.json:87, check-gates.json:96). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` is in this artifact bundle, and the contribution wrapper gate marks that N/A (check-gates.json:105). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: human must accept static-source label verification as sufficient for this UI-label defect because no issue-specific dogtail interface repro exists (patch.diff:105, check-gates.json:42). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: maintainer/user fitness turns on whether the final visible-label policy under the latest scope resolves the reported clutter/inconsistency without over-removing required ellipses (brief.md:9, brief.md:60). |

## §6 Human Decisions

1. C1 scope: Decide whether Iteration 2 supersedes the original Add/Edit/Merge wording, so the accepted target is "Edit without ellipsis; Add/Merge with ellipsis."
2. C5 causal adequacy: Decide whether the HIG classification is correct for these commands; if Edit is not a state/info opener, the patch is too broad or wrong.
3. T5 judgment: Decide whether the static parser regression plus C4 red/green gate is adequate evidence without an issue-specific GUI dogtail repro.
4. V validation: Decide whether the resulting UI labels are fit for users and maintainers, not just mechanically consistent with the test.
