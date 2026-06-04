# Result — issue selftest / ** off-by-one-in-pager

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect: ** The result pager shows N-1 of N items; the last item is dropped.
- Success criterion: ** Pager shows all N items; a test over a 3-item list asserts 3 are rendered.
- Repo + branch target: ** example-repo @ main
- Scope (one logical fix) / out of scope: ** Fix the pager's range bound. / out of scope: pager styling, pagination size.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C5 causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T3 runtime: gramps core unit suite: fail — Generated XML report: /workspace/gramps-testbed-v2/test-results/TEST-gramps.gen.merge.test.merge_ref_test.SourceSourceCh
- T5 judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Cross-vendor reviewer (advisory, artifact-only)

Reviewer family: codex. Inputs: patch.diff, brief.md, check-gates.json (build-notes.md withheld).

## Per-item verdicts
- PASS — re-ran asserted evidence: stub red→green confirmed.
- PASS — every cited path:line grounds on the target branch.
- PASS — diff stays within one logical fix (model-decidable).
- NEEDS-HUMAN — validation fitness-to-purpose: is this the right thing at all? (always-human by design)

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] validation fitness-to-purpose: is this the right thing at all? (always-human by design)

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome:
- Iteration delta (if iterating):
- By / date:

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
