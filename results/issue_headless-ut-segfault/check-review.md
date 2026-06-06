# Check Review — headless-unit-discovery-segfault

> Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`,
> `check-gates.json`. `build-notes.md` deliberately withheld — Step-0 backtrace
> and Do's own reasoning are therefore unverifiable from here; noted where it bites.

## Headline

The patch fixes a **real** headless abort (`grampletpane.py:LinkTag` class-body
`Gtk.Label` construction, guarded behind the brief-mandated `has_display()`), and
the gating **C4-verify passes** (red-without-fix / green-with-fix on the targeted
import). **But the whole-suite check fails the success criterion:** `T3-unit`
records `runner exited 133` (= 128+5 = **SIGTRAP**) with *no matching baseline
signature* — the headless `run-unit.sh` discover run **still core-dumps**, now on a
*different* (non-baselined) frame. The brief's success criterion is that the suite
"no longer emits `Trace/breakpoint trap (core dumped)`" (`brief.md:14`). It still
does. The captured cause was genuine but **incomplete**.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:14` carries a single, testable success criterion (suite completes discovery without SIGTRAP + new subprocess test exits 0 headless); scope/out-of-scope explicit (`brief.md:16`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | `check-gates.json` C4-verify `red-without-fix=PASS` confirms the new test reddens pre-fix; test is correctly subprocess-based (`patch.diff:86-92`) since a SIGTRAP can't be caught in-process. (Step-0 faulting-frame backtrace lives in withheld `build-notes.md` — not independently checkable here.) |
| C3 — C3 Change | PASS | Minimal, display-guarded fix that **reuses** `has_display()` as the brief required (`patch.diff:134` import; `:150` guard; `:161` `__init__` None-guard) — does not adopt PR #2354's over-broad `__init__.py` change. Caveat: patch adds `gramps/gui/test/headless_import_test.py` but **no `gramps/gui/test/__init__.py`**, which `brief.md:18` explicitly requires for the new test package. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` C4-verify (gating=true) = `green-with-fix=PASS / red-without-fix=PASS`. Proves the *targeted* import goes red→green; scoped to the test's two modules, not the whole suite (see T3/C5). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Contested/incomplete root cause: the captured `grampletpane:LinkTag` cause is real and fixed, yet `T3-unit` still exits 133 (SIGTRAP, new non-baseline signature) — so the stated cause does **not** fully account for the suite-level abort the brief targets. Brief's disposition hint says to iterate to Plan if isolation is incomplete (`brief.md:21`); backtrace withheld (`build-notes.md`) so completeness can't be re-derived. |
| T1 — T1 Structure | N/A | Core-only change; doc 16 §Structure is addon-source-only and no addons-source path appears in `patch.diff` (matches gate `T1-structure` N/A). The missing core test-package `__init__.py` is tracked under C3, not here. |
| T2 — T2 Shape | PASS | New file `headless_import_test.py` carries the GPL header (`patch.diff:7-24`); no diagnostic `print`; comment-only edits to `grampletpane.py`. Matches gate `T2-shape` PASS. |
| T3 — T3 Runtime | FAIL | `T3-unit` (`run-unit.sh`) **exited 133 = SIGTRAP**, new failure not in baseline (`check-gates.json` rows[6]) — the headless suite still core-dumps, contradicting the success criterion (`brief.md:14`). Additional deltas: `T3-addon-unit-60` exit 1, `T3-addon-unit-61` exit 1, `T3-interface` new `setUpClass (interface.test_smoke.SmokeTest)` failure — origin (regression vs pre-existing noise) not separable from artifacts. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (gate `T4-contribution` N/A) — nothing to check against doc 16 §Commit messages / §Contributor workflow. |
| T5 — T5 Judgment | NEEDS-HUMAN | Holistic call reserved for reviewer + human: given the residual `T3-unit` SIGTRAP, decide iterate-to-Plan (re-isolate the still-faulting frame per `brief.md:21`) vs. accept this as a correct-but-partial increment. Also resolve the missing `__init__.py` (C3) before any ready-mark. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always human at sign-off. Fitness is **not** demonstrated by the artifacts: the load-bearing success criterion (suite no longer segfaults headless) is unmet — `T3-unit` exit 133. Human must validate whether the delivered change meets purpose or requires re-scoping. |

## §6 — Items the human must clear (NEEDS-HUMAN)

1. **C5 — Causal adequacy / contested root cause.** The fixed cause
   (`grampletpane:LinkTag`) is real but does not explain the *still-present*
   suite SIGTRAP (`T3-unit` exit 133, new non-baseline signature). Confirm
   against the withheld Step-0 backtrace in `build-notes.md` whether a second
   headless-fatal class-body widget construction remains, and whether the brief's
   "iterate to Plan if isolation incomplete" hint (`brief.md:21`) should fire.

2. **T5 — Judgment.** Decide disposition: iterate-to-Plan to isolate the residual
   abort vs. accept a correct-but-partial fix. Settle the missing
   `gramps/gui/test/__init__.py` (brief-required for the new test package,
   `brief.md:18`; absent from `patch.diff`) before the PR is marked ready.

3. **V — Validation fitness-to-purpose.** Success criterion (`brief.md:14`:
   "`run-unit.sh` no longer emits `Trace/breakpoint trap (core dumped)`") is
   **not met** per `T3-unit` exit 133. Human must validate fitness at sign-off;
   on current artifacts the increment does not satisfy the stated purpose.

## Note on residual T3 reds (advisory, not a gate)

`T3-addon-unit-60/61` (exit 1) and `T3-interface` (new `SmokeTest.setUpClass`
failure) are deltas outside the baseline. The brief scopes out "other unrelated
`T3-unit` baseline reds" but does not pre-clear *new* addon/interface deltas;
whether the `grampletpane` edit perturbed the interface smoke path, or these are
unrelated environment noise, cannot be separated from the artifacts alone and is
flagged for the human under T5.
