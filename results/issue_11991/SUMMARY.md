# Result — issue 11991 / citation-list-refresh-after-source-edit

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Sources view, editing a citation and saving it does not update the
- Success criterion: After a citation is edited and saved while the Sources view is
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the stale citation row after an in-place citation edit in the Sources view

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_11991
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — run-verify-interface.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_11991
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2-potfiles – N/A: no patch.diff
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: 4 new failure(s) not in baseline: LifeLineChartView.collection::import_or_collection, PDFFor
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

## 1. Artifact caveat

`patch.diff` is absent from the review directory, and the gate artifact records the same missing-patch condition for both verification commands (`check-gates.json:37`, `check-gates.json:46`). `PDCA_TARGET` was readable, so source citations below use `/home/eddie/workspace/gramps`; where the missing patch prevents reviewing the proposed change, the basis is grounded in the supplied artifacts.

## 2. Verdict table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the defect, success criterion, invariant, GUI surface, scope, and reproduction path clearly enough to test against (`brief.md:9`, `brief.md:12`, `brief.md:15`, `brief.md:24`, `brief.md:28`). |
| C2 — C2 Reproduction (red pre-fix) | FAIL | The brief gives a manual repro and expects an AT-SPI repro test, but the gates show no configured/recorded red pre-fix reproduction result (`brief.md:28`, `brief.md:31`, `check-gates.json:15`). |
| C3 — C3 Change | FAIL | The review cannot identify or inspect the proposed code change because the required `patch.diff` artifact is missing, despite C3's oracle being `patch.diff` (`check-gates.json:24`, `check-gates.json:26`). |
| C4 — C4 Verification (red→green) | FAIL | Red-to-green verification did not run against a patch: both unit and GUI verification gates fail on `no patch.diff`, which is an artifact failure rather than a target-state compile/apply defect (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:42`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | FAIL | The target source supports the likely causal area: `SourceView` connects only source signals while `ListView` connects exactly its `signal_map`, and citation views wire `citation-update`; however no patch is present to show the defect is causally fixed (`gramps/plugins/view/sourceview.py:117`, `gramps/gui/views/listview.py:844`, `gramps/plugins/view/citationlistview.py:150`, `gramps/plugins/view/citationtreeview.py:143`). |
| T1 — T1 Structure | N/A | The brief scopes this as a core GUI change, not an addon layout change, and the T1 gate also reports addon structure as not applicable (`brief.md:24`, `check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | N/A | No changed Python file can be shape-reviewed because `patch.diff` is missing; this is already captured as the C3 artifact failure, not a separate style finding (`check-gates.json:69`, `check-gates.json:73`, `check-gates.json:78`, `check-gates.json:82`). |
| T3 — T3 Runtime | FAIL | Runtime gates are not clean: the core unit baseline reports four new failures, although the GUI smoke gate is green (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description was included, and the brief keeps the work in draft until Check sign-off, so contribution-wrapper checks do not apply to this artifact bundle (`brief.md:46`, `check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | FAIL | Reviewer judgment cannot accept a bundle with no patch and no red-to-green verification, because the success criterion turns on visible citation-row refresh after save (`brief.md:12`, `check-gates.json:37`, `check-gates.json:46`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: after a complete patch and verification bundle exist, a human must decide whether the GUI behavior satisfies the user-facing purpose: the saved citation row refreshes in-place in Sources view without navigation (`brief.md:12`, `brief.md:24`). |

## §6 Human clearance items

1. **V — Validation — fitness-to-purpose:** Decide, after `patch.diff` and red-to-green evidence are supplied, whether the user-visible Sources view behavior meets the success criterion. Impact: without this clearance, the review can only reject the current artifact bundle, not confirm the fix is fit for release.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] V — Validation — fitness-to-purpose — DECISION OWED: after a complete patch and verification bundle exist, a human must decide whether the GUI behavior satisfies the user-facing purpose: the saved citation row refreshes in-place in Sources view without navigation (`brief.md:12`, `brief.md:24`).

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
- Iteration delta (if iterating): Re-dispositioned from merged-wider (signed off 2026-06-28) to discontinued per maintainer decision, 2026-07-01.
- By / date: Eduard Ralph / 2026-07-01

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
