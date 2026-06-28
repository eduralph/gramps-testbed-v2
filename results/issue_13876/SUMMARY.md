# Result — issue 13876 / citation-tree-delete-citation

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Citations view's **Citation Tree** view mode, selecting a citation
- Success criterion: Deleting a selected citation row in the Citation Tree view mode
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the failed citation deletion in

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
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Target-state caveat: `$PDCA_TARGET` is readable at `/home/eddie/workspace/gramps`, but it is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` rather than the brief's `maintenance/gramps61` target; the touched `libsourceview.py` preimage matches the patch index and `git apply --check` succeeds, while added-file citations are therefore grounded on `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 -- C1 Spec | PASS | The brief defines the failing workflow, success criterion, invariant, scope, and repro target tightly enough to judge the patch (`brief.md:9`, `brief.md:12`, `brief.md:15`, `brief.md:25`, `brief.md:30`). |
| C2 -- C2 Reproduction (red pre-fix) | PASS | The required failure is "citation remains after delete" (`brief.md:30`), and the red/green gate reports red-without-fix exercised and passed as a red check (`check-gates.json:33`, `check-gates.json:37`). |
| C3 -- C3 Change | PASS | The target helper classifies non-source selected handles as citations (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:49`) but then always removes a source (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:101`), and the patch replaces that with type-dispatched removal (`patch.diff:11`). |
| C4 -- C4 Verification (red->green) | PASS | Core verification reports green-with-fix and red-without-fix both PASS (`check-gates.json:33`, `check-gates.json:37`); GUI AT-SPI was skipped/non-gating, so final GUI fitness is deferred to V (`check-gates.json:42`, `check-gates.json:46`). |
| C5 -- C5 Causal adequacy | PASS | The defect path is causal: selected citation handles flow to `("Citation", handle)` (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:49`), backlink cleanup already uses `obj_type` (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:97`), and only the terminal remove call was hard-coded to source (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:101`). |
| T1 -- T1 Structure | N/A | No addon-source layout is touched; the artifact changes core library/test/POTFILES paths only (`patch.diff:1`, `patch.diff:16`, `patch.diff:166`; `check-gates.json:60`). |
| T2 -- T2 Shape | PASS | The new core test carries the project GPL header (`patch.diff:22`) and the new Python test files are registered in `POTFILES.skip` as requested by the brief (`brief.md:40`, `patch.diff:174`). |
| T3 -- T3 Runtime | PASS | Runtime gates report the core unit baseline matched and the GUI smoke was green, with only baseline drift caveats recorded (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 -- T4 Contribution | N/A | No commit message or PR description artifact is present in the bundle, and the contribution gate marks that wrapper check N/A (`check-gates.json:105`, `check-gates.json:109`). |
| T5 -- T5 Judgment | PASS | The patch stays inside the scoped delete behavior and supporting test/i18n registration; duplicate confirmation dialogs and source-row changes remain out of scope (`brief.md:25`, `brief.md:27`, `patch.diff:1`, `patch.diff:16`, `patch.diff:166`). |
| V -- Validation -- fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human must decide whether the headless production-helper red/green evidence is sufficient for the GUI success criterion after confirmation, because the GUI-specific interface repro was skipped (`brief.md:12`, `check-gates.json:42`, `check-gates.json:46`). |

## §6 Human Decisions

1. V -- Validation -- fitness-to-purpose: decide whether to accept the core helper red/green proof as sufficient for the user-facing Citation Tree delete workflow, despite the skipped GUI AT-SPI repro. Impact: accepting clears sign-off on behavior; rejecting requires a runnable GUI reproduction before this can be called fit for purpose.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] V -- Validation -- fitness-to-purpose — DECISION OWED: human must decide whether the headless production-helper red/green evidence is sufficient for the GUI success criterion after confirmation, because the GUI-specific interface repro was skipped (`brief.md:12`, `check-gates.json:42`, `check-gates.json:46`).
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
