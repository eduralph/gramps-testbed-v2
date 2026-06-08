# Result — issue 8653 / deep-connections-excludes-start-person

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The **Deep Connections Gramplet** reports connection paths that name the Home/start person as an *intermediate relationship anchor* — e.g. "Main person / sibling of another person / **sibling of main person** / …" — so the search origin appears *inside* a path's relationship steps instead of only as its terminal root. (Mantis 8653, status `confirmed`; reporter calls the first case "definitely a bug" and concedes the parent → child-of-spouse case is "probably harder to avoid".) **Confirmed reproducible on current gramps60 in iteration 1** — the 2024 "Updated DeepConnectionsGramplet" commit rebuilt only the UI; the search algorithm is unchanged, so this is NOT POSSIBLY-FIXED.
- Success criterion: For the active person, the connection path(s) the gramplet produces **in production** (the search driven by `DeepConnectionsGramplet.main()`) contain the Home/start person **only** as the path's terminal `"self"` root — no produced path names the Home person as an intermediate relationship step/anchor — and each path still connects the active person to the Home person (the chain is not broken). The regression test demonstrates this by driving the **same search code `main()` runs** (see Test file), not a copy of it.
- Repo + branch target: `addons-source` @ `maintenance/gramps60` — branched from `upstream/maintenance/gramps60` (addons production; the maintainer cherry-picks forward to gramps61). Confirmed: `DeepConnectionsGramplet.gpr.py` declares `gramps_target_version="6.0"`; the working-tree `DeepConnectionsGramplet.py` is byte-identical to `upstream/maintenance/gramps60` (`git -C ../addons-source diff upstream/maintenance/gramps60 -- …` is empty), so the `path:line` citations below are valid for the target branch. (INTEGRATION §2.)
- Scope (one logical fix) / out of scope: Remove the defect whereby a produced connection path names the Home/start person as an *intermediate relationship anchor*, so the Home person is recorded only as the path root. Orientation (where the paths are produced — NOT a prescribed fix shape): the breadth-first connection search in `DeepConnectionsGramplet.main()` seeds the queue with the Home person as the `"self"` root (`DeepConnectionsGramplet.py:352-358`), expands each node via `get_relatives` (`:221-279`, called at `:439`), and renders the found path with `pretty_print` (`:287-316`). / **out of scope:** the parent → child-of-spouse chains the reporter conceded are "probably harder to avoid"; any change to the gramplet UI / pause-continue / progress / relationship-label wording; the pre-existing addon-structure deviations T1/T2 flag on files this fix does not touch (folder-name vs `.gpr.py` id `Deep Connections Gramplet`; missing GPL header in `DeepConnectionsGramplet.gpr.py`); and **any change that lets the Home handle be dereferenced before `main()`'s existing "No Home Person set" guard** (`:334-338`) — the no-Home-person case MUST keep returning early, no regression (iteration-1 risk T5-b).

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix. Repro confirmed in iteration 1 (refutes the "already fixed by the visited-cache" hypothesis — the cache blocks re-*expanding* Home, not Home being named as a root-adjacent anchor). This is **iteration 2**: do NOT re-attempt the v1 parallel-copy shape; satisfy the production-path requirement above.
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 ✓ structure: 1 addon(s) conform to doc 16 §Structure (1 advisory)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — The fix removes the cause at the construction seam (Home is never emitted as an interior anchor), not by filtering rendered output — good. But the chosen shape *discards the first-hop relation label* (a direct relative of Home renders attached to the root with no "… of \<Home\>" step; e.g. active=S yields just `[('self',D)]`, patch.diff:374-387). Whether that is the adequate causal shape vs. relabelling-relative-to-root is the judgment the brief explicitly routes to sign-off (brief.md:60-65).
- [x] T3 — T3 Runtime — All four T3 rows are deltas, not matched baseline noise: addon-unit ×60 and ×61 report "runner exited 1 with no parsed failures and no matching baseline signature (a new failure mode)" (check-gates.json:73,82), and the addon-unit matrix is documented as *resolved / no standing baseline* (INTEGRATION.md:170-173), so a delta there is a real signal — plausibly the new GTK-importing test erroring under the non-xvfb `run-addon-unit` runner (the test's own portability caveat, patch.diff:104-107). The two interface deltas (`setUpClass interface.test_smoke.SmokeTest`, check-gates.json:91,100) the patch cannot have caused (it touches no core/GUI-startup code) and match the documented `_Glade__dirname` smoke baseline (INTEGRATION.md:176-178) — environmental. Human must triage whether the addon-unit delta is the added test or environment. Advisory (non-gating).
- [x] T5 — T5 Judgment — Reviewer + human sign-off element (INTEGRATION.md:216,230-231). Reviewer opinion: the build is technically sound and clears all three iteration-1 rejection reasons — production-path test not a copy (patch.diff:220,326), genuine behavioural red (C2), and no `default_person is None` regression because the Home handle is passed by the post-guard caller and never re-dereferenced inside the seam (patch.diff:38-41,50-52; brief.md:56-59). Open judgment carried to human: the label-fidelity shape (see C5/V) and the T3 addon-unit delta.
- [x] V — Validation — fitness-to-purpose — Always-human (check-gates.json:123-129; INTEGRATION.md:230-231). Is "Home no longer an intermediate step, but its direct relatives shown attached to the root without a relation label" the right product behaviour for the Deep Connections Gramplet? The brief reserves this for sign-off (brief.md:60-65). The out-of-scope parent→child-of-spouse chains remain unaddressed by design (brief.md:16).

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
- By / date: Eduard Ralph / 2026-06-08

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
- issue_8653: Do verifies only the gating C4 runner (`run-verify.sh`) but the advisory T3 `run-addon-unit.sh` is a *different* runner run later at Check — consider requiring the Do/gate path to reconcile a green-C4 / failed-T3 split (root-cause or classify the addon-unit exit) before handing to the human, so an un-diagnosed "exited 1 / no parsed failures" delta plus a reviewer guess isn't what sign-off has to triage; also fix the reviewer's wrong model that `run-addon-unit.sh` lacks xvfb/GI bootstrap (it has both, run-addon-unit.sh:239-244).
- issue_8653: run a standalone root-cause analysis of the `run-addon-unit.sh` "exited 1 / no parsed failures, no matching baseline signature" behavior — is it an install/setup/all-skipped crash, a `t3_baseline.py` parsing blind spot, or genuinely the addon test — accepted here as advisory but the cause was never established.
