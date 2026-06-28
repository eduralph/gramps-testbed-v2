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
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*12110_*.py for bundle issue_12110 — the per-fix GUI red→green cannot run; 
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

Target-state caveat: `$PDCA_TARGET` is readable at `/home/eddie/workspace/gramps` and `patch.diff` applies cleanly there, but that checkout is dirty and on a different branch than the brief target; existing pre-fix source citations use the target checkout, while added-file/added-line citations use `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the stale Call-name indicator defect, success criterion, invariant, and scope around `gramps/gui/editors/editname.py` (`brief.md:9`, `brief.md:15`, `brief.md:19`, `brief.md:28`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix `given_field` has no `changed` callback while only `call_field` connects validation, so changing Given cannot re-run Call validation (`gramps/gui/editors/editname.py:223`, `gramps/gui/editors/editname.py:236`). |
| C3 — C3 Change | NEEDS-HUMAN | DECISION OWED: the patch wires Given changes to forced Call validation, but also adds a new production helper under `gramps/gen/utils` despite the brief expecting no new files except a possible test module; human must decide whether that API/scope expansion is acceptable (`patch.diff:1`, `patch.diff:111`, `patch.diff:130`, `brief.md:43`). |
| C4 — C4 Verification (red→green) | PASS | The focused gate reports green-with-fix and red-without-fix PASS, and the added tests assert both red→black and black→red transitions after a Given-name change triggers revalidation (`check-gates.json:33`, `check-gates.json:37`, `patch.diff:247`, `patch.diff:265`). |
| C5 — C5 Causal adequacy | PASS | The observed cause is a missing revalidation trigger on Given changes, and the patch makes `_revalidate_call` force `call_field.obj.validate(force=True)` through the same predicate used by `_validate_call` (`gramps/gui/widgets/monitoredwidgets.py:154`, `gramps/gui/widgets/validatedmaskedentry.py:1110`, `patch.diff:105`, `patch.diff:121`). |
| T1 — T1 Structure | N/A | Core-only patch with no `addons-source` path, so addon structure rules do not apply (`check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | New Python files carry GPL headers and both new files are registered in `po/POTFILES.skip` (`patch.diff:7`, `patch.diff:140`, `patch.diff:292`, `patch.diff:300`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: full core unit runtime is inconclusive because the runner exited before producing JUnit XML, while GUI smoke passed; human must decide whether the focused C4 evidence is sufficient or a rerun is required (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` is present in the artifact bundle, so contribution-wrapper checks do not apply (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: the headless test uses a fake validatable entry and no `engine/interface/test_bug_*12110_*.py` GUI repro exists, so a human must accept whether this verifies the actual GTK signal path enough for publication (`patch.diff:192`, `patch.diff:208`, `check-gates.json:42`, `check-gates.json:46`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: final fitness turns on whether the user-visible Name editor indicator now behaves correctly in real workflow after Given edits, which requires human sign-off against the brief’s success criterion (`brief.md:15`, `brief.md:32`). |

## §6 Human Clearance Items

1. C3 scope/API expansion: decide whether adding `gramps/gen/utils/callname.py` is acceptable for this narrowly scoped editor fix, or whether the callback/predicate should remain local to `editname.py`.
2. T3 runtime coverage: decide whether to accept the focused red→green C4 result despite the full core unit runner pre-test crash, or require a clean unit baseline rerun.
3. T5 verification shape: decide whether the helper-level fake-entry test is sufficient evidence for the GTK Given-field `changed` wiring, or require a direct `EditName._revalidate_call`/interface repro.
4. V fitness-to-purpose: confirm in the intended Name editor workflow that Given-name edits update the Call field red/black state without re-touching Call.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C3 — C3 Change — DECISION OWED: the patch wires Given changes to forced Call validation, but also adds a new production helper under `gramps/gen/utils` despite the brief expecting no new files except a possible test module; human must decide whether that API/scope expansion is acceptable (`patch.diff:1`, `patch.diff:111`, `patch.diff:130`, `brief.md:43`).
- [ ] T3 — T3 Runtime — DECISION OWED: full core unit runtime is inconclusive because the runner exited before producing JUnit XML, while GUI smoke passed; human must decide whether the focused C4 evidence is sufficient or a rerun is required (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`).
- [ ] T5 — T5 Judgment — DECISION OWED: the headless test uses a fake validatable entry and no `engine/interface/test_bug_*12110_*.py` GUI repro exists, so a human must accept whether this verifies the actual GTK signal path enough for publication (`patch.diff:192`, `patch.diff:208`, `check-gates.json:42`, `check-gates.json:46`).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: final fitness turns on whether the user-visible Name editor indicator now behaves correctly in real workflow after Given edits, which requires human sign-off against the brief’s success criterion (`brief.md:15`, `brief.md:32`).
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*12110_*.py for bundle issue_12110 — the per-fix GUI red→green cannot run; 

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
- Iteration delta (if iterating): C3 scope rejected: the call-name validity predicate and revalidation trigger must stay local to gramps/gui/editors/editname.py. Do not introduce gramps/gen/utils/callname.py or any other new production file; inline the logic in editname.py directly. T3 unit-runner crash is a known infrastructure issue — do not block on it. T5/V: if headless GTK signal-path testing is not feasible, manual confirmation of the Name editor behaviour is sufficient.
- By / date: Eduard Ralph / 2026-06-28

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
