# Result — issue 12539 / families-children-tab-refresh

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Families view, the bottom "Children" tab does not refresh to match
- Success criterion: After a filter/Find changes the Families list and the active
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the missing Children-tab refresh on a filter/Find-driven selection change in

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Target caveat: `$PDCA_TARGET` was readable at `/home/eddie/workspace/gramps`, but it is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` rather than the briefed `maintenance/gramps61`; the patch applies cleanly there, so existing-source citations use the target and new/changed hunks cite `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states a concrete Families-view defect, success criterion, invariant, scope, and repro path in `brief.md:8`, `brief.md:14`, `brief.md:17`, `brief.md:26`, and `brief.md:30`. |
| C2 — C2 Reproduction (red pre-fix) | FAIL | The expected GUI repro is named in `brief.md:35`, but the interface gate reports it skipped/unexercised in `check-gates.json:42`, while the committed test in `patch.diff:123` imports a new helper from `patch.diff:171` rather than reproducing the pre-fix Families filter symptom through existing production code. |
| C3 — C3 Change | PASS | The change hooks the existing `FamilyView(ListView)` path (`gramps/plugins/view/familyview.py:67`) after `ListView.build_tree` rebuilds and rebinds the model (`gramps/gui/views/listview.py:330`, `gramps/gui/views/listview.py:372`) and redirects the active family through `change_active` in `patch.diff:17` and `patch.diff:35`. |
| C4 — C4 Verification (red→green) | PASS | The configured core verifier records `green-with-fix=PASS / red-without-fix=PASS` in `check-gates.json:33`, and I do not convert the skipped GUI repro in `check-gates.json:42` into a blocking C4 failure. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: accept or reject the inferred root cause that stale Children data is caused by a hidden active family after rebuild, because `change_active` emits `active-changed` via `gramps/gui/views/navigationview.py:206` and `gramps/gui/displaystate.py:125`, and `FamilyChildren` listens on Family active changes at `gramps/plugins/gramplet/children.py:227`, but the end-to-end GUI repro was not exercised. |
| T1 — T1 Structure | N/A | No `addons-source` path is touched; the patch is core-only as shown by the changed paths in `patch.diff:1`, `patch.diff:56`, `patch.diff:123`, and `patch.diff:214`. |
| T2 — T2 Shape | PASS | New Python files carry GPL headers in `patch.diff:62` and `patch.diff:129`, and all new core `.py` paths are added to `po/POTFILES.skip` in `patch.diff:214`. |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: decide whether to accept runtime evidence with the core unit baseline unavailable from a pre-test runner crash in `check-gates.json:87`, while the GUI smoke baseline passed in `check-gates.json:96`. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` wrapper is present in the artifact bundle, matching the T4 N/A gate in `check-gates.json:105`. |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the extra production helper and new `gramps/plugins/view/test` package are acceptable despite the brief saying no new Gramps-tree files were expected except possible tests in `brief.md:41`, because the helper is introduced in `patch.diff:56` and the test package in `patch.diff:120`. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: validate in a real Families-view session that after Father=`Simpson` Find, the visible active family's Children tab updates without re-clicking, as required by `brief.md:14`, because the GUI repro gate did not exercise the behavior in `check-gates.json:42`. |

## §6 Human Clearance Items

1. C5 causal adequacy: decide whether the active-handle repair is the actual root-cause fix, given the static signal chain is coherent but the GUI repro was skipped.
2. T3 runtime: decide whether the non-gating unit baseline runner crash is acceptable for sign-off, or whether a clean unit-suite run is required before merge.
3. T5 judgment: decide whether the new helper module and new `gramps/plugins/view/test` package are an acceptable scope expansion for this small Families-view fix.
4. V validation: perform or accept a real GUI validation of the briefed workflow, since artifact gates did not prove the end-to-end Children-tab behavior.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — DECISION OWED: accept or reject the inferred root cause that stale Children data is caused by a hidden active family after rebuild, because `change_active` emits `active-changed` via `gramps/gui/views/navigationview.py:206` and `gramps/gui/displaystate.py:125`, and `FamilyChildren` listens on Family active changes at `gramps/plugins/gramplet/children.py:227`, but the end-to-end GUI repro was not exercised.
- [x] T3 — T3 Runtime — DECISION OWED: decide whether to accept runtime evidence with the core unit baseline unavailable from a pre-test runner crash in `check-gates.json:87`, while the GUI smoke baseline passed in `check-gates.json:96`.
- [x] T5 — T5 Judgment — DECISION OWED: decide whether the extra production helper and new `gramps/plugins/view/test` package are acceptable despite the brief saying no new Gramps-tree files were expected except possible tests in `brief.md:41`, because the helper is introduced in `patch.diff:56` and the test package in `patch.diff:120`.
- [x] V — Validation — fitness-to-purpose — DECISION OWED: validate in a real Families-view session that after Father=`Simpson` Find, the visible active family's Children tab updates without re-clicking, as required by `brief.md:14`, because the GUI repro gate did not exercise the behavior in `check-gates.json:42`.
- [x] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss

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
- By / date: Eduard Ralph / 2026-06-28

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
