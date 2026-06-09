# Check review — issue 8796 / viewmanager-empty-views-indexerror

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json` (build-notes.md withheld by design). Every Basis
> below is re-derived from those artifacts, not copied from the gate text.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Brief carries a concrete, load-bearing success criterion (`brief.md:10`: empty available-view set → init without raising, opens with no active page; red→green contract stated) and an explicit totality invariant (`brief.md:11`). Spec is well-formed and testable. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Test drives the **real** `views_to_show` / `init_interface` / `__change_page` / `config_view` on the genuine `gramps.gui.viewmanager` module (`patch.diff:218-253`); `check-gates.json` `C4-verify` records `red-without-fix=PASS`. Caveat: red is demonstrated with the test file run in isolation, not under whole-suite discovery (see C4/T3). |
| C3 — C3 Change | PASS | Source-level fix: `views_to_show` returns `(None, None, [])` for the empty set (`patch.diff:58-65`); `init_interface` unpacks the 3-tuple and only navigates when `current_cat is not None` (`patch.diff:11-24`). Non-empty path is byte-equivalent to the prior `defaults[0/1/2]` unpack. Citations present in-comment; diff is clean and localized. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` `C4-verify`: `green-with-fix=PASS / red-without-fix=PASS` (gating row, the only one). BUT this is the narrow mechanical green — it runs the new file alone. The whole-suite signal (T3) **contradicts** it with a non-empty regression delta, so C4-green ≠ "change is clean under the suite." |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Always-human (contested root-cause). The root-cause *approach* was rejected twice: iter-1 (test leaks into shared suite) and iter-2 (use a by-construction upstream fix, not site-local downstream guards). This patch is a hybrid — it fixes the source (`views_to_show` `patch.diff:58-65`) but **retains 2 of 3 downstream guards** (`__change_page` `patch.diff:32-38`, `config_view` `patch.diff:47-50`) instead of demonstrating their unreachability post-fix. Whether that satisfies the iter-1 ask ("prove `__change_page` unreachable or guard it") and the iter-2 ask (by-construction totality) is a human judgment. |
| T1 — T1 Structure | N/A | Core-only change (`gramps/gui/viewmanager.py` + `gramps/gui/test/viewmanager_test.py`); no addons-source path in `patch.diff`. §Structure (doc 16) is addon-only. Matches gate `T1-structure`. |
| T2 — T2 Shape | PASS | New test file carries the GPL header (`patch.diff:75-92`); only advisory is `print("REPRO_OK")` in the child program (`patch.diff:253`), which is the test's pass-marker, not production output. Matches gate `T2-shape` (1 conform, 2 advisory). |
| T3 — T3 Runtime | FAIL | `check-gates.json` records **both** runtime rows `fail`: `T3-unit` DELTA 7 new failures (`imports_test::test_imp_3_4`) and `T3-interface` DELTA 1 new failure (`SmokeTest setUpClass`) — **byte-identical to the iter-1 and iter-2 carry-forwards** (`brief.md:29-30, 36-37`). The rewritten subprocess-per-scenario harness prevents `sys.modules` leakage but not disk side-effects from importing real `gramps.*` in the child (plugin/config cache under the gramps home), nor a stale/environmental baseline — an identical delta surviving a fully rewritten test points at one of those. iter-2's explicit "Confirm T3 is green against the new patch" is **unmet**. Advisory (gating:false), but it is the exact basis on which both prior iterations were rejected. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle. Matches gate `T4-contribution`. |
| T5 — T5 Judgment | NEEDS-HUMAN | Reviewer+human. Test drives production methods (good) but still **reconstructs the post-`__init__` state via `ViewManager.__new__` + hand-set attributes** (`patch.diff:193-215`) and stubs `__build_tools_menu`/`__build_report_menu` — exactly the "reconstructed-`__new__`-input drift surface" iter-2 T5 asked to shrink by moving toward the real `init_interface` entry point. That ask appears unaddressed; subprocess-per-scenario is heavy. Test-design fitness is a judgment call. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. The manual GUI repro on `maintenance/gramps61` (hide every view plugin, restart, confirm no `IndexError`, app opens with no active page) was unrun in iter-1 and iter-2 (`brief.md:28, 35`) and there is no artifact evidencing it was run for this iteration. Must be run and accepted before release. |

## §6 — items the human must clear

1. **C5 — contested root-cause / scope.** Decide whether the hybrid (source fix in
   `views_to_show` + `init_interface` guard, but retained `__change_page` and
   `config_view` downstream guards) satisfies the iter-2 "by-construction, total
   over the empty set" directive, or whether the two remaining guards must be shown
   unreachable post-fix and removed. (`patch.diff:32-38`, `:47-50`.)
2. **T5 — test-design judgment.** Accept or reject the `__new__`-reconstructed
   ViewManager + subprocess harness given iter-2's request to move the regression
   toward the real `init_interface` entry and shrink the reconstruction drift
   surface (`patch.diff:193-215`).
3. **V — manual GUI validation unrun.** Execute the brief's repro and confirm the
   no-active-page outcome before sign-off.

## Blocking flag (not a §6 human-judgment item — a re-run/diagnosis task)

- **T3 is RED and identical to both rejected iterations.** Overall gate reads
  `pass` only because T3 is advisory and C4 (isolation-only) is the lone gating row
  — but T3 is the precise basis on which iter-1 and iter-2 were rejected, and the
  carry-forward set "confirm T3 green" as a release precondition. The byte-identical
  delta across three different test implementations suggests the failures are **not
  prevented by the subprocess `sys.modules` isolation** — re-derive whether they are
  a filesystem/cache side-effect of importing real `gramps.*` in the child, a stale
  gate artifact, or a contaminated/flaky baseline, before treating this as
  releasable. As it stands, the artifacts do **not** show a clean whole-suite run.
