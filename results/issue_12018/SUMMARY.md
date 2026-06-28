# Result — issue 12018 / tag-organize-dialog-search

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The "Organize Tags" dialog's tag list has GTK's interactive type-ahead
- Success criterion: In the Organize Tags dialog, the type-ahead search either is
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the nonfunctional interactive search on the tag list TreeView in the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*12018_*.py for bundle issue_12018 — the per-fix GUI red→green cannot run; 
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Target-state caveat: `$PDCA_TARGET` is readable but is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` and does not contain this bundle's changes; `gramps/gui/views/tags.py` still matches the patch's old blob (`235be79c82`) with the inline columns and no search binding at `gramps/gui/views/tags.py:478`. Citations for bundled added/changed lines therefore use `patch.diff`; this is not a C4 blocker.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief gives a concrete UI defect and success criterion: Organize Tags search must either target Name or be removed, within `gramps/gui/views/tags.py` scope (`brief.md:13`, `brief.md:24`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The pre-fix target has the tag list columns and `ListModel` creation but no search binding (`gramps/gui/views/tags.py:478`, `gramps/gui/views/tags.py:485`), matching the brief's Ctrl-F/no-selection-move repro (`brief.md:29`); the red-without-fix gate passed (`check-gates.json:37`). |
| C3 — C3 Change | PASS | The patch chooses the allowed "search column = Name" resolution by defining Name as model column 2 and calling `set_search_column` on the actual `namelist` TreeView (`patch.diff:16`, `patch.diff:44`, `patch.diff:63`). |
| C4 — C4 Verification (red→green) | PASS | The configured per-fix verification reports green-with-fix and red-without-fix PASS (`check-gates.json:33`, `check-gates.json:37`); the missing GUI dogtail repro is non-gating/unverifiable, not a stale-target compile/apply failure (`check-gates.json:42`, `check-gates.json:47`). |
| C5 — C5 Causal adequacy | PASS | The change directly binds GTK interactive search to the visible Name model column while preserving the existing column order (`patch.diff:19`, `patch.diff:29`, `patch.diff:44`), which satisfies the invariant that the enabled search control must have an effect. |
| T1 — T1 Structure | N/A | The bundle touches core GUI/test/translation files, not an addon layout; the configured T1 gate also reports addon structure N/A (`patch.diff:1`, `patch.diff:70`, `patch.diff:193`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | The new test carries the GPL header and the added core test files are registered in `POTFILES.skip` as required by the brief (`patch.diff:76`, `patch.diff:92`, `patch.diff:201`, `patch.diff:204`). |
| T3 — T3 Runtime | PASS | The whole core unit baseline and GUI smoke gates both pass, with only recorded baseline drift caveats (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is in the bundle, so the contribution-wrapper gate is explicitly N/A (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | PASS | Scope is narrow and coherent: production code changes only the Organize Tags TreeView search setup, while tests cover the column index and binding side effect (`patch.diff:60`, `patch.diff:63`, `patch.diff:155`, `patch.diff:170`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because the GUI dogtail repro is absent/unverifiable and the unit test uses a recording stand-in for the TreeView, a human must decide whether the artifact evidence is sufficient for the actual user-facing Ctrl-F/type-ahead behavior (`check-gates.json:42`, `check-gates.json:46`, `patch.diff:105`, `patch.diff:113`). |

## §6 Human Decisions Owed

1. V — Validation — fitness-to-purpose: decide whether the red→green unit evidence plus the direct `set_search_column(_TAG_NAME_COL)` change is sufficient to accept the real Organize Tags UI behavior, or whether a manual/dogtail validation artifact is required before sign-off.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] V — Validation — fitness-to-purpose — DECISION OWED: because the GUI dogtail repro is absent/unverifiable and the unit test uses a recording stand-in for the TreeView, a human must decide whether the artifact evidence is sufficient for the actual user-facing Ctrl-F/type-ahead behavior (`check-gates.json:42`, `check-gates.json:46`, `patch.diff:105`, `patch.diff:113`).
- [x] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*12018_*.py for bundle issue_12018 — the per-fix GUI red→green cannot run; 

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
- Tracker comment / PR description must explain why a recording stand-in unit test was used instead of the brief's prescribed dogtail test: OrganizeTagsDialog cannot be built headlessly (GTK aborts without a display), so the production search-binding seam was driven via a fake TreeView that records set_search_column(); the fix is a single GTK API call with no logic to get wrong.
