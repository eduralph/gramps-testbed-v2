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
