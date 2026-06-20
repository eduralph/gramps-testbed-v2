# Result — issue headless-ut-segfault / ** headless-unit-discovery-segfault

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** the whole-suite headless core unit run (`engine/scripts/ubuntu/run-unit.sh` → `GRAMPS_RESOURCES=. python3 -m xmlrunner discover`, no `$DISPLAY`) dies `Trace/breakpoint trap (core dumped)` during test discovery, reddening `T3-unit`. **The underlying defect is not yet isolated** (so states the baseline manifest, `engine/baselines/run-unit.json`). The prior draft's theory — that `class PersistentTreeView(Gtk.TreeView)` subclassing at import (via `gramps/gui/widgets/__init__.py:45`) crashes the interpreter — is **falsified**: (1) subclassing `Gtk.TreeView`/`Gtk.EventBox` with `DISPLAY` unset defines cleanly, exit 0 — a GType registration needs no display; (2) `gramps/gui/widgets/photo.py:45` `class Photo(Gtk.EventBox)` does the same subclass-at-import *earlier* in the import order (`widgets/__init__.py:30`, before `:45`), so it would crash first if that were the trigger. The real faulting frame is unknown and must be captured before any fix.
- Success criterion: ** the headless core unit suite completes discovery and runs without segfaulting (`run-unit.sh` no longer emits `Trace/breakpoint trap (core dumped)`), and the new subprocess regression test that reproduces the crashing import/call chain exits 0 headless.
- Repo + branch target: ** `gramps @ maintenance/gramps61` (core fix per INTEGRATION §2, forward-merged to `master`). If isolation pins the cause outside core gramps, iterate to Plan to re-resolve the target.
- Scope (one logical fix) / out of scope: ** (1) **isolate** the discovery-time segfault on an *unmodified* `maintenance/gramps61` checkout in Docker — capture the actual faulting frame; (2) apply the **minimal** headless-safe fix for that captured cause; (3) ship a subprocess regression test. / **out of scope:** the persistenttreeview-subclass theory (falsified); PR #2354's blanket `widgets/__init__.py` `else: __all__ = []` change (breaks ~30 importers); **adding a new `has_gtk_display()` helper** — `gramps.gen.constfunc.has_display()` already exists (proper `Gtk.init_check()` + `Gdk.Display.get_default()` probe) and `gui/utils.py:61` already imports it, so reuse it; any behaviour change when a display **is** present; fixing other unrelated `T3-unit` baseline reds.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix → **VERIFY/ISOLATE FIRST.** If the Step-0 backtrace shows the cause is materially different from anything a minimal core patch can safely address (e.g. a third-party/C library crash, or a cause outside core gramps), stop and **iterate to Plan** with the captured evidence rather than forcing a fix. Once green-baseline, drop the core-dump signature from `engine/baselines/run-unit.json` and re-promote `T3-unit` to gating.
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 133 with no parsed failures and no matching baseline signature (a new failure 
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Contested/incomplete root cause: the captured `grampletpane:LinkTag` cause is real and fixed, yet `T3-unit` still exits 133 (SIGTRAP, new non-baseline signature) — so the stated cause does **not** fully account for the suite-level abort the brief targets. Brief's disposition hint says to iterate to Plan if isolation is incomplete (`brief.md:21`); backtrace withheld (`build-notes.md`) so completeness can't be re-derived.
- [x] T5 — T5 Judgment — Holistic call reserved for reviewer + human: given the residual `T3-unit` SIGTRAP, decide iterate-to-Plan (re-isolate the still-faulting frame per `brief.md:21`) vs. accept this as a correct-but-partial increment. Also resolve the missing `__init__.py` (C3) before any ready-mark.
- [x] V — Validation — fitness-to-purpose — Always human at sign-off. Fitness is **not** demonstrated by the artifacts: the load-bearing success criterion (suite no longer segfaults headless) is unmet — `T3-unit` exit 133. Human must validate whether the delivered change meets purpose or requires re-scoping.

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
- By / date: Eduard Ralph / 2026-06-06

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
