# Check Review

## 1. Target Caveat

`$PDCA_TARGET` was readable at `/home/eddie/workspace/gramps`, but it was on branch `fix/bug-8850-gedcom-import-cal-date-case-sensitive`, not the requested `maintenance/gramps61` target in `brief.md:23`. The patch applies cleanly to that target state, so this is a target-state caveat, not a patch defect. Existing-source citations below use `$PDCA_TARGET`; added lines not present in the target are cited from `patch.diff`.

## 2. Verdict Table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the stale Call-name indicator defect, success criterion, invariant, and in/out scope clearly enough to review against (`brief.md:9`, `brief.md:15`, `brief.md:19`, `brief.md:28`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The pre-fix target validates Call against Given in `_validate_call`, connects validation only on `call_field`, and gives `given_field` no change hook, matching the stale red/black repro (`gramps/gui/editors/editname.py:173`, `gramps/gui/editors/editname.py:223`, `gramps/gui/editors/editname.py:236`). |
| C3 — C3 Change | PASS | The patch adds a Given-change callback that force-validates the Call field and wires it into `given_field`, directly targeting the missing revalidation edge (`patch.diff:90`, `patch.diff:100`). |
| C4 — C4 Verification (red→green) | FAIL | The gate reports red/green, but the added test only imports/calls the newly added utility predicate and never drives the Given-field changed callback or forced Call validation path (`check-gates.json:33`, `patch.diff:153`, `patch.diff:177`, `patch.diff:187`). |
| C5 — C5 Causal adequacy | PASS | `MonitoredEntry._on_change` invokes the supplied `changed` callback, and forced validation emits the `validate` signal and updates valid/invalid state, so the new hook should recompute the indicator from current Given text (`gramps/gui/widgets/monitoredwidgets.py:154`, `gramps/gui/widgets/validatedmaskedentry.py:1075`, `gramps/gui/widgets/validatedmaskedentry.py:1113`, `gramps/gui/widgets/validatedmaskedentry.py:1117`). |
| T1 — T1 Structure | N/A | The patch is core-only, with no addon path or addon layout surface to assess (`patch.diff:1`, `patch.diff:55`, `patch.diff:108`). |
| T2 — T2 Shape | PASS | The new Python files have project GPL headers and are registered in `po/POTFILES.skip`; the unrelated extra POTFILES scope is deferred to T5 (`patch.diff:7`, `patch.diff:114`, `patch.diff:208`, `patch.diff:216`). |
| T3 — T3 Runtime | PASS | The artifacted gates report the core unit baseline and GUI interface smoke as passing, with only baseline drift caveats (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` is in the bundle, so contribution wrapper review does not apply (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the `plugins/lib/test` POTFILES additions are acceptable stacked-base bookkeeping or must be removed, because they are outside the call-name scope stated in the brief (`patch.diff:224`, `brief.md:28`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human sign-off must confirm the Name editor's actual Call-field red/black indicator follows Given edits, because final fitness-to-purpose is always human and the supplied test is predicate-level only (`brief.md:15`, `patch.diff:177`, `patch.diff:187`). |

## 6. Human-Clear Items

1. T5 scope judgment: decide whether the unrelated-looking `po/POTFILES.skip` additions for `gramps/plugins/lib/test/__init__.py` and `gramps/plugins/lib/test/libsourceview_test.py` are intentional stacked-base/prerequisite bookkeeping or should be removed from this patch.
2. Validation fitness-to-purpose: confirm in the actual Name editor that changing Given revalidates the Call field in both directions, red to black and black to red, without re-touching Call.
