# Result — issue 8362 / gedcom-export-place-type-accented

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: (Reported on 4.1.1, 2015.) GEDCOM export of a marriage place differed
- Success criterion: Exporting an event whose place has an accented title and a place
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: confirm the reported export discrepancy no longer reproduces on the current

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — test-only patch — no non-test production file for the red-without-fix leg to revert; the regression test must still pass
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): fail — T2 ✗ new core file gramps/plugins/export/test/exportgedcom_place_test.py is not registered in po/POTFILES.in or po/POTFI
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Advisory review — NOT COMPLETED

The reviewer did not produce a verdict table (reviewer leaf failed: Command '['claude', '-p', '--model', 'claude-sonnet-4-6', '--effort', 'medium', '--agent', 'reviewer', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Edit', '--add-dir', '/home/eddie/workspace/gramps', '--output-format', 'stream-json', '--verbose']' returned non-zero exit status 1.).

Failure class: **transient infra — safe to re-run.** The leaf exited non-zero with no output and retries did not recover, so it almost certainly hit a usage/rate limit or a transient API/network error rather than reviewing the diff; a sibling advisory leaf of a different family may already have covered it. See `check-review.error.log` in this bundle for the captured error.

- NEEDS-HUMAN — re-run the Check reviewer; this bundle has no advisory review and must not be accepted until one exists.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] re-run the Check reviewer; this bundle has no advisory review and must not be accepted until one exists.
- [x] C4 fix verified: test red pre-fix, green post-fix unverifiable — test-only patch — no non-test production file for the red-without-fix leg to revert; the regression test must still pass

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-25

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
