# Result — issue 12110 / call-name-revalidate-on-given-change

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Name editor, the Call name field is validated against the Given name
- Success criterion: Editing the Given name re-runs the call-name validity check, so
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the missing re-validation of the Call field when the Given field changes in

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — run-verify-interface.sh: /home/eddie/workspace/gramps-6.1-lane0 has uncommitted changes — refusing to patch it
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

Target-state caveat: `PDCA_TARGET=/home/eddie/workspace/gramps` is readable, but it is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` with unrelated dirty files, not the requested `maintenance/gramps61`; unchanged source behavior is cited from that tree, while proposed additions are cited from `patch.diff`.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines the defect as stale Call-field validation when Given changes and defines success as re-running the Call validity check on Given edits (`brief.md:9`, `brief.md:15`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix `editname.py` computes Call validity from `given_field` but connects validation only to `call_field`, while the Given field has no `changed` hook (`/home/eddie/workspace/gramps/gramps/gui/editors/editname.py:176`, `/home/eddie/workspace/gramps/gramps/gui/editors/editname.py:223`, `/home/eddie/workspace/gramps/gramps/gui/editors/editname.py:236`). |
| C3 — C3 Change | PASS | The patch adds a Given-field `changed` callback and forces the existing Call widget validation from that callback, which is the missing trigger surface (`patch.diff:9`, `patch.diff:20`, `patch.diff:29`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: decide whether static trace plus manual GUI sign-off is enough, because the artifacts provide no core `*_test.py` red→green proof and interface verification was blocked by a dirty lane rather than by the patch (`check-gates.json:33`, `check-gates.json:42`). |
| C5 — C5 Causal adequacy | PASS | The causal chain is adequate for the scoped editor: `MonitoredEntry` calls `changed` after updating the Given text, and forced validation emits the Call field's existing custom validator (`/home/eddie/workspace/gramps/gramps/gui/widgets/monitoredwidgets.py:154`, `/home/eddie/workspace/gramps/gramps/gui/widgets/validatedmaskedentry.py:1075`, `/home/eddie/workspace/gramps/gramps/gui/widgets/validatedmaskedentry.py:1113`). |
| T1 — T1 Structure | N/A | Addon structure rules do not apply to this core-only edit of `gramps/gui/editors/editname.py` (`patch.diff:1`). |
| T2 — T2 Shape | PASS | The patch touches one existing Python file, adds no new/removal file registration burden, and the configured shape/POTFILES gates pass (`patch.diff:1`, `check-gates.json:69`, `check-gates.json:78`). |
| T3 — T3 Runtime | PASS | Advisory runtime gates report the unit baseline matches known reds and GUI smoke is green; baseline drift is a caveat, not a new patch failure (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is included in this bundle, so the contribution-wrapper gate has nothing to evaluate (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the issue scope is strictly the secondary Name editor or also the primary Person editor, which has the same Call/Given validation-only-on-Call pattern (`brief.md:28`, `/home/eddie/workspace/gramps/gramps/gui/editors/editperson.py:331`, `/home/eddie/workspace/gramps/gramps/gui/editors/editperson.py:379`, `/home/eddie/workspace/gramps/gramps/gui/editors/editperson.py:392`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: confirm the patched Name editor satisfies the real user workflow, because fitness-to-purpose is human-owned and the artifact bundle lacks a red→green GUI proof (`brief.md:15`, `check-gates.json:33`). |

## §6 Human Clearance Items

1. C4 — Verification: Decide whether to accept static review plus manual GUI confirmation for red→black and black→red Given-field transitions, or require a committed automated/interface repro before sign-off.
2. T5 — Judgment: Decide whether fixing only `gramps/gui/editors/editname.py` is the intended scope, or whether the analogous primary Person editor Call/Given path must be included before publication.
3. V — Validation: Perform or accept human validation of the actual Name editor workflow against the brief's success criterion.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 — C4 Verification (red→green) — DECISION OWED: decide whether static trace plus manual GUI sign-off is enough, because the artifacts provide no core `*_test.py` red→green proof and interface verification was blocked by a dirty lane rather than by the patch (`check-gates.json:33`, `check-gates.json:42`).
- [ ] T5 — T5 Judgment — DECISION OWED: decide whether the issue scope is strictly the secondary Name editor or also the primary Person editor, which has the same Call/Given validation-only-on-Call pattern (`brief.md:28`, `/home/eddie/workspace/gramps/gramps/gui/editors/editperson.py:331`, `/home/eddie/workspace/gramps/gramps/gui/editors/editperson.py:379`, `/home/eddie/workspace/gramps/gramps/gui/editors/editperson.py:392`).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: confirm the patched Name editor satisfies the real user workflow, because fitness-to-purpose is human-owned and the artifact bundle lacks a red→green GUI proof (`brief.md:15`, `check-gates.json:33`).
- [ ] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)

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
- Iteration delta (if iterating): The patch correctly fixes the Name editor (editname.py) — manual GUI confirmed that editing the Given field now immediately re-validates the Call field indicator. However, gramps/gui/editors/editperson.py (the primary Person editor) has the same stale Call/Given validation pattern. The fix must be extended to cover editperson.py before publication. The editname.py approach is correct; apply the same _revalidate_call hook there.
- By / date: Eduard Ralph / 2026-06-28

## 10. Act candidates (hints for the next Act review)
- Multi-word call names (e.g. "Johann Sebastian") remain permanently red because _validate_call splits Given into single tokens — pre-existing limitation, separate issue candidate.
