# Check Review

Target-state caveat: `$PDCA_TARGET` was readable and `git apply --check patch.diff` succeeded; existing-source citations are grounded on `/home/eddie/workspace/gramps`, while new added-file lines are cited from `patch.diff` because the file is absent until the patch is applied.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect and success criterion as Given edits re-running Call validity so the red/black state follows current Given text (`brief.md:9`, `brief.md:15`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The target source re-derives the stale state: `_validate_call` reads Given (`gramps/gui/editors/editname.py:176`, `gramps/gui/editors/editperson.py:334`) but only Call is connected to validation (`gramps/gui/editors/editname.py:236`, `gramps/gui/editors/editperson.py:392`). |
| C3 — C3 Change | PASS | The patch adds Given-field changed hooks that force Call validation in both affected editors (`patch.diff:9`, `patch.diff:29`, `patch.diff:41`, `patch.diff:61`), matching the iteration-3 carry-forward requirement to cover `editperson.py` too (`brief.md:68`). |
| C4 — C4 Verification (red→green) | PASS | The added test drives a real `MonitoredEntry._on_change` path into production `_revalidate_call` and checks red→black and black→red transitions (`patch.diff:177`, `patch.diff:204`, `patch.diff:218`, `patch.diff:232`); the essential verification gate passed, while the dogtail advisory failed only on a dirty verification lane (`check-gates.json:33`, `check-gates.json:42`). |
| C5 — C5 Causal adequacy | PASS | The causal dependency is complete: production validation emits the custom predicate on non-empty text (`gramps/gui/widgets/validatedmaskedentry.py:1110`), and `MonitoredEntry` invokes its `changed` callback on Given changes (`gramps/gui/widgets/monitoredwidgets.py:154`), so forcing Call validation on that callback addresses the stale indicator. |
| T1 — T1 Structure | N/A | This is a core GUI/test patch with no addon path, so addon structure rules do not apply (`patch.diff:1`, `patch.diff:33`, `patch.diff:65`, `patch.diff:276`). |
| T2 — T2 Shape | PASS | The new test file includes the GPL header and is registered in `po/POTFILES.skip` as required for a new core Python test module (`patch.diff:71`, `patch.diff:284`). |
| T3 — T3 Runtime | PASS | Runtime gates report the unit baseline and GUI interface smoke as passing; the recorded baseline drift is advisory, not a new red (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this bundle, so contribution-wrapper checks are not applicable (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the artifact evidence is publication-sufficient despite the GUI red→green dogtail repro not running because of a dirty external lane; impact is confidence in end-user indicator behavior beyond the headless signal-path test (`check-gates.json:42`, `patch.diff:99`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: confirm the patched Name/Person editor behavior satisfies the Mantis/user workflow, because artifacts prove the wiring and tests but do not include a successful manual or dogtail GUI red→green run (`brief.md:32`, `check-gates.json:42`). |

## §6 Human Clearance Items

1. T5 — T5 Judgment: Human must decide whether the headless production-path test plus passing essential gate is enough to publish when the GUI dogtail advisory did not execute due an external dirty lane, not a patch failure.
2. V — Validation — fitness-to-purpose: Human must confirm the real editor workflow is fit for purpose: editing Given in both Name and Person editors should immediately update the Call field indicator without retouching Call.
