# Result — issue 820-build-toolchain-coverage / 820-build-toolchain-coverage

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: PR #820's `.github/docker/gramps-ci/Dockerfile` purges the build
- Success criterion: source-built addon deps either **build** in PR #820 CI (the
- Repo + branch target: gramps-project/addons-source @ `maintenance/gramps60` via
- Scope (one logical fix) / out of scope: decide and implement one of: (a) keep `libgraphviz-dev`/`libpq-dev` (and

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix — carries one decision (bake headers vs declare-and-
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: worktree /home/eddie/workspace/addons-source-6.0-fork-lane0 missing — run 'make worktrees LANES=N'.
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
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
- Iteration delta (if iterating): Bundle is not verifiable as-is. Before the next Do/Check: - C4 never ran: run-verify failed because worktree /home/eddie/workspace/addons-source-6.0-fork-lane0 was missing ('make worktrees LANES=N'). Provision the worktree so the red->green test (tests/test_addon_system_deps.py) actually executes — no evidence yet that it fails pre-fix / passes post-fix. - Advisory review never produced (reviewer leaf crashed, non-zero exit). Re-run the Check reviewer; bundle cannot be accepted without one. - T3 gramps61 delta: 1 new failure not in baseline, Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq. Confirm whether it is caused by this change or pre-existing noise. The patch approach itself looks sound — this iterate is to get the bundle verified, not to redesign the fix.
- By / date: Eduard Ralph / 2026-06-18

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
