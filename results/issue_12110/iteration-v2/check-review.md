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
