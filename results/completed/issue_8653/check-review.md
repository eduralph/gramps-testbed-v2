# Check review — issue 8653 / deep-connections-excludes-start-person (iteration 2)

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json` (build-notes.md withheld by design). Each Basis
> below is re-derived independently; `path:line` cites the artifact I checked.
>
> **Verification limit I'm honest about:** I am blocked from reading the full
> production `DeepConnectionsGramplet.py` — only the diff hunks are in-bundle and
> the addons-source checkout is outside my allowed roots. Verdicts that depend on
> un-diffed lines of `main()` (the seed/dequeue/self-detection logic, the
> placement of the "No Home Person set" guard relative to the call site) are
> reasoned from the diff plus the C4 gate's behavioural red→green, and flagged.

## Verdict table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | Success criterion is concrete and testable — Home only as terminal `"self"` root, never an intermediate anchor, chain still connects active→Home (brief.md:12); the test encodes exactly this triad (`assertNotIn "D"` in intermediates, `root[1]=="D"`, count==1: patch.diff:354-372). Spec and oracle agree; no gate, `result:none` (check-gates.json:6-12). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Re-traced: pre-fix `main()` produces `[('child',S),('sibling',D),('self',D)]`, so `intermediate_handles=[S,D]` and `assertNotIn("D", …)` (patch.diff:354-359) fails *behaviourally*, not as a missing-module ImportError — the iteration-1 defect (brief.md:20). Gate confirms `red-without-fix=PASS` (check-gates.json:33-39). Test is non-vacuous: `assertIn("S", …)` forces a genuine multi-hop route (patch.diff:348-352). |
| C3 — C3 Change | PASS | Change is coherent and scoped to the search seam: optional `start_handle` param + post-processing in `get_relatives` (patch.diff:9-10, 38-41) threaded from the one `main()` call site (patch.diff:50-52). Case 2 (re-parent root-person relatives onto bare `path`) removes the `('sibling',D)` anchor at its source; case 1 (drop relatives that *are* start) is defensive. No mutation, read-only linked list. New `tests/__init__.py` + GPL-headered test (patch.diff:65-83). |
| C4 — C4 Verification (red→green) | PASS | Gating C4 reports `green-with-fix=PASS / red-without-fix=PASS` (check-gates.json:33-39). Re-derived green: post-fix path `[('child',S),('self',D)]` satisfies all four assertions. Crucially the test drives the **real** `main()` generator (`for _signal in harness.main()`, patch.diff:326) via a GUI-only-override subclass (patch.diff:220-271) — not a parallel BFS copy — so production routes through the same seam the test exercises (§3.4 / brief.md:19, iteration-1's primary failure). Run outside the broad `try/except` so fix errors surface (patch.diff:99-102). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | The fix removes the cause at the construction seam (Home is never emitted as an interior anchor), not by filtering rendered output — good. But the chosen shape *discards the first-hop relation label* (a direct relative of Home renders attached to the root with no "… of \<Home\>" step; e.g. active=S yields just `[('self',D)]`, patch.diff:374-387). Whether that is the adequate causal shape vs. relabelling-relative-to-root is the judgment the brief explicitly routes to sign-off (brief.md:60-65). |
| T1 — T1 Structure | PASS | Gate PASS, 1 addon conforms, 1 advisory (check-gates.json:54-55) — the advisory is the pre-existing folder-name-vs-`.gpr.py`-id deviation the brief puts out of scope (brief.md:16,66-67). `tests/__init__.py` is required for the dotted-path addon test package (INTEGRATION.md:112), not the addon-root `__init__.py` T1 forbids. |
| T2 — T2 Shape | PASS | Gate PASS, 1 file conforms (check-gates.json:60-64). New test file carries the GPL header (patch.diff:65-83) and contains no diagnostic `print()` — the only new-file requirements the brief imposes (brief.md:68). |
| T3 — T3 Runtime | NEEDS-HUMAN | All four T3 rows are deltas, not matched baseline noise: addon-unit ×60 and ×61 report "runner exited 1 with no parsed failures and no matching baseline signature (a new failure mode)" (check-gates.json:73,82), and the addon-unit matrix is documented as *resolved / no standing baseline* (INTEGRATION.md:170-173), so a delta there is a real signal — plausibly the new GTK-importing test erroring under the non-xvfb `run-addon-unit` runner (the test's own portability caveat, patch.diff:104-107). The two interface deltas (`setUpClass interface.test_smoke.SmokeTest`, check-gates.json:91,100) the patch cannot have caused (it touches no core/GUI-startup code) and match the documented `_Glade__dirname` smoke baseline (INTEGRATION.md:176-178) — environmental. Human must triage whether the addon-unit delta is the added test or environment. Advisory (non-gating). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` / `pr-description.md` in the bundle (check-gates.json:108-109) — draft-only stage per STOP discipline (brief.md:29-31); the contribution wrapper is authored at publish, so there is nothing for T4 to judge. |
| T5 — T5 Judgment | NEEDS-HUMAN | Reviewer + human sign-off element (INTEGRATION.md:216,230-231). Reviewer opinion: the build is technically sound and clears all three iteration-1 rejection reasons — production-path test not a copy (patch.diff:220,326), genuine behavioural red (C2), and no `default_person is None` regression because the Home handle is passed by the post-guard caller and never re-dereferenced inside the seam (patch.diff:38-41,50-52; brief.md:56-59). Open judgment carried to human: the label-fidelity shape (see C5/V) and the T3 addon-unit delta. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human (check-gates.json:123-129; INTEGRATION.md:230-231). Is "Home no longer an intermediate step, but its direct relatives shown attached to the root without a relation label" the right product behaviour for the Deep Connections Gramplet? The brief reserves this for sign-off (brief.md:60-65). The out-of-scope parent→child-of-spouse chains remain unaddressed by design (brief.md:16). |

