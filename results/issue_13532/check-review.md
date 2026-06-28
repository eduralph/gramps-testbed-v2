# Check Review

Target-state caveat: `$PDCA_TARGET` is readable but is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive`, not the brief's `maintenance/gramps61`; the patch applies cleanly there, so unchanged pre-patch source citations use `$PDCA_TARGET` and added-code/test citations use `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect, success criterion, invariant, and scope around fan-chart name labels respecting the active name format (`brief.md:9`, `brief.md:12`, `brief.md:15`, `brief.md:25`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The user-visible repro is concrete (`brief.md:30`) and the configured C4 unit red-without-fix gate reports PASS (`check-gates.json:33`), establishing pre-fix red behavior for the exercised production name path. |
| C3 — C3 Change | PASS | The patch replaces the target's hard-pinned two-line formats (`gramps/gui/widgets/fanchart.py:151`, `gramps/gui/widgets/fanchart.py:743`) with active-format splitting/rendering (`patch.diff:19`, `patch.diff:221`) and adds name-format refresh wiring (`patch.diff:234`, `patch.diff:246`, `patch.diff:258`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: unit red→green passed (`check-gates.json:33`), but the GUI AT-SPI repro for the actual chart workflow was skipped/unverifiable (`check-gates.json:42`); decide whether production-path unit proof plus source review is sufficient for this GUI-scoped fix. |
| C5 — C5 Causal adequacy | PASS | The pre-fix cause is the widget registering/drawing fixed `%l` and `%f %s` formats (`gramps/gui/widgets/fanchart.py:151`, `gramps/gui/widgets/fanchart.py:743`), and the patch routes both lines through the active `NameDisplay` format plus rebuild-on-nameformat-change (`patch.diff:45`, `patch.diff:225`, `patch.diff:238`). |
| T1 — T1 Structure | N/A | No addon layout is touched; the gate classifies structure as addon-only and not applicable to this core patch (`check-gates.json:60`). |
| T2 — T2 Shape | PASS | Shape and POTFILES gates pass, including registration of the new core test in `po/POTFILES.skip` (`check-gates.json:69`, `check-gates.json:78`, `patch.diff:266`). |
| T3 — T3 Runtime | PASS | Runtime baselines passed: core unit suite matched known baseline and GUI smoke was green, with only baseline-drift caveats noted by the gate (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in the bundle, so the contribution-wrapper gate is not applicable (`check-gates.json:105`). |
| T5 — T5 Judgment | PASS | The edit stays within the named scope, adds focused regression coverage for the production name path, and leaves the remaining user-facing GUI confirmation explicitly owed under C4/V rather than hidden. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must confirm the patched Fan Chart/Descendant/2-way views visibly follow Display -> Name format after preference changes, because automated GUI validation did not exercise that workflow (`brief.md:12`, `check-gates.json:42`). |

## §6 Human Clearance Items

1. C4 verification: decide whether to accept the passed unit red→green evidence for `NameDisplay.display_two_lines` and the reviewed `nameformat-changed` wiring despite the skipped GUI AT-SPI repro.
2. V validation: manually confirm in Gramps that changing Display -> Name format updates Fan Chart, Descendant Fan Chart, and 2-way Fan Chart labels as intended.
