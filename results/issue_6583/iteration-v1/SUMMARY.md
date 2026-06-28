# Result — issue 6583 / verify-toolbar-label-ellipsis-gone

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Reported (v4.0.0): list-view toolbar buttons were labelled "Add…",
- Success criterion: On `maintenance/gramps61`, confirm the list-view toolbar no
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: verify the list-view toolbar (built via the `ActionGroup`/UIManager in

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_6583
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — run-verify-interface.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_6583
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2-potfiles – N/A: no patch.diff
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Target-state caveat: `$PDCA_TARGET` is readable, but it is currently on `fix/bug-8850-gedcom-import-cal-date-case-sensitive`, not the briefed `maintenance/gramps61` branch. Because `patch.diff` is absent and the brief explicitly allows a no-patch verification disposition, I treated the automated "no patch.diff" C4 failures as a harness/artifact-shape mismatch rather than a patch defect.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief gives a narrow success criterion: confirm Add/Edit/Merge/Remove list-view toolbar controls no longer carry the reported ellipsis labels, with no patch if confirmed (`brief.md:12`). |
| C2 — C2 Reproduction (red pre-fix) | N/A | The original red condition is documented as historical v4.0.0 behavior, while this cycle is current-state verification on `maintenance/gramps61`, not a new fix needing a live red pre-fix run (`brief.md:9`, `brief.md:28`). |
| C3 — C3 Change | N/A | No source patch is expected for the accepted success path: the brief says "Verification, not a new fix (no patch if confirmed)" and the review directory has no `patch.diff` (`brief.md:14`). |
| C4 — C4 Verification (red→green) | PASS | Current-state source verification is green for the requested label check: list-view actions are defined as `"Add"`, `"Remove"`, `"Merge"`, and `"Edit"` without ellipses (`gramps/gui/views/listview.py:226`, `gramps/gui/views/listview.py:237`); the automated C4 failures are only "no patch.diff" (`check-gates.json:33`, `check-gates.json:42`). |
| C5 — C5 Causal adequacy | PASS | The defect turns on inconsistent trailing ellipses in Add/Edit/Merge toolbar action labels, and the relevant `ActionGroup` entries no longer contain those labels; remaining ellipsis strings are progress/status text, not toolbar action labels (`gramps/gui/views/listview.py:226`, `gramps/gui/views/listview.py:674`, `gramps/gui/views/listview.py:1388`). |
| T1 — T1 Structure | N/A | No addon layout is present or changed; the gate also classifies T1 as addon-only and not applicable without an addons-source path (`check-gates.json:60`). |
| T2 — T2 Shape | N/A | No checkable Python patch or new/removed core Python file is present, matching the gate's no-patch/no-checkable-path result (`check-gates.json:69`, `check-gates.json:78`). |
| T3 — T3 Runtime | PASS | Runtime gates are not regressed: unit baseline matches known reds and GUI smoke is green, with only baseline-tree-drift caveats reported (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description wrapper is present, which is acceptable for a no-patch verification bundle unless the human elects to publish a documentation/closure PR (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the branch-target caveat and no-patch verification artifact are acceptable for closing this cycle; impact is whether this proceeds as a resolved verification or must be rerun against an exact `maintenance/gramps61` checkout before sign-off (`brief.md:20`, `check-gates.json:33`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: decide whether source-level evidence plus any required manual UI sign-off satisfies the user-visible toolbar-label purpose; impact is closing Mantis 6583 as already fixed versus requiring a follow-up UI/text check (`brief.md:32`, `brief.md:40`). |

## §6 Human Clearance Items

1. T5 Judgment: Clear the target-state/artifact-shape caveat. `$PDCA_TARGET` is readable but not on the named branch, and the automated C4 gate failed because it expected `patch.diff`; decide whether this no-patch verification bundle may stand or must be rerun on an exact `maintenance/gramps61` checkout.
2. Validation fitness-to-purpose: Perform or accept the manual UI sign-off described by the brief. The source evidence shows no Add/Edit/Merge toolbar action ellipsis in `listview.py`, but the human must decide whether that is enough to resolve the reported user-visible inconsistency.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] T5 — T5 Judgment — DECISION OWED: decide whether the branch-target caveat and no-patch verification artifact are acceptable for closing this cycle; impact is whether this proceeds as a resolved verification or must be rerun against an exact `maintenance/gramps61` checkout before sign-off (`brief.md:20`, `check-gates.json:33`).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: decide whether source-level evidence plus any required manual UI sign-off satisfies the user-visible toolbar-label purpose; impact is closing Mantis 6583 as already fixed versus requiring a follow-up UI/text check (`brief.md:32`, `brief.md:40`).

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
- Iteration delta (if iterating): The builder correctly found the Add.../Edit.../Merge... ellipsis labels are still present on maintenance/gramps61 across ~10 view files (libpersonview.py, libplaceview.py, citationlistview.py, citationtreeview.py, eventview.py, familyview.py, mediaview.py, noteview.py, repoview.py, sourceview.py, relview.py). However it concluded "by-design / WONTFIX" under the argument that dialog-openers correctly take "...". That reading is wrong: maintainer Nick H confirms the GNOME Guidelines say to remove the ellipses from these labels. The fix is a text-only patch removing the trailing "..." from the Add/Edit/Merge toolbar button labels and their matching popup/menu label entries across all the view files listed in the build-notes. A close-disposition artifact is no longer appropriate; the next Do should produce patch.diff + commit-msg + pr-description.
- By / date: Eduard Ralph / 2026-06-28

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
