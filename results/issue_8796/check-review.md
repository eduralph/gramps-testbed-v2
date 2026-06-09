# Check review — issue 8796 / viewmanager-empty-views-indexerror (iteration 4)

> Advisory, artifact-only, decorrelated. Inputs: patch.diff, brief.md, check-gates.json
> (build-notes.md withheld by design). Verdicts re-derived from the artifacts, not
> read off the builder's notes.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | brief.md:10 states a concrete, falsifiable success criterion (zero available views → init interface raises nothing, opens with no active page) + an explicit totality invariant (brief.md:11). Scope/out-of-scope are bounded (brief.md:14). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Red confirmed: check-gates `C4-verify: red-without-fix=PASS`. Re-derived: pre-fix `views_to_show([])` returns `(0,0,[])` (old body, patch.diff:147-170), so `assertEqual(...,(None,None,[]))` (patch.diff:66,70) fails. Caveat: it asserts the *causal return value*, not the literal `IndexError` the success criterion names — the real-path IndexError repro is absent (routed to T5/V). |
| C3 — C3 Change | PASS | Single coherent change: extract `views_to_show` to GTK-free `viewmanagerutils.py` (patch.diff:228-268), re-import + drop in-file copy (patch.diff:83,143-170), guard navigation in `init_interface` (patch.diff:100-106), retain `__change_page`/`config_view` guards (patch.diff:114-121,130-135). No circular import (viewmanagerutils pulls only `gramps.gen.config`). Empty-set path is the only behavioural change; non-empty path byte-identical → minimal per §1.1. |
| C4 — C4 Verification (red→green) | PASS | Gating row green: check-gates `C4-verify: green-with-fix=PASS / red-without-fix=PASS`, `overall: pass`. Re-derived both directions on `views_to_show([])`: `(0,0,[])`→red, `(None,None,[])`→green. Both `use_last=False` and `use_last=True` cases hold (guard precedes the `if use_last` block, patch.diff:241-247). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause (`views_to_show([])` collapsing to `(0,0,[])`) is fixed by construction (patch.diff:241-247) + non-navigation guard — satisfies the iter-2/iter-3 by-construction directive. But two downstream guards are *retained* with reachability claims (`__change_page` via `_post_load_newdb_gui` viewmanager.py:1221 → `get_current_page()==-1`; `config_view` via action viewmanager.py:528) that artifact-only Check cannot verify against source. Keep-vs-remove (symptom-vs-by-construction) and reachability are a human call per the brief's C5 oracle. |
| T1 — T1 Structure | N/A | Core-only change; no addons-source path in patch.diff. §Structure is addon-only (matches check-gates T1-structure path_line). |
| T2 — T2 Shape | PASS | GPL header present on both new files (patch.diff:7-24, 182-202); check-gates `T2 ✓ shape: 1 file(s) conform … (2 advisory)`. No `print()` introduced. |
| T3 — T3 Runtime | NEEDS-HUMAN | Both advisory runtime gates FAIL: 7 new unit deltas (`imports_test::test_imp_3_4`, check-gates T3-unit) + 1 GUI-smoke delta (check-gates T3-interface). This patch carries **no** sys.modules stubbing / subprocess harness (cf. iter-1 leak), yet the same deltas persist byte-for-byte — corroborating the iter-1/2/3 environmental attribution (missing bsddb backend / Glade dirname / stale baseline). Artifact-only Check cannot confirm the attribution; human must accept these as environmental, not patch-induced. |
| T4 — T4 Contribution | N/A | No commit-msg.txt / pr-description.md in the bundle (draft-only per STOP discipline); matches check-gates T4-contribution path_line. |
| T5 — T5 Judgment | NEEDS-HUMAN | The clean unit test of the production `views_to_show` satisfies iter-3 ask #1, and reuses the real function (not a parallel re-impl, §3.4). But iter-3 ask #2 — a dogtail interface test driving the **real** `init_interface` entry, doubling as automated V — is undelivered. No automated test exercises `init_interface`→`goto_page` end-to-end, so the literal startup `IndexError` the success criterion names is never reproduced by CI. Whether the function-level test alone is sufficient gating coverage is a human judgment. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Manual GUI repro (hide every view plugin on maintenance/gramps61, restart, confirm no IndexError + app opens with no active page) is recorded unrun across iter-1/2/3 (brief.md:28,35,42) and no automated dogtail substitute ships this iteration. Always-human; must be run and accepted before sign-off. |

## §6 — items the human must clear (NEEDS-HUMAN)

1. **C5 — causal adequacy / retained guards.** Confirm the two downstream guards
   (`__change_page` patch.diff:114-121, `config_view` patch.diff:130-135) are
   genuinely reachable on the empty-view set independently of `init_interface`
   (the recorded entry points: `_post_load_newdb_gui` → `__change_page(get_current_page()==-1)`
   at viewmanager.py:1221; the ConfigView accelerator at viewmanager.py:528). If
   reachable, retention is justified; if not, iter-2's by-construction directive
   asks for their removal. Reachability is asserted in comments but unverifiable from
   the artifacts alone.

2. **T3 — advisory runtime reds.** Accept (or reject) the attribution that the 7 unit
   deltas + 1 smoke delta are environmental and not caused by this patch. Supporting
   evidence re-derived here: this iteration removed the sys.modules stubbing that was
   the suspected iter-1 leak, yet the deltas persist unchanged — consistent with a
   stale baseline / missing backend rather than the patch. Confirmation needs the
   build/run environment, which is outside the Check bundle.

3. **T5 — test coverage judgment.** Decide whether the function-level
   `views_to_show([])` unit test is adequate gating coverage given the absence of the
   iter-3-requested real-entry (dogtail) test. The shipped test never drives
   `init_interface`/`goto_page`, so the actual startup `IndexError` and the no-active-page
   end state are not asserted by any automated test.

4. **V — fitness-to-purpose.** Run the manual GUI repro on maintenance/gramps61 and
   confirm: no `IndexError` at startup, main window opens with no active page. Unrun to
   date; with no automated dogtail test landing this iteration, manual validation is the
   only V evidence available and must precede release.

## Reviewer note (advisory, non-gating)

C2/C4 are GREEN at the unit level and the source fix is minimal and well-targeted. The
open risk is **coverage altitude**, not the fix logic: every iteration's gating
regression has stopped at the `views_to_show` return value, while the success
criterion (brief.md:10) and iter-3's directive both call for a test that drives the
real navigation path and observes the `IndexError` going away. Until that test exists
or V is run manually, "no startup crash" is verified only by inference from the
function's return value, not by exercising the crash site (`goto_page`
`self.current_views[cat_num]=view_num`).
