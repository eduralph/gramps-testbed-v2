# Result — issue 6571 / gedcom-multiple-surname-comma-export

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: When a person has multiple surnames (the compound-surname facility) and the
- Success criterion: N/A — disposed as **by-design**, no patch. The reporter himself
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: none — this is a triage disposition, not a fix. / out of scope: changing the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: by-design
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

The reviewer leaf was skipped: this bundle's Plan concluded a close / no-fix disposition (by-design), so there is no patch to review.

- NEEDS-HUMAN — Confirm the close disposition 'by-design' (no patch was built). Override to a fix path (iterate-to-Do) if the close is wrong.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] Confirm the close disposition 'by-design' (no patch was built). Override to a fix path (iterate-to-Do) if the close is wrong.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: discontinued
- Iteration delta (if iterating): Re-dispositioned from merged-wider/by-design (signed off 2026-06-21) to discontinued per maintainer decision, 2026-07-01.
- By / date: Eduard Ralph / 2026-07-01

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
