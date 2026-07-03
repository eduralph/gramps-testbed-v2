# Result — issue 8841 / note-link-click-hypersensitive

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the styled-text Note editor/view, a hyperlink fires "open in browser"
- Success criterion: After the fix, a single click whose position is not actually
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: The URL-match detection in the styled-text editor resolves the pointer to

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — C4-verify-interface: green-with-fix=FAIL / red-without-fix=PASS
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

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

Reviewing issue 8841: fix styled-text note hyperlink activation so clicks in empty space beside/below a link do not open the snapped nearest link.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines the defect, success criterion, invariant, scope, and target branch for the hyperlink hit-test bug; decision owed is only whether later verification proves this exact GUI behavior, not what must be built (`brief.md:5`, `brief.md:11`, `brief.md:16`, `brief.md:25`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The target preimage still uses `get_iter_at_location(x, y)` and immediately derives `self.match`/link tags from that snapped iter, matching the stated red mechanism for empty-space clicks (`gramps/gui/widgets/styledtexteditor.py:435`, `gramps/gui/widgets/styledtexteditor.py:438`, `gramps/gui/widgets/styledtexteditor.py:446`; repro described at `brief.md:31`). |
| C3 — C3 Change | PASS | The patch is narrowly scoped to `StyledTextEditor`, adds a geometry guard before URL/link matching, and clears `self.match` when the pointer is outside the iter rectangle (`patch.diff:27`, `patch.diff:39`, `patch.diff:49`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: the human must clear whether the withheld AT-SPI/dogtail repro was actually red pre-fix and green post-fix, because `check-gates.json` reports core verification unverifiable and interface verification failed from missing lane worktree, while my local Xvfb probe could not initialize a display (`check-gates.json:33`, `check-gates.json:42`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | PASS | The patched guard sits before the production path that emits `match-changed`, which sets `url_match`, and before button press consumes `url_match` to call `_open_url_cb`; this addresses the snapped-iter cause rather than only browser launch (`gramps/gui/widgets/styledtexteditor.py:450`, `gramps/gui/widgets/styledtexteditor.py:404`, `gramps/gui/widgets/styledtexteditor.py:511`, `gramps/gui/widgets/styledtexteditor.py:516`). |
| T1 — T1 Structure | N/A | No addon path is changed; the configured structure gate also treats this as addon-only and not applicable to the core file patch (`patch.diff:1`, `check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | The only touched source file already has the GPL header, the patch adds no new core Python files requiring POTFILES registration, and both shape/POTFILES gates pass (`gramps/gui/widgets/styledtexteditor.py:1`, `check-gates.json:69`, `check-gates.json:78`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: the human must decide whether to accept or rerun runtime coverage, because both unit and GUI smoke gates failed before producing JUnit XML, which is an environment/runner result rather than demonstrated patch behavior (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this review bundle, and the contribution gate explicitly marks that wrapper check N/A (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | PASS | Advisory judgment: the patch is minimal, applies cleanly to the target preimage, and changes the hit-test decision point rather than out-of-scope menu or browser-launch behavior; remaining judgment is captured under C4/T3/V (`brief.md:28`, `patch.diff:1`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must validate the actual user-facing GUI fitness-to-purpose: empty-area clicks beside/below a read-only note link must not open the browser, while on-link glyph clicks must still open under the existing gesture semantics (`brief.md:11`, `brief.md:13`). |

## §6 Human Clearances

1. C4 verification: rerun or inspect the withheld `engine/interface/test_bug_0008841_note_link_hittest.py` result and confirm red pre-fix / green post-fix for empty-space clicks and real link clicks.
2. T3 runtime: decide whether the unit/interface pre-test runner failures are waived infrastructure issues or require a clean rerun before sign-off.
3. V validation: manually confirm in Gramps Notes on the patched build that clicking beside/below the URL does nothing and clicking on the rendered URL still follows the existing Ctrl+click/view-mode behavior.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C4 — C4 Verification (red→green) — DECISION OWED: the human must clear whether the withheld AT-SPI/dogtail repro was actually red pre-fix and green post-fix, because `check-gates.json` reports core verification unverifiable and interface verification failed from missing lane worktree, while my local Xvfb probe could not initialize a display (`check-gates.json:33`, `check-gates.json:42`, `check-gates.json:46`).
- [x] T3 — T3 Runtime — DECISION OWED: the human must decide whether to accept or rerun runtime coverage, because both unit and GUI smoke gates failed before producing JUnit XML, which is an environment/runner result rather than demonstrated patch behavior (`check-gates.json:87`, `check-gates.json:96`).
- [x] V — Validation — fitness-to-purpose — DECISION OWED: a human must validate the actual user-facing GUI fitness-to-purpose: empty-area clicks beside/below a read-only note link must not open the browser, while on-link glyph clicks must still open under the existing gesture semantics (`brief.md:11`, `brief.md:13`).
- [x] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)

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
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- Docker image `gramps-testbed:ubuntu-6.1.0` pip install fails on gramps build deps (silent container exit 1), blocking the automated C4 interface gate — image needs rebuilding or dependency pinning.
- Host environment lacks `pytest`; interface tests had to fall back to `python3 -m unittest` — add pytest to the host dev-deps or document the fallback in the runner guide.