## §6 — items the human must clear

Each NEEDS-HUMAN row above is a §6 item:

1. **C5 — causal shape / label fidelity.** The fix collapses the first hop from a
   relative of Home onto the bare root, dropping the "… of \<Home\>" relation
   label (active=S renders as `[('self',D)]`; the multi-hop A renders as
   `[('child',S),('self',D)]`, so S attaches to the D-root with no shown relation
   to D). Confirm this rendered shape is acceptable, or that relabel-relative-to-root
   is preferred. (build-notes.md, withheld from me, is where Do was asked to state
   what the chosen shape does to the rendered label — brief.md:60-65; read it.)

2. **T3 — addon-unit matrix delta.** `T3-addon-unit-60` and `-61` both report a
   *new failure mode* against a suite that should be green-baseline. Determine
   whether the new `DeepConnectionsGramplet/tests/test_deep_connections.py`
   errors under `run-addon-unit.sh` (no xvfb/GI bootstrap, unlike the C4
   `run-verify.sh`) — the test imports `gi`/Gtk at load (patch.diff:104-107). If
   so, the regression test is not portable across runners even though C4 is green.
   The two interface deltas read as the documented environmental smoke baseline,
   not this patch — confirm.

3. **V — fitness-to-purpose.** Is removing only the Home-as-intermediate-anchor
   case (with the in-scope label change) the right outcome, given the conceded
   out-of-scope parent→child-of-spouse chains remain? Human call at sign-off.

## Notes on evidence strength

- **Iteration-2's load-bearing requirement is met.** The test drives the
  production `main()` generator through a GUI-only-override harness, not a second
  BFS, and `main()` now calls the shared `get_relatives` seam — so loop-level drift
  is caught (brief.md:19,40-48; patch.diff:220-271,326,50-52). This is the single
  thing iteration 1 got wrong, and it is corrected.
- **C4 red is genuinely behavioural**, not a missing-module ImportError: the
  assertion that fails pre-fix is `assertNotIn("D", intermediate_handles)` on a
  path the real `main()` produced (brief.md:20; patch.diff:354-359).
- **Residual artifact-only risk:** I could not confirm `main()`'s self/root
  detection still behaves when a direct relative (e.g. S) is handed the root path
  object by reference (case 2, patch.diff:40-41). The C4 green and test 2
  (active=S → `root[1]=="D"`) are empirical evidence it does, but a reader with the
  full `main()` should confirm no code path keys off `current_path[1][0]=="self"`
  in a way that now misclassifies a collapsed relative.
