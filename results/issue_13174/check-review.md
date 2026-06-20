# Check review — issue 13174 / addon-manager-refresh-missing-listing-crash

Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
`brief.md`, `check-gates.json` (`build-notes.md` withheld by design). Every Basis
below is re-derived from the artifacts, not copied from the gate output.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:10–11 gives a concrete success criterion + invariant ("fails gracefully… no dangling window… subsequent valid refresh still works"); the spec is well-formed and testable. |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | The cancelled-dispatch tests (utils_test.py:170–193) target `AddonRefreshDispatch`, a class **this same patch introduces** (patch.diff:1–95); their red pre-fix is an `ImportError`, not the dangling-window crash. Whether that proxy is a genuine reproduction depends on the unverified root-cause model — see C5. |
| C3 — C3 Change | PASS | Coherent diff: new core helper (_addonrefresh.py), headless test, GUI wiring in _windows.py (patch.diff:198–247), and POTFILES.skip registration (patch.diff:252–268) per brief.md:18. |
| C4 — C4 Verification (red→green) | PASS | Gating gate C4-verify reports green-with-fix=PASS / red-without-fix=PASS (check-gates.json:33–39). Mechanically the suite flips red→green; note the red is driven by the missing patch-introduced class (see C2), so it verifies the proxy contract, not the GUI crash path. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Contested root cause. The fix guards the *window-closed-mid-refresh* race (_windows.py close()/cancel, patch.diff:231–247), but the brief repro (brief.md:15) is an immediate crash on **first Refresh with no window-close step**. If the window stays open, `deliver` runs while `alive` and calls `load_addons` exactly as before (patch.diff:83–95, 235) — the patch does not change the thread `load_addons` runs on. Causal link between the gate and the reported crash is unverified from artifacts. |
| T1 — T1 Structure | N/A | The T1 gate checks *addon* layout (folder==id, target_version, .gpr.py); this is a **core** patch (brief.md:12), not an addon. Gate reported `fail` "no .gpr.py" (check-gates.json:51–56), but the rule is misapplied — non-gating and inapplicable here. |
| T2 — T2 Shape | PASS | GPL headers present on both new files (patch.diff:7–23, 102–118); gate T2 pass, 2 advisory print() notes (check-gates.json:60–66). |
| T3 — T3 Runtime | PASS | T3-unit and T3-interface both match recorded baseline known-reds (check-gates.json:69–84). Advisory only: "baseline tree drift: recorded detached@674e3b" — worth a glance but non-gating. |
| T4 — T4 Contribution | N/A | No commit-msg.txt or pr-description.md in the bundle (check-gates.json:87–93); consistent with brief.md:25–27 STOP discipline (draft-only until sign-off). |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle is reviewer + human sign-off. Craft is clean (documented, headered, headless-testable). Open judgment: a new dispatch abstraction tested as a proxy vs. a simpler teardown/idle-add guard, and whether testing the proxy instead of the GUI path is the right altitude given brief.md:16's `PDCA-UNVERIFIABLE` escape hatch. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Does the change actually stop the user-reported first-Refresh crash (brief.md:10,15)? No headless test exercises the real GUI dangling-window path, and the repro does not involve closing the window — fitness-to-purpose must be confirmed by a human (ideally a live or interface repro). |

## §6 — Items the human must clear

Each NEEDS-HUMAN row above lands here:

1. **C2 / C5 (linked) — root cause vs. repro mismatch.** The patch's theory is a
   *late callback after the window is torn down*. The brief's repro is an
   immediate crash on the **first** Refresh against a 404 listing, with no
   documented window-close. As written, when the window is still open the
   dispatch is `alive` and `deliver` calls `load_addons` unchanged — so the
   reported repro path appears **unaddressed** by the gate. A human must confirm
   the actual crash mechanism (jralls' note 6) and whether closing-the-window is
   really on the reported repro path. If it is not, this fix may pass its tests
   and still leave the user-visible crash live.

2. **C2 — reproduction is a proxy.** `AddonRefreshDispatch` is new in this patch;
   the red pre-fix for the dispatch tests is an import error, not the crash. The
   real GUI dangling-window path in `_windows.py` is exercised by **no** headless
   test. Decide whether this satisfies C4's red→green intent or should be flagged
   `PDCA-UNVERIFIABLE` per brief.md:16, with the interface test
   (`tests/interface/test_bug_13174_addon_refresh.py`) carrying the real
   reproduction.

3. **T5 — design altitude.** Confirm the new gate abstraction is the right fix
   shape (vs. a simpler teardown/idle-add guard), and that proxy-level testing is
   acceptable here.

4. **V — fitness-to-purpose.** Human sign-off that the user's crash is actually
   prevented, not just that the helper's unit contract holds.

## Reviewer notes (re-derived, non-gating)

- **`get_addons` test may be green pre-fix.**
  `test_missing_listing_returns_empty_without_raising` (utils_test.py:142–147)
  asserts existing `get_addons` behavior. If `get_addons` already returns `[]`
  for a missing listing (it touches no patched code), this test passes both
  before and after the fix — it is a useful invariant guard but **not** a
  regression test for the crash. Confirm whether it contributes to the C4
  red→green at all.

- **T1 gate is a false positive**, not a defect in the patch: an addon-structure
  rule fired against a core change. Worth correcting in the gate config so it
  does not recur, but it does not reflect on this diff.

- **Mechanical-green caveat (C4).** Per the standing discipline that a green
  check is not a correctness verification: gate C4-verify proves the helper test
  suite flips red→green and that the new file imports — it does **not** prove the
  Gtk draw-cycle dangling-pointer crash is gone. That gap is the substance of
  items 1–2 above.
