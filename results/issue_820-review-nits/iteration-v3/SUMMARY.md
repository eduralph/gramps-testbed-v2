# Result — issue 820-review-nits / 820-review-nits

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: a set of independent low-risk issues in PR #820's test/harness code:
- Success criterion: each item resolved — (a) helper wired in or removed; (b)
- Repo + branch target: gramps-project/addons-source @ `maintenance/gramps60` via
- Scope (one logical fix) / out of scope: the five cleanups above. / out of scope: the lib convergence

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (small, low-risk; splittable).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — error: .github/workflows/ci.yml: patch does not apply
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures)
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Advisory review — NOT COMPLETED

The reviewer did not produce a verdict table (reviewer leaf failed: Command '['claude', '-p', '--model', 'claude-opus-4-8', '--effort', 'high', '--agent', 'reviewer', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Edit', '--output-format', 'stream-json', '--verbose']' returned non-zero exit status 1.).

- NEEDS-HUMAN — re-run the Check reviewer; this bundle has no advisory review and must not be accepted until one exists.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] re-run the Check reviewer; this bundle has no advisory review and must not be accepted until one exists.

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): issue_820-review-nits Rejected: C4 gate red — patch.diff does not apply ("error: .github/workflows/ci.yml: patch does not apply"), so the test was never shown red-pre/green-post. Patch was cut against a stale base; re-cut all hunks against current maintenance/gramps60 (ci.yml has moved since these hunks were written). Also fix before re-Check: - Advisory review never completed (reviewer leaf crashed, exit 1) — there is no §5 verdict and the §6 NEEDS-HUMAN item cannot be cleared until a review exists. Ensure the reviewer leaf runs. - T3 gramps61 × core 6.1 regression: 1 new failure vs baseline — Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq. Investigate whether the py_compile/.gpr.py inclusion change or the type_plugins() rewrite triggers it; gramps60 matrix is green.
- By / date: Eduard Ralph / 2026-06-19

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
