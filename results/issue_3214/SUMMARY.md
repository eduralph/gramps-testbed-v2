# Result — issue 3214 / preformatted-note-fontsize-reset-to-default

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Note editor, changing a (preformatted) note's font size away from the
- Success criterion: Applying a style value equal to its default leaves the text with **no
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the `int` (and, for consistency, `str`) branch of

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C4 — C4 Verification (red→green) — DECISION OWED: The human must decide whether to accept the patch after rerunning verification on the intended maintenance/gramps61 worktree, because this target is on master at aef9f35 and full apply fails only in stale POTFILES context, while direct unittest execution here aborts before tests with ResourcePath.ERROR for missing build/share; this is an environment/target-state caveat, not observed patch failure.
- [x] T3 — T3 Runtime — DECISION OWED: The human must decide whether the whole-suite runtime gate can be deferred or rerun in a valid lane, because check-gates reports a pre-test crash with no JUnit XML at check-gates.json:78 and check-gates.json:82, which does not identify a regression in this patch.
- [x] T5 — T5 Judgment — DECISION OWED: The human must sign off that the localized guard plus focused regression tests are enough risk coverage for this core widget path, given no full-suite runtime result was obtained.
- [x] V — Validation — fitness-to-purpose — DECISION OWED: The human must validate fitness-to-purpose for the Note editor/report workflow, because artifact review verifies the data-model invariant but does not manually confirm rendered report behavior in the application.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
