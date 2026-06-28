# Result — issue 12260 / note-link-new-object-crash

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Creating a new linked object from the link-edit dialog (e.g. a new Note via
- Success criterion: Creating a new Note (or other object) through the link-edit
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the wrong assumption in `gramps/gui/editors/editlink.py` `_on_new_callback`

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*12260_*.py for bundle issue_12260 — the per-fix GUI red→green cannot run; 
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

## Target-State Caveat

`$PDCA_TARGET` was set and readable at `/home/eddie/workspace/gramps`, but the checked-out branch observed there is not the brief's stated `maintenance/gramps61` target (`brief.md:24`). The production `editlink.py` preimage matches the patch index for that file (`patch.diff:2`), and the patch applies cleanly to the target tree; added lines and the new test are therefore grounded on `patch.diff`, not treated as target defects.

## Verdict Table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | Brief provides defect, success criterion, invariant, scope, and test target; the detected Note-vs-handle contract conflict is escalated under C5/T5 (`brief.md:9`, `brief.md:16`, `brief.md:19`, `brief.md:29`, `brief.md:36`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix `_on_new_callback` dereferences `.handle` on its callback argument, and a real editor callback can emit only `get_handle()`, so the handle-string red case is re-derived (`gramps/gui/editors/editlink.py:156`, `gramps/gui/editors/editlink.py:160`, `gramps/gui/editors/editcitation.py:400`, `gramps/gui/editors/editcitation.py:401`). |
| C3 — C3 Change | PASS | Patch reads string callbacks as handles using the selected object type and preserves the object-callback path; the new test is registered in POTFILES.skip (`patch.diff:20`, `patch.diff:21`, `patch.diff:23`, `patch.diff:26`, `patch.diff:124`). |
| C4 — C4 Verification (red→green) | PASS | Gating verifier reports targeted red-without-fix and green-with-fix PASS; the missing GUI repro is non-gating and not a fabricated C4 blocker (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:42`, `check-gates.json:47`). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: target `EditNote.save` passes the object while `EditCitation.save` passes a handle, so a human must decide whether the Note/ToDo root cause is misstated or a different base is authoritative, because the patch fixes handle-string callbacks but not an independently proven Note-specific route (`gramps/gui/editors/editnote.py:381`, `gramps/gui/editors/editnote.py:383`, `gramps/gui/editors/editcitation.py:400`, `gramps/gui/editors/editcitation.py:401`, `patch.diff:20`). |
| T1 — T1 Structure | N/A | Core-only patch has no addons-source path, so addon layout structure does not apply (`check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | Existing touched production file has GPL header, the new test adds the GPL header, and the new core test is listed in POTFILES.skip (`gramps/gui/editors/editlink.py:1`, `patch.diff:37`, `patch.diff:53`, `patch.diff:124`). |
| T3 — T3 Runtime | FAIL | Whole-suite unit baseline runner exited before producing JUnit XML, while GUI smoke passed; this is runtime coverage debt rather than C4 red-green failure (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description is present in the bundle, so contribution-wrapper review does not apply (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: human must judge whether targeted C4 red-green is enough despite the non-gating unit-runner crash and absent GUI red→green repro, because that determines sign-off risk (`check-gates.json:37`, `check-gates.json:46`, `check-gates.json:91`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human must validate fitness to the actual Mantis 12260 intent because artifact-only review confirms a handle-string callback fix but not the brief's specific Note/ToDo route (`brief.md:16`, `brief.md:33`, `brief.md:35`, `gramps/gui/editors/editnote.py:381`, `gramps/gui/editors/editnote.py:383`). |

## §6 Human Clearance Items

1. C5 — Decide whether the authoritative defect is the general handle-string new-object callback path, such as Citation, or specifically the Note/ToDo path described in the brief. Impact: if Note/ToDo is required, require an interface repro or corrected base evidence; if the handle-string path is the intended bug, causal adequacy clears.
2. T5 — Decide whether to accept sign-off risk with targeted C4 red-green passing while the whole-suite unit baseline crashed before JUnit and GUI red→green repro is absent. Impact: acceptance relies on the focused regression test rather than full runtime confidence.
3. V — Decide whether the patch is fit for Mantis 12260 on the intended maintenance base. Impact: this is the final approve/reject decision after resolving the scope and verification-risk questions above.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — DECISION OWED: target `EditNote.save` passes the object while `EditCitation.save` passes a handle, so a human must decide whether the Note/ToDo root cause is misstated or a different base is authoritative, because the patch fixes handle-string callbacks but not an independently proven Note-specific route (`gramps/gui/editors/editnote.py:381`, `gramps/gui/editors/editnote.py:383`, `gramps/gui/editors/editcitation.py:400`, `gramps/gui/editors/editcitation.py:401`, `patch.diff:20`).
- [x] T5 — T5 Judgment — DECISION OWED: human must judge whether targeted C4 red-green is enough despite the non-gating unit-runner crash and absent GUI red→green repro, because that determines sign-off risk (`check-gates.json:37`, `check-gates.json:46`, `check-gates.json:91`).
- [x] V — Validation — fitness-to-purpose — DECISION OWED: human must validate fitness to the actual Mantis 12260 intent because artifact-only review confirms a handle-string callback fix but not the brief's specific Note/ToDo route (`brief.md:16`, `brief.md:33`, `brief.md:35`, `gramps/gui/editors/editnote.py:381`, `gramps/gui/editors/editnote.py:383`).
- [x] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*12260_*.py for bundle issue_12260 — the per-fix GUI red→green cannot run; 

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
