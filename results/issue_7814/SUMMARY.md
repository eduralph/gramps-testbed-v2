# Result — issue 7814 / detdescendant-death-line-for-living

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The Detailed Descendant Report printed "Died ______ in ______." for a person
- Success criterion: Generating a Detailed Descendant Report (or driving the report's
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: verify (and, only if it still reproduces, remove) the emission of death/burial

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_7814
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2-potfiles – N/A: no patch.diff
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 7814 / detdescendant-death-line-for-living

**Reviewer:** Claude (advisory, artifact-only)
**Date:** 2026-06-27
**Inputs examined:** brief.md, check-gates.json; no patch.diff present in review dir or in results/issue_7814/
**PDCA_TARGET:** unset — citations grounded on check-gates.json evidence and directly-observed result artifacts; cross-checkout browsing withheld per protocol

---

## Primary finding before the table

**No `patch.diff` was produced.** The builder wrote a test file
(`results/issue_7814/detdescendantreport_test.py`, 301 lines, well-structured)
and set `close-disposition = not-reproducible`, but never packaged any of it as a
diff. Every gate that expected a patch therefore trivially fell through as N/A or
failed on absence rather than content. The verdict table reflects the artifact state
as-found; the human must decide whether to package the test as a proper diff and
rerun the cycle, or close the issue without a committed regression guard.

---

## 5/5/1 Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief is complete: success criterion, repro instruction, test-file path, POTFILES.skip requirement, and explicit POSSIBLY-FIXED disposition. No ambiguity in scope or acceptance bar. |
| C2 Reproduction (red pre-fix) | NEEDS-HUMAN | Human must confirm the "not-reproducible" finding was actually exercised against maintenance/gramps61 per the repro instruction (brief.md:29-30) — no mechanical trace of a repro attempt exists in the result bundle beyond the close-disposition file. |
| C3 Change | FAIL | Test file exists at results/issue_7814/detdescendantreport_test.py but was never packaged as patch.diff; the required deliverable artifact is absent. Content cannot be reviewed or applied. |
| C4 Verification (red→green) | FAIL | Mechanical gate failed with "no patch.diff in results/issue_7814" (check-gates.json:C4 path_line); no patch to stage pre-fix red → post-fix green. Not a stale-target ordering issue — the patch simply was not produced. |
| C5 Causal adequacy | NEEDS-HUMAN | The test file exercises the `probably_alive` guard the brief cites at detdescendantreport.py:768-769 and 901-902; no capability probe added. Human must confirm those guard lines are intact on maintenance/gramps61 HEAD — that is the causal claim the "not-reproducible" disposition rests on, and it was not verified mechanically in this cycle. |
| T1 Structure | N/A | Core-only change (no addon path); §Structure is addon-only. Gate confirmed N/A (check-gates.json T1). |
| T2 Shape | NEEDS-HUMAN | Test file has GPL header (detdescendantreport_test.py:6-19, copyright 2025). Brief explicitly requires registering any new test .py in `po/POTFILES.skip` (brief.md:35); decide whether POTFILES.skip registration must be part of the packaged diff before close. |
| T3 Runtime | NEEDS-HUMAN | Gate reports 1 new failure vs baseline: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (check-gates.json T3); this test ID does not appear in t3-run-unit.log (34 034 lines), suggesting baseline skew rather than a regression this change caused. Human must decide: environmental noise / baseline staleness, or real regression requiring investigation before the issue is closed. |
| T4 Contribution | N/A | No commit-msg.txt or pr-description.md in bundle; gate confirmed N/A (check-gates.json T4). Deferred until patch is packaged. |
| T5 Judgment | NEEDS-HUMAN | Decide whether a test-only deliverable with no source change is the correct closure artifact for a POSSIBLY-FIXED issue: the brief says "a regression test … is the deliverable" for an already-fixed case (brief.md:16), but the test was never committed to the repo, so the guard could be silently removed in future without the test catching it. The value of the regression guard depends on the test actually landing in the tree. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Human must confirm: (a) the "not-reproducible" finding warrants a Mantis 7814 closure comment, (b) the regression test as written adequately protects the guard (both write_person_info and __write_children paths covered), and (c) EMPTY_ENTRY is a public export of detdescendantreport.py on maintenance/gramps61 (the test imports it at detdescendantreport_test.py:59; if it is a module-private name the test will error on import). |

---

## §6 Human-clearance checklist

- [ ] **C2** Confirm "not-reproducible" was tested against maintenance/gramps61 per the brief's repro instruction before accepting the close-disposition.
- [ ] **C5** Verify `probably_alive` guards at detdescendantreport.py:768-769 and 901-902 are present on maintenance/gramps61 HEAD (the causal basis for the no-fix close).
- [ ] **T2** Decide whether `po/POTFILES.skip` must be updated to register `gramps/plugins/textreport/test/detdescendantreport_test.py` (brief.md:35 requires it); include in packaged diff.
- [ ] **T3** Determine whether `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` delta is environmental/baseline noise or a real regression; clear or file separately before close.
- [ ] **T5** Decide whether the test file must be committed to the repo as a closure artifact (recommended) or whether a comment-only Mantis close is acceptable.
- [ ] **V** Confirm `EMPTY_ENTRY` is a public name in detdescendantreport.py on maintenance/gramps61 (test import at detdescendantreport_test.py:59 will fail at collection time if it is not).
- [ ] **V** Issue a Mantis 7814 closure comment recording the already-fixed disposition and, if the test lands, the commit reference.

---

## C5 smell-test note

The test file adds no capability probe (`hasattr`, `try/except ImportError`, or fallback around an optional API). It consumes `EMPTY_ENTRY` as a constant to mirror production configuration and calls the real production routines directly. The C5 smell-test does not fire.

---

## Advisory disposition

**Do not advance to merge.** The primary blocker is the absent `patch.diff` (C3/C4
FAIL). The builder must package the test file as a proper diff (placing it at
`gramps/plugins/textreport/test/detdescendantreport_test.py`, updating
`po/POTFILES.skip`, adding commit-msg.txt), then rerun the Check cycle. The
human-clearance items above should be resolved in the same pass.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C2 Reproduction (red pre-fix) — Human must confirm the "not-reproducible" finding was actually exercised against maintenance/gramps61 per the repro instruction (brief.md:29-30) — no mechanical trace of a repro attempt exists in the result bundle beyond the close-disposition file.
- [x] C5 Causal adequacy — The test file exercises the `probably_alive` guard the brief cites at detdescendantreport.py:768-769 and 901-902; no capability probe added. Human must confirm those guard lines are intact on maintenance/gramps61 HEAD — that is the causal claim the "not-reproducible" disposition rests on, and it was not verified mechanically in this cycle.
- [x] T2 Shape — Test file has GPL header (detdescendantreport_test.py:6-19, copyright 2025). Brief explicitly requires registering any new test .py in `po/POTFILES.skip` (brief.md:35); decide whether POTFILES.skip registration must be part of the packaged diff before close.
- [x] T3 Runtime — Gate reports 1 new failure vs baseline: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (check-gates.json T3); this test ID does not appear in t3-run-unit.log (34 034 lines), suggesting baseline skew rather than a regression this change caused. Human must decide: environmental noise / baseline staleness, or real regression requiring investigation before the issue is closed.
- [x] T5 Judgment — Decide whether a test-only deliverable with no source change is the correct closure artifact for a POSSIBLY-FIXED issue: the brief says "a regression test … is the deliverable" for an already-fixed case (brief.md:16), but the test was never committed to the repo, so the guard could be silently removed in future without the test catching it. The value of the regression guard depends on the test actually landing in the tree.
- [x] Validation — fitness-to-purpose — Human must confirm: (a) the "not-reproducible" finding warrants a Mantis 7814 closure comment, (b) the regression test as written adequately protects the guard (both write_person_info and __write_children paths covered), and (c) EMPTY_ENTRY is a public export of detdescendantreport.py on maintenance/gramps61 (the test imports it at detdescendantreport_test.py:59; if it is a module-private name the test will error on import).

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: discontinued
- Iteration delta (if iterating): Re-dispositioned from merged-wider/not-reproducible (signed off 2026-06-27; close comment was posted to Mantis) to discontinued per maintainer decision, 2026-07-01.
- By / date: Eduard Ralph / 2026-07-01

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
