# Result — issue 6824 / html-report-relative-media-paths

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The HTML backend of the text reports (e.g. Detailed Ancestor Report,
- Success criterion: After the fix, `HtmlDoc.add_media(...)` emits an `<img>` whose
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: In the HTML docgen, the image reference written into the HTML is the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: core worktree /home/eddie/gramps/gramps-6.1-lane4 missing — run 'make worktrees LANES=N'.
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix Gramps HTML text reports so embedded media `<img src>` uses the report-relative data directory while preserving the absolute on-disk copy destination.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states a precise defect and success criterion: `HtmlDoc.add_media(...)` must emit report-relative `src` while keeping the copied image in the correct on-disk location (`brief.md:13`, `brief.md:16`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | I added only the patch's new regression test in a temp copy of `$PDCA_TARGET` and ran `GRAMPS_RESOURCES=/tmp/pdca-gramps-res... python3 -m unittest gramps.plugins.test.htmldoc_relmedia_test`; it failed red because `src` contained `/tmp/.../myreport/isphoto.jpg`, matching the root cause visible in target source at `gramps/plugins/docgen/htmldoc.py:610` and `gramps/plugins/docgen/htmldoc.py:624`. |
| C3 — C3 Change | PASS | The production hunk separates absolute copy path `imdir = datadirfull()` from relative HTML reference `imref = datadir()` and replaces all four `src=imdir + os.sep + refname` sites with `src=imref + "/" + refname` (`patch.diff:8`, `patch.diff:12`, `patch.diff:20`, `patch.diff:26`, `patch.diff:34`, `patch.diff:40`). |
| C4 — C4 Verification (red→green) | PASS | In a temp copy, the test failed before the production hunk and passed after applying it: `Ran 2 tests ... OK`; the configured gate failure was an environment/runner issue, not this patch's behavior (`check-gates.json:33`, `check-gates.json:37`). |
| C5 — C5 Causal adequacy | PASS | The root cause is the same absolute `datadirfull()` value being used for both resize destination and HTML `src` (`gramps/plugins/docgen/htmldoc.py:610`, `gramps/plugins/docgen/htmldoc.py:624`), while `datadir()` provides the relative subdirectory needed for the reference (`gramps/plugins/lib/libhtmlbackend.py:288`, `gramps/plugins/lib/libhtmlbackend.py:294`). |
| T1 — T1 Structure | N/A | Core-only patch; addon structure rules do not apply, consistent with the gate's N/A classification (`check-gates.json:51`, `check-gates.json:55`). |
| T2 — T2 Shape | PASS | The added test has the existing GPL header shape and the new core Python test is registered in `po/POTFILES.skip` by the patch (`patch.diff:51`, `patch.diff:175`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: the human must decide whether focused red→green verification is sufficient despite the whole-suite baseline runner crashing before producing JUnit XML; this is a target/runner health risk, not evidence of a behavioral regression (`check-gates.json:79`, `check-gates.json:82`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact was provided in this artifact-only review bundle, so contribution-wrapper checks do not apply (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: the human must accept or reject the target-state caveat that `$PDCA_TARGET` is on `master`, not the brief's `maintenance/gramps61`, and the `po/POTFILES.skip` hunk does not apply there even though the code/test hunks apply cleanly (`brief.md:24`, `patch.diff:167`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: final fitness depends on human acceptance that the unit-level `HtmlDoc.add_media` exercise covers the intended user workflow of copied/shared HTML reports with bundled images (`brief.md:33`, `brief.md:36`). |

## §6 Human Clearance Items

1. T3 Runtime: Decide whether to accept the focused red→green unit verification in place of the unavailable whole-suite baseline, whose configured runner failed before JUnit output (`check-gates.json:79`, `check-gates.json:82`).
2. T5 Judgment: Decide whether the `$PDCA_TARGET` branch mismatch is acceptable for this review. I observed `$PDCA_TARGET` on `master`; the brief targets `maintenance/gramps61` (`brief.md:24`). Code/test hunks apply cleanly, but `po/POTFILES.skip` is stale relative to the patch context.
3. Validation fitness-to-purpose: Decide whether the tested production `HtmlDoc.add_media` path is enough evidence for the manual report-copy scenario, or whether a full GUI/manual report generation pass is required before sign-off (`brief.md:33`, `brief.md:36`).


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 — T3 Runtime — DECISION OWED: the human must decide whether focused red→green verification is sufficient despite the whole-suite baseline runner crashing before producing JUnit XML; this is a target/runner health risk, not evidence of a behavioral regression (`check-gates.json:79`, `check-gates.json:82`).
- [x] T5 — T5 Judgment — DECISION OWED: the human must accept or reject the target-state caveat that `$PDCA_TARGET` is on `master`, not the brief's `maintenance/gramps61`, and the `po/POTFILES.skip` hunk does not apply there even though the code/test hunks apply cleanly (`brief.md:24`, `patch.diff:167`).
- [x] V — Validation — fitness-to-purpose — DECISION OWED: final fitness depends on human acceptance that the unit-level `HtmlDoc.add_media` exercise covers the intended user workflow of copied/shared HTML reports with bundled images (`brief.md:33`, `brief.md:36`).
- [x] C4 fix verified: test red pre-fix, green post-fix FAILED (gating) — run-verify.sh: core worktree /home/eddie/gramps/gramps-6.1-lane4 missing — run 'make worktrees LANES=N'.

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
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- Process delta: run `make preflight LANES=N` before any batch session; the 2026-07-02 batch found all lane worktrees missing (lanes 0–5), causing C4/T3 gate failures across all five bundles (6824, 7924, 8841, 3214, 6170).
