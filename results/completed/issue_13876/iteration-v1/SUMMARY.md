# Result — issue 13876 / citation-tree-view-delete-noop

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Sources category's **Citation Tree** view mode, selecting a Citation row (not a Source row) and choosing Delete shows the confirmation dialog(s), but after confirming **nothing is deleted** — the citation remains. Only Source rows (and their child citation) are actually removed; a selected Citation row is deleted only if its parent Source row is also selected. (Mantis 13876; NO-NOTES — description + Discourse report are the only signal.)
- Success criterion: In Citation Tree view mode, selecting a Citation row and confirming Delete **actually removes that citation** from the database — the same effect the flat Citation list view's delete produces — and the row disappears from the view.
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core).
- Scope (one logical fix) / out of scope: the Citation **Tree** view's delete handler does not actually delete a selected citation row — make it perform the citation removal (matching list-view behaviour). / **out of scope:** Source-row deletion behaviour (already works); the double-confirmation-dialog UX the reporter notes (cosmetic, separate); changes to flat Citation list view (used only as the correct-behaviour reference).

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (NO-NOTES — root cause derived on repro)
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — → essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite.
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 3 file(s) conform to doc 16 §Coding style
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
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
- Iteration delta (if iterating): C4 failed on both the upstream and essential-line legs — a real test failure, not an environment issue. The builder fabricated the "green-with-fix=PASS / red-without-fix=PASS" claim in build-notes.md; it has no Bash access and never ran run-verify.sh. Root cause of the test failure: the builder imported LibSourceView directly in the headless test, but LibSourceView is a GUI view mixin with gi/gramps.gui imports — it was never headlessly importable and that is not a bug to fix. The builder's assertion that it "only imports gramps.gen.errors.HandleError" was unverified and wrong. The one-line fix to libsourceview.py (remove_source → db.method("remove_%s", obj_type)) is correct in principle and should be kept. Rewrite the test so it does not import LibSourceView. The fix is ultimately a db-method dispatch: test that db.method("remove_%s", obj_type)(handle, trans) removes the right object for obj_type="Citation" vs "Source" at the gen.db layer, without going through the GUI mixin. If direct headless testing is genuinely impossible, declare PDCA-UNVERIFIABLE and carry the reproduction as an interface test instead. Also: scope the POTFILES.skip changes to only the new citationtreeview_test.py entry — remove the mass deletions of unrelated test entries and the erroneous undoablestyledbuffer_test.py line that belong to other bundles.
- By / date: Eduard Ralph / 2026-06-20

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
