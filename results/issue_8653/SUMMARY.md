# Result — issue 8653 / ** deep-connections-excludes-start-person

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** The **Deep Connections Gramplet** reports connection paths that route back through the start (Home) person, producing nonsensical chains such as "Main person / sibling of another person / **sibling of main person**" — the start person, which is the search origin, appears *inside* the path rather than only as its root. (Mantis 8653; reporter calls the first case "definitely a bug" and the parent/child-of-spouse case "probably harder to avoid".)
- Success criterion: ** A connection path the gramplet produces for the active person does **not** contain the Home/start person as an intermediate relationship step — the start person appears only as the implicit search root, never re-entered partway through a path.
- Repo + branch target: ** `addons-source` @ `maintenance/gramps60` — branched from `upstream/maintenance/gramps60` (addons production; the maintainer cherry-picks forward to gramps61). Confirmed: `DeepConnectionsGramplet.gpr.py` declares `gramps_target_version="6.0"`. (INTEGRATION §2.)
- Scope (one logical fix) / out of scope: ** Exclude the start (Home) person from being traversed/re-entered as an intermediate node in the connection search so it cannot appear mid-path. The relevant logic is the BFS in `DeepConnectionsGramplet/DeepConnectionsGramplet.py` `main()` (queue seeded with the default person, `:353-358`) + `get_relatives()` (`:221-279`) + `pretty_print()` (`:287-316`). / **out of scope:** the "harder" second case the reporter conceded (parent → child-of-spouse chains); any change to the gramplet's UI, pause/continue, or relationship-label wording.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** verify repro first — the report is from 2015 (4.1.3) and the gramplet has since been **substantially rewritten** (modern Gtk UI; the BFS caches visited handles, which may already block re-entering the start person). Do must confirm the symptom reproduces on the current gramps60 code **before** changing anything; if it does **not** reproduce, report POSSIBLY-FIXED with the evidence rather than forcing a change.
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ DeepConnectionsGramplet: folder name does not match any .gpr.py id ['Deep Connections Gramplet'] (doc16-addon §Stru
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): fail — T2 ✗ DeepConnectionsGramplet.gpr.py: no GPL licence header in the first 40 lines (AGENTS.md §File Headers)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 133 with no parsed failures and no matching baseline signature (a new failure 
- T3 runtime: addon unit suites (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: signature 'pip install … failure(s)'
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 8653 / deep-connections-excludes-start-person

> Advisory, artifact-only, decorrelated from the builder. Inputs seen: `patch.diff`,
> `brief.md`, `check-gates.json`. `build-notes.md` was withheld. Every Basis below is
> re-derived from the artifacts, not copied from the gate text.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | Success criterion (brief.md:10 — start person never an intermediate step) is concrete and directly targeted by the exclusion block at `connection_search.py:139-148` (patch.diff:253-262). Scope/out-of-scope (brief.md:12) respected: UI, pause/continue, label wording untouched; the conceded parent→child-of-spouse case is not attempted. |
| C2 — C2 Reproduction (red pre-fix) | PASS | C4 gate records `red-without-fix=PASS` (check-gates.json:33-39). I re-traced the `_nibling_db` scenario (patch.diff:427-447): without the exclusion block, `search_connections("D","A")` yields path_steps `[(child,S),(sibling,D),(SELF,D)]` — D appears as a non-root anchor, so `assertNotIn("D", intermediate_handles)` (patch.diff:476) fails. Repro is genuine, not vacuous (guard `assertIn("S",…)` at patch.diff:469 forces the multi-hop). NOTE: repro is at the extracted-helper level, not the `example.gramps` GUI repro the brief described (brief.md:13). |
| C3 — C3 Change | PASS | Refactor extracts relation-gathering into a GUI-free seam as the brief authorised (brief.md:14); new files carry GPL headers and no diagnostic prints; fix is localised to `get_relatives` post-processing. Caveat carried to T5: `search_connections` (patch.diff:265-293) is a **second** BFS that parallels the gramplet's `main()` loop rather than a shared extraction — the production loop in `main()` is not itself extracted, only `get_relatives`/`get_links_from_notes`. |
| C4 — C4 Verification (red→green) | PASS | Gating gate C4-verify = PASS, `green-with-fix=PASS / red-without-fix=PASS` (check-gates.json:33-39). Re-traced with the fix: rule-2 collapse sets S's path to the root, so path_steps(A) = `[(child,S),(SELF,D)]`; D only at root → green. The fix sits in `get_relatives`, which the real gramplet calls via `connection_search.get_relatives(start_handle=self.default_person.handle)` (patch.diff:98-104), so the production path is exercised by the shared function (though not by the tested BFS loop — see T5). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Always-human + contested mechanism. Root cause re-derived: the modern BFS cache blocks re-*expanding* the start node but NOT its appearance as an intermediate *anchor label* (the `(sibling, D)` step) — so the bug is real on gramps60 and the brief's "possibly already fixed" hypothesis (brief.md:17) is refuted. Rule 1 (drop start as a relative, patch.diff:256) cleanly fixes the reporter's first case. Rule 2 (patch.diff:257-261) is the contestable part: it re-points ALL of the start person's direct relatives to the bare root node, **discarding the relation label** that says how they connect (S's "sibling of Home" is erased; A renders as "child of S" with S floating at root). Human must judge whether that fidelity loss is acceptable vs. a minimal fix. |
| T1 — T1 Structure | NEEDS-HUMAN | Gate FAIL = folder `DeepConnectionsGramplet` ≠ .gpr.py id `Deep Connections Gramplet` (check-gates.json:55). The patch does **not** touch `DeepConnectionsGramplet.gpr.py` or rename the folder, so this mismatch is **pre-existing**, not introduced — and renaming is out of scope (brief.md:12). Human to confirm the pre-existing structure deviation is acceptable. (The added `tests/__init__.py` is required by the dotted-path test convention the brief mandates, brief.md:14, and is not the flagged item.) |
| T2 — T2 Shape | NEEDS-HUMAN | Gate FAIL = no GPL header in first 40 lines of `DeepConnectionsGramplet.gpr.py` (check-gates.json:64). That file is **not** in the patch, so the gap is pre-existing. The patch's own new files DO comply: GPL headers at `connection_search.py:1-19` and `tests/test_deep_connections.py:1-15`; no diagnostic prints in either. Human to confirm the untouched-file header gap is out of scope. |
| T3 — T3 Runtime | NEEDS-HUMAN | Mixed: addon-unit PASS (matches pre-existing `pip install … failure(s)` baseline — meaning that runner may not actually execute the new test; C4's run-verify is the real run evidence). But TWO deltas need human attribution: core unit suite `exited 133 with no parsed failures` (check-gates.json:73 — looks like a segfault/headless-environment crash, not obviously patch-related) and GUI smoke `1 new failure: setUpClass (interface.test_smoke.SmokeTest)` (check-gates.json:91). I cannot decorrelate the smoke delta from the bare top-level `import connection_search` (patch.diff:11) added to the gramplet load path — needs verification that Gramps puts the addon dir on sys.path at plugin-load time. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (check-gates.json:100), so there is no commit/PR wrapper to evaluate. Consistent with the brief's STOP discipline (brief.md:21-23 — draft only, PR not ready before sign-off). |
| T5 — T5 Judgment | NEEDS-HUMAN | Always reviewer+human. Open engineering-judgment items: (a) `search_connections` duplicates `main()`'s BFS — the test validates a *copy* of the loop, so loop-level drift would not be caught (only the shared `get_relatives` is co-exercised); (b) `self.default_person.handle` (patch.diff:103) is a NEW hard dependency inside `get_relatives` — if no Home person is set, `default_person` may be `None` → AttributeError regression; `main()` not in artifacts to confirm it is always set; (c) bare `import connection_search` portability under Gramps plugin loading (see T3); (d) rule-2 relation-label loss (see C5). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always human at sign-off. The fix is verified at the unit level only; it has not been validated in the actual gramplet against `example.gramps` in the GUI (brief.md:13), and rule 2 changes how the start person's direct relatives render. Human must confirm the produced paths actually satisfy the reporter's intent. |

## §6 — Items the human must clear (one per NEEDS-HUMAN row)

1. **C5 / root-cause (contested).** Confirm the diagnosis: cache blocks re-expansion but not the intermediate *anchor label*, so the bug is real (brief's "possibly fixed" hypothesis is refuted). Then judge **rule 2** (`connection_search.py:143-147` / patch.diff:257-261): collapsing every direct relative of the Home person onto the bare root node discards the relation label connecting them. Is dropping "S is sibling of Home" acceptable, or should the fix preserve the label while keeping Home out of the *body* of other paths?

2. **T1 / structure (pre-existing, scope).** Folder vs .gpr.py-id mismatch is pre-existing and untouched by the patch. Confirm it is out of scope and not a regression.

3. **T2 / shape (pre-existing, scope).** Missing GPL header on `DeepConnectionsGramplet.gpr.py` is pre-existing (file not in patch). Confirm out of scope; the patch's own new files comply.

4. **T3 / runtime deltas (attribution).** Attribute the core-unit `exit 133` (likely environmental crash) and the GUI-smoke `setUpClass` new failure. Specifically verify the bare `import connection_search` resolves when Gramps loads the gramplet (addon dir on sys.path), since a load-time failure there could surface as the smoke delta.

5. **T5 / judgment.** (a) Decide whether the duplicated `search_connections` BFS is acceptable or whether `main()`'s loop should be the single tested code path; (b) verify `self.default_person` is guaranteed non-`None` before `get_relatives` runs (else AttributeError when no Home person is set) — `main()` was not in the review bundle to confirm.

6. **V / fitness-to-purpose.** Validate the fix in the real gramplet against `example.gramps` in the GUI; confirm the rendered paths meet the reporter's intent and rule 2's relabeling reads sensibly to a user.

## Summary

The core fix (rule 1, dropping the start person when it surfaces as another node's relative — `connection_search.py:142` / patch.diff:256) is correct and directly resolves the reporter's first case; my independent trace confirms red→green and refutes the "already fixed by the cache" hypothesis. C4 is objectively green. The residual risk is concentrated in **rule 2's label-discarding collapse** (a causal-adequacy/fidelity judgment), the **duplicated BFS** that means the test validates a copy of the production loop rather than the loop itself, a possible **`default_person is None` regression**, and the **two unattributed T3 runtime deltas** (one of which could plausibly stem from the new bare import). None are auto-FAIL on the artifacts available, but all are advisory NEEDS-HUMAN gates that should be cleared before sign-off. The two structure/shape FAILs (T1, T2) are pre-existing on files the patch never touches.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Always-human + contested mechanism. Root cause re-derived: the modern BFS cache blocks re-*expanding* the start node but NOT its appearance as an intermediate *anchor label* (the `(sibling, D)` step) — so the bug is real on gramps60 and the brief's "possibly already fixed" hypothesis (brief.md:17) is refuted. Rule 1 (drop start as a relative, patch.diff:256) cleanly fixes the reporter's first case. Rule 2 (patch.diff:257-261) is the contestable part: it re-points ALL of the start person's direct relatives to the bare root node, **discarding the relation label** that says how they connect (S's "sibling of Home" is erased; A renders as "child of S" with S floating at root). Human must judge whether that fidelity loss is acceptable vs. a minimal fix.
- [x] T1 — T1 Structure — Gate FAIL = folder `DeepConnectionsGramplet` ≠ .gpr.py id `Deep Connections Gramplet` (check-gates.json:55). The patch does **not** touch `DeepConnectionsGramplet.gpr.py` or rename the folder, so this mismatch is **pre-existing**, not introduced — and renaming is out of scope (brief.md:12). Human to confirm the pre-existing structure deviation is acceptable. (The added `tests/__init__.py` is required by the dotted-path test convention the brief mandates, brief.md:14, and is not the flagged item.)
- [x] T2 — T2 Shape — Gate FAIL = no GPL header in first 40 lines of `DeepConnectionsGramplet.gpr.py` (check-gates.json:64). That file is **not** in the patch, so the gap is pre-existing. The patch's own new files DO comply: GPL headers at `connection_search.py:1-19` and `tests/test_deep_connections.py:1-15`; no diagnostic prints in either. Human to confirm the untouched-file header gap is out of scope.
- [x] T3 — T3 Runtime — Mixed: addon-unit PASS (matches pre-existing `pip install … failure(s)` baseline — meaning that runner may not actually execute the new test; C4's run-verify is the real run evidence). But TWO deltas need human attribution: core unit suite `exited 133 with no parsed failures` (check-gates.json:73 — looks like a segfault/headless-environment crash, not obviously patch-related) and GUI smoke `1 new failure: setUpClass (interface.test_smoke.SmokeTest)` (check-gates.json:91). I cannot decorrelate the smoke delta from the bare top-level `import connection_search` (patch.diff:11) added to the gramplet load path — needs verification that Gramps puts the addon dir on sys.path at plugin-load time.
- [x] T5 — T5 Judgment — Always reviewer+human. Open engineering-judgment items: (a) `search_connections` duplicates `main()`'s BFS — the test validates a *copy* of the loop, so loop-level drift would not be caught (only the shared `get_relatives` is co-exercised); (b) `self.default_person.handle` (patch.diff:103) is a NEW hard dependency inside `get_relatives` — if no Home person is set, `default_person` may be `None` → AttributeError regression; `main()` not in artifacts to confirm it is always set; (c) bare `import connection_search` portability under Gramps plugin loading (see T3); (d) rule-2 relation-label loss (see C5).
- [x] V — Validation — fitness-to-purpose — Always human at sign-off. The fix is verified at the unit level only; it has not been validated in the actual gramplet against `example.gramps` in the GUI (brief.md:13), and rule 2 changes how the start person's direct relatives render. Human must confirm the produced paths actually satisfy the reporter's intent.

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
- issue_8653: accepted with a T3 follow-up — confirm the bare `import connection_search` (patch.diff:11) resolves on Gramps' addon sys.path at plugin-load, and re-attribute/re-promote the batch-wide `exit 133` + `setUpClass (SmokeTest)` T3 deltas (identical across all three bundles → likely environmental).
