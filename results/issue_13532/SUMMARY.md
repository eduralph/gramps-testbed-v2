# Result — issue 13532 / fanchart-view-respects-name-format

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The Fan Chart view (and the related Descendant / 2-way fan views) does not
- Success criterion: With a given active "Name format", the names drawn in the Fan
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the fan-chart view rendering names without applying the active name-format

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
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 5 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C4 — C4 Verification (red→green) — DECISION OWED: unit red→green passed (`check-gates.json:33`), but the GUI AT-SPI repro for the actual chart workflow was skipped/unverifiable (`check-gates.json:42`); decide whether production-path unit proof plus source review is sufficient for this GUI-scoped fix.
- [x] V — Validation — fitness-to-purpose — DECISION OWED: a human must confirm the patched Fan Chart/Descendant/2-way views visibly follow Display -> Name format after preference changes, because automated GUI validation did not exercise that workflow (`brief.md:12`, `check-gates.json:42`).
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
