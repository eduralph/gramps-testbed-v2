# Result — issue 7832 / get-age-dateless-birth-masks-dated-fallback

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: When a person has a Birth event that carries only a place (no date) plus a
- Success criterion: For a person with a Birth event lacking a date and a dated Baptism
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the date-bearing event selection used to compute a person's *age* when the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass —   · cleared stale essential-dependency.json (now passes on clean upstream)
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: 4 new failure(s) not in baseline: LifeLineChartView.collection::import_or_collection, PDFFor
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# check-review.md — issue 7832 / get-age-dateless-birth-masks-dated-fallback

**Reviewer:** Claude (advisory, artifact-only, decorrelated)
**Date:** 2026-06-27
**Inputs:** `patch.diff`, `brief.md`, `check-gates.json` (build-notes.md withheld by design)
**PDCA_TARGET:** unset — all citations grounded on `patch.diff` alone

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | brief.md is well-formed: defect, root cause at path:line, success criterion testable, scope bounded; repro instruction is reproducible |
| C2 Reproduction (red pre-fix) | PASS | No gate configured; but the pre-fix code is visible in patch.diff lines 34-36 (`if event: return event` unconditionally) — the dateless-Birth masking behaviour is mechanically certain from the diff alone |
| C3 Change | PASS | Three surgical changes: (1) `_has_usable_date` helper (patch.diff:10-17) mirroring the same validity test `get_age` applies; (2) `require_date=False` added to both fallback functions (lines 20, 51) — backward-compatible default; (3) `get_age` calls both with `require_date=True` (lines 84-85); plus test file and POTFILES.skip entry; all changes are within stated scope |
| C4 Verification (red→green) | PASS | Gate result: pass (check-gates.json C4-verify); logic independently confirmed: pre-fix `test_dateless_birth_falls_back_to_dated_baptism` would fail because the dateless Birth is returned immediately; post-fix `require_date=True` skips it and reaches the dated Baptism fallback |
| C5 Causal adequacy | PASS | Fix addresses the root cause directly (the premature return at patch.diff:34-36 is gated rather than bypassed); no capability probe / hasattr / try-fallback guard smell detected; `require_date` is a semantic parameter, not a runtime probe for an optional feature |
| T1 Structure | N/A | Core-only change; T1 addon-layout check does not apply (confirmed by gate: "N/A: no addons-source path in patch.diff") |
| T2 Shape | PASS | GPL header present on new test file (patch.diff:96-113); `po/POTFILES.skip` updated with `gramps/gen/utils/test/db_test.py` (patch.diff:250); both sub-gates pass per check-gates.json |
| T3 Runtime | NEEDS-HUMAN | Gate reports 4 new failures vs baseline (LifeLineChartView.collection::import_or_collection, PDF…); decide whether these are pre-existing infrastructure/collection failures or introduced by this patch — if pre-existing, T3 is clear; if introduced, scope and cause must be assessed |
| T4 Contribution | N/A | No commit-msg.txt or pr-description.md in bundle; gate recorded N/A; non-gating |
| T5 Judgment | PASS | Patch is minimal and symmetric (birth and death fallback treated identically); backward-compatible default preserves all non-age callers (place display etc.); `_has_usable_date` correctly triples-guards validity; fallback loop `continue` correctly scans all fallback events for a dated one; tests cover both the regression case and the non-regression case with independent dates to prevent false-positive correlation |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Confirm that Fan Chart colouring (fanchartview) is restored for a real person record with a dateless Birth + dated Baptism + dated Death — this is the stated user-visible symptom and cannot be verified without a running Gramps UI against live or fixture data |

---

## Notes for human sign-off

### §6 Items requiring human clearance

- **[ ] T3 — 4 new unit failures:** `LifeLineChartView.collection::import_or_collection` and three others (PDF-related, per gate path_line). Decide: are these pre-existing baseline regressions unrelated to `gramps/gen/utils/db.py`, or introduced by this patch? The patch touches no addon collection or PDF code, so they are likely pre-existing — but this must be confirmed by running the same suite on the unpatched branch and comparing.

- **[ ] V — Fan Chart visual regression:** Manual smoke-test required: load a Gramps database (or use the test fixture logic from `db_test.py`) and open the Fan Chart view for a person with a dateless Birth event and a dated Baptism. Confirm the person's segment acquires colour (age is now computable). The unit tests cover the `get_age` return value; they do not cover the rendering path in fanchartview.

### Additional reviewer observations (informational, not blocking)

- **`_has_usable_date` date validity check** (`bool(date) and date.get_valid() and not date.is_empty()`, patch.diff:16-17): this triple-guard is correct and consistent with the brief's claim that it mirrors what `get_age` already applies internally.
- **Death fallback symmetry:** `get_death_or_fallback` receives the same treatment; no asymmetry between birth and death paths.
- **Non-age callers unaffected:** Default `require_date=False` means every existing call site outside `get_age` retains its current behaviour. This is the correct design given the brief's explicit out-of-scope note ("displaying a birth place").
- **Prior-art check** (from brief.md triage): upstream commits `b3a5cf346f` (Black reformat) and `0502ab2af3` (`find_children`) do not touch the birth/age fallback; no closed PR found for this path. No mechanical conflict with upstream history.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 Runtime — Gate reports 4 new failures vs baseline (LifeLineChartView.collection::import_or_collection, PDF…); decide whether these are pre-existing infrastructure/collection failures or introduced by this patch — if pre-existing, T3 is clear; if introduced, scope and cause must be assessed
- [x] Validation — fitness-to-purpose — Confirm that Fan Chart colouring (fanchartview) is restored for a real person record with a dateless Birth + dated Baptism + dated Death — this is the stated user-visible symptom and cannot be verified without a running Gramps UI against live or fixture data

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
- By / date: Eduard Ralph / 2026-06-27

## 10. Act candidates (hints for the next Act review)
- PDFForms addon collection crash (`The reportlab package is required`) appears in T3-addon-unit-61 results; add to run-addon-unit-61.json baseline so it stops surfacing as a §6 delta every cycle
