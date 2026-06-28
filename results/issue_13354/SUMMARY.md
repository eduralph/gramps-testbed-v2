# Result — issue 13354 / mediamanager-tooltip-viz-a-viz-typo

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The Media Manager tool's help/tooltip for "Convert paths from absolute to
- Success criterion: the Media Manager "absolute → relative" help text renders the word as
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the single misspelled word in the help string at mediamanager.py:640. / out of

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*13354_*.py for bundle issue_13354 — the per-fix GUI red→green cannot run; 
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (4 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# check-review.md — issue 13354 / mediamanager-tooltip-viz-a-viz-typo

**Reviewer:** Claude (advisory, no Write/Edit authority)
**Grounding:** `$PDCA_TARGET` is unset — all `path:line` citations are grounded on `patch.diff` alone.
**C5 smell-test:** No `hasattr`, no `try/except` around optional imports, no conditional runtime guards introduced; patch is a pure string-literal substitution. Smell-test: **negative**.

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief names precise location (mediamanager.py:640), exact bad string ("viz-a-viz"), exact success criterion ("vis-à-vis" or "vis-a-vis"), tight scope (single word only), test-file requirement with POTFILES.skip registration — all verifiable in patch.diff. |
| C2 Reproduction (red pre-fix) | PASS | No independent C2 gate configured (check-gates.json C2 result="none"); the gating C4-verify row reports `red-without-fix=PASS`, confirming pre-fix failure of the regression test — the red half is evidenced. |
| C3 Change | PASS | patch.diff:9–10 replaces `"viz-a-viz"` with `"vis-à-vis"` in `Convert2Rel.description`; patch.diff:14–88 adds the new test package (`__init__.py`), two targeted regression tests, and two POTFILES.skip entries — all within the brief's stated scope; no unrelated lines changed. |
| C4 Verification (red→green) | PASS | C4-verify (gating=true): `green-with-fix=PASS / red-without-fix=PASS` (check-gates.json:37–38). GUI interface verification is UNVERIFIABLE (no dogtail script for this bug) but is non-gating and expected by the brief ("expect C4 PDCA-UNVERIFIABLE … do NOT manufacture scaffolding"). |
| C5 Causal adequacy | PASS | Root cause is a misspelled string literal at patch.diff:9; fix is its exact inverse (corrected literal) with no intermediate guard, probe, or conditional — the correction is structurally complete and proportionate. |
| T1 Structure | N/A | Core-only change; T1 addon-layout rules (doc 16 §Structure) are addon-only — gate confirms "N/A: no addons-source path in patch.diff". |
| T2 Shape | PASS | New test file carries GPL header (patch.diff:23–39); Gramps coding-style conformance gate PASS with 4 non-blocking advisories; new core .py files registered in po/POTFILES.skip (patch.diff:84–85); T2-potfiles gating gate PASS. |
| T3 Runtime | PASS | Unit suite matches recorded baseline (7 known reds, unchanged); interface smoke PASS and baseline-red gone; baseline tree drift noted in gate (`recorded detached@674e3b`) is a target-state caveat, not a patch defect. |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle; gate confirms N/A. |
| T5 Judgment | PASS | Fix is minimal and precisely targeted; the two regression tests are complementary (negative: old spelling absent; positive: new spelling present); `__init__.py` correctly packages the new test directory; accented form "vis-à-vis" is the typographically correct French loanword and within brief's stated acceptable alternatives; no scope creep; prior-art check per brief found no prior fix on upstream/maintenance/gramps61. One fragility noted: `from gramps.plugins.tool.mediamanager import Convert2Rel` (patch.diff:54) will trigger GTK module-level imports — test will fail at import time in display-less environments without `DISPLAY`/Wayland. C4 PASS confirms the build environment handles this; it is a test-environment constraint, not a defect in the fix itself. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Confirm the corrected tooltip renders as "vis-à-vis" in the live GUI (Tools → Utilities → Media Manager → hover "Convert paths from absolute to relative") — automated dogtail verification was UNVERIFIABLE for this bug; a human must clear the GUI repro before the fix ships, because the only evidence of correct rendering is the string-literal test, not the rendered widget. Also confirm whether the accented form ("vis-à-vis") or ASCII form ("vis-a-vis") is the project's preferred style for translatable strings. |

---

## Notes for §6 human-clearance

- **§6-V** Validate corrected tooltip in GUI (Tools → Media Manager → hover "Convert paths from absolute to relative") visually shows "vis-à-vis"; confirm accented vs. ASCII preference for project style.
- **§6-T5-fragility** (advisory, non-blocking): if the test suite is ever run in a CI environment without a display and without `DISPLAY=:99` or similar, `mediamanager_test.py` will fail at import time due to GTK top-level imports in `mediamanager.py`. No action required for this fix, but worth recording for future test-environment hardening.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] Validation — fitness-to-purpose — Confirm the corrected tooltip renders as "vis-à-vis" in the live GUI (Tools → Utilities → Media Manager → hover "Convert paths from absolute to relative") — automated dogtail verification was UNVERIFIABLE for this bug; a human must clear the GUI repro before the fix ships, because the only evidence of correct rendering is the string-literal test, not the rendered widget. Also confirm whether the accented form ("vis-à-vis") or ASCII form ("vis-a-vis") is the project's preferred style for translatable strings.
- [x] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*13354_*.py for bundle issue_13354 — the per-fix GUI red→green cannot run; 

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
