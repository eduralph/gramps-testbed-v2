# Result — issue 13747 / metadata-set-serialization-order

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Saving/closing an unmodified family tree rewrites the on-disk sqlite file:
- Success criterion: N/A (close) — no patch lands in this bundle. The fix's own success
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: none — fix already exists in-flight; do NOT re-author. / out of scope: the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-close — superseded by open upstream PR 2340; the fix and its
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — N/A — close disposition (no patch to verify)
- C3 Change: none — patch.diff
- C4 Verification (red→green): none — N/A — close disposition (no patch to verify)
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 Structure: none — N/A — close disposition (no patch to verify)
- T2 Shape: none — N/A — close disposition (no patch to verify)
- T3 Runtime: none — N/A — close disposition (no patch to verify)
- T4 Contribution: none — N/A — close disposition (no patch to verify)
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Advisory review — SKIPPED (close disposition)

The reviewer leaf was skipped: this bundle's Plan concluded a close / no-fix disposition (likely-close), so there is no patch to review.

- NEEDS-HUMAN — Confirm the close disposition 'likely-close' (no patch was built). Override to a fix path (iterate-to-Do) if the close is wrong.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] Confirm the close disposition 'likely-close' (no patch was built). Override to a fix path (iterate-to-Do) if the close is wrong.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden: confirmed close — superseded by an open PR
- Outcome: discontinued
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-21
- Why discontinued / where the work goes: defect is real and still unfixed on the target
  branch, but a complete fix + regression test is already submitted as open upstream PR 2340
  ("Sort set metadata so unchanged databases are not rewritten", branch
  fix/bug-13747-metadata-set-order, commit 48b8294aa5, "Fixes #13747"). Work is carried by
  that PR; re-briefing here would duplicate it.

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
