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

