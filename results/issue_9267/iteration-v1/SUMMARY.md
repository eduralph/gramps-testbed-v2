# Result — issue 9267 / name-format-change-rebuilds-sort

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Changing the Display Name format in Preferences refreshes what each row
- Success criterion: After changing the Display Name format in Edit→Preferences→
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the missing sort-order rebuild when the active display-name format changes

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
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style (4 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Target-state note: `$PDCA_TARGET` is readable at `/home/eddie/workspace/gramps`, is an unpatched base, and `git apply --check patch.diff` succeeds; citations for added lines are therefore grounded on `patch.diff`, while existing source context is grounded on the target tree.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states a concrete defect, success criterion, invariant, scope, and repro for People flat name-format re-sort (`brief.md:8`, `brief.md:13`, `brief.md:16`, `brief.md:25`, `brief.md:29`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The repro describes the pre-fix stale order and reopen contrast (`brief.md:29`), and the configured red/green gate reports red-without-fix PASS (`check-gates.json:33`). |
| C3 — C3 Change | FAIL | The patch installs `_format_changed()` on shared `BasePersonView` and calls `self.model.rebuild_sort()` (`patch.diff:239`, `patch.diff:246`), but `PersonTreeView` also uses `BasePersonView` with `PersonTreeModel` (`gramps/plugins/view/persontreeview.py:61`, `gramps/plugins/view/persontreeview.py:67`, `gramps/gui/views/treemodels/peoplemodel.py:592`) while the patch only adds `rebuild_sort()` to `FlatBaseModel` (`patch.diff:21`). |
| C4 — C4 Verification (red→green) | PASS | The core verification gate reports green-with-fix PASS and red-without-fix PASS (`check-gates.json:33`, `check-gates.json:37`); caveat: the GUI interface repro was skipped/unverifiable (`check-gates.json:42`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | PASS | For the flat-list defect, the target reuses cached sort keys unless empty (`gramps/gui/views/treemodels/flatbasemodel.py:589`, `gramps/gui/views/treemodels/flatbasemodel.py:623`), and the patch invalidates/recomputes them before rebuild (`patch.diff:21`, `patch.diff:45`, `patch.diff:56`). |
| T1 — T1 Structure | N/A | No addon structure is touched; the conformance gate also classifies T1 as addon-only N/A for this core patch (`check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | Shape and POTFILES gates pass (`check-gates.json:69`, `check-gates.json:78`), and the new core test is registered in `po/POTFILES.skip` (`patch.diff:253`, `patch.diff:261`). |
| T3 — T3 Runtime | FAIL | Runtime gates passed generally (`check-gates.json:87`, `check-gates.json:96`), but the patched shared callback would raise on Person Tree format changes because `PersonTreeModel` inherits `TreeBaseModel` (`gramps/gui/views/treemodels/peoplemodel.py:592`, `gramps/gui/views/treemodels/treebasemodel.py:251`) and the new method is only on `FlatBaseModel` (`patch.diff:21`, `patch.diff:246`). |
| T4 — T4 Contribution | N/A | No commit message or PR wrapper artifact is present, matching the T4 N/A gate basis (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the acceptable fix may broaden from the brief's flat People name-format scope to shared name/place format handling in `BasePersonView` (`brief.md:13`, `brief.md:25`, `brief.md:28`, `patch.diff:232`, `patch.diff:234`); impact: determines whether the final fix should be flat-only, guarded by model capability, or extended safely to tree/place paths. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: after the C3/T3 runtime defect is corrected, a human must confirm the actual GUI People flat list satisfies the success criterion because the interface repro was skipped/unverifiable (`brief.md:13`, `check-gates.json:42`, `check-gates.json:46`). |

## §6 Human Decisions

1. T5 scope/judgment: decide whether this cycle should remain limited to People flat name-format sorting, or whether shared `BasePersonView` handling of name/place format changes is acceptable if made safe for both flat and tree models.
2. V fitness-to-purpose: after the runtime defect is fixed, validate the real GUI workflow in People flat view because the interface repro did not exercise the bug in automation.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] T5 — T5 Judgment — DECISION OWED: decide whether the acceptable fix may broaden from the brief's flat People name-format scope to shared name/place format handling in `BasePersonView` (`brief.md:13`, `brief.md:25`, `brief.md:28`, `patch.diff:232`, `patch.diff:234`); impact: determines whether the final fix should be flat-only, guarded by model capability, or extended safely to tree/place paths.
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: after the C3/T3 runtime defect is corrected, a human must confirm the actual GUI People flat list satisfies the success criterion because the interface repro was skipped/unverifiable (`brief.md:13`, `check-gates.json:42`, `check-gates.json:46`).
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): _format_changed() calls self.model.rebuild_sort() on BasePersonView, which is shared with PersonTreeView; PersonTreeModel inherits TreeBaseModel, not FlatBaseModel, so rebuild_sort() is absent there and would raise AttributeError at runtime. Add a safety guard (hasattr check or no-op on TreeBaseModel) before shipping.
- By / date: Eduard Ralph / 2026-06-28

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
