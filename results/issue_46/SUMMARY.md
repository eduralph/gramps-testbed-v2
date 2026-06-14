# Result — issue 46 / graphview-import-raises-on-missing-deps

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: `GraphView/graphview.py` raises a bare `Exception` at **module import** when GooCanvas (`graphview.py:111-113`) or the `dot`/GraphViz binary (`:120-122`) is unavailable. These fire at top level, so the module is unimportable by any caller that has not first consulted the plugin's declared requirements — including the addon's own test collection: `GraphView/tests/test_graphview_dot_handles.py` does `from GraphView.graphview import DotSvgGenerator` at top level, so on a host without `dot` the test loader crashes during collection (traceback, 0 tests) instead of the suite running. The `.gpr.py` already declares `requires_gi=[("GooCanvas","2.0,3.0")]` and `requires_exe=["dot"]` (`graphview.gpr.py:16-17`), and Gramps' own plugin manager already gates loading on them — `Requirements.check_plugin()` (`gramps/gen/utils/requirements.py:129-133`) and `_pluginreg.scan_dir()` removing any plugin whose check fails (`gramps/gen/plug/_pluginreg.py:1478-1479`) — so it never imports the module when a requirement is absent. The module-level `raise` therefore duplicates a gate the framework already owns and breaks every direct importer. Reported and root cause verified on the target branch; the raises are present unchanged on `maintenance/gramps60` and `maintenance/gramps61`.
- Success criterion: On the target branch, importing the module — `import GraphView.graphview`, and `from GraphView.graphview import DotSvgGenerator` — completes **without raising** when GooCanvas / the `dot` binary are absent. The shipped regression test drives that import with the dependency unavailable: pre-fix it errors during import, post-fix it imports cleanly, so `GraphView/tests/` collects and runs on a host lacking `dot` instead of crashing collection. The plugin's missing-dependency behaviour for end users is unchanged — it remains gated by the registration-level `requires_*`.
- Repo + branch target: addons-source @ `maintenance/gramps60` (addons production — INTEGRATION §2; branch from `upstream/maintenance/gramps60`). Cherry-pick forward to `maintenance/gramps61` as a **separate** pick — the issue states the same code is on both branches; verify it remains correct there ("applies cleanly" is not "remains correct").
- Scope (one logical fix) / out of scope: Remove the import-time hard failure so the module imports when its declared GooCanvas/`dot` dependencies are absent. (Mechanism — pure removal of the raises vs. relocating any availability check — is left to Do; this brief names no probe/guard. Do prefers removing the cause over guarding it, principles §3.1/§3.3.) / out of scope: changing the missing-dependency UX for end users (already owned by `requires_gi`/`requires_exe` at registration), the bug-13832 DOT node-id quoting logic, and the GooCanvas API calls inside the view's runtime methods.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (open issue; root cause verified on target branch; reproduces; localized behavioural fix).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 ✓ structure: 1 addon(s) conform to doc 16 §Structure
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 46 / graphview-import-raises-on-missing-deps (iteration 2)

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json`. `build-notes.md` withheld by design. Every Basis
> below is re-derived from those three files, not copied from the builder's claim.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | brief.md:10 carries a concrete, testable success criterion ("importing the module … completes without raising when GooCanvas / the `dot` binary are absent"); Defect/Invariant/Scope/Test-file fields all present and well-formed (brief.md:8-19). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The shipped test fails when the import raises: child non-zero exit → `assertEqual(returncode, 0)` fails (patch.diff:113-127). check-gates.json:38 records `red-without-fix=PASS`, i.e. the reproduction was confirmed red without the fix. |
| C3 — C3 Change | PASS | patch.diff:9-20 removes exactly the two import-time `raise Exception(...)` (graphview.py:111-113 GooCanvas, :120-122 dot) and nothing else — the "pure removal of the raises" the brief's Scope explicitly permits/prefers (brief.md:14); bug-13832 quoting and runtime GooCanvas calls untouched. |
| C4 — C4 Verification (red→green) | PASS | check-gates.json:33-40, the sole gating row: `C4-verify: green-with-fix=PASS / red-without-fix=PASS` via run-verify.sh. Both directions exercised. (NB: this verifies the unit reproduction only — not the T3 runtime deltas below; per CLAUDE.md a green gating check is not a correctness verification of the whole change.) |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Oracle is "reviewer + human sign-off" (check-gates.json:46). Removing the raises directly targets the stated root cause (duplicated registration-layer gate, brief.md:9), which reads adequate — BUT three T3 runtime gates still FAIL with the iteration-1 rejection signature (below). I cannot re-derive from artifacts whether the import invariant is actually restored in the runtime environments, so adequacy is unconfirmed. |
| T1 — T1 Structure | PASS | New test at `GraphView/tests/test_graphview_import.py` matches the addon convention (`tests/` package + `test_*` prefix); check-gates.json:51-57 `T1 ✓ structure: 1 addon(s) conform`. |
| T2 — T2 Shape | PASS | GPL header present on the new file (patch.diff:31-48); check-gates.json:59-66 `T2 ✓ shape: 1 file(s) conform`; no `print()` flagged. |
| T3 — T3 Runtime | FAIL | check-gates.json reports fail on 3 of 4 runtime gates: addon-unit ×60 (line 73) and ×61 (line 82) both "runner exited 2 … new failure mode"; addon E2E (line 100) "1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)". The `t3_baseline` tool attributes these as *new* deltas, and they replicate the exact signatures iteration 1 was rejected for (brief.md:29-31). Only interface-smoke matches baseline (line 91). |
| T4 — T4 Contribution | N/A | No commit-msg.txt / pr-description.md in the bundle, so the commit/PR wrapper gate has nothing to assess (check-gates.json:109). |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle is "reviewer + human sign-off" (check-gates.json:115). The rebuild correctly removes iteration 1's top-level `import gi` / `gi.require_version` pin — the new test imports only stdlib at module top level and runs the production import in a child interpreter (patch.diff:76-94), relying on the inherited PYTHONPATH gi pin rather than reimplementing it (patch.diff:108-111). That addresses the stated rejection cause; whether it actually met the iteration-2 objective is contradicted by the persisting T3 deltas and needs human adjudication. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human (oracle: "human at sign-off", check-gates.json:125). The brief's promise that end-user missing-dependency UX is unchanged — still gated solely by `requires_gi`/`requires_exe` at registration (brief.md:10-11) — is a fitness-to-purpose judgment not derivable from these artifacts. |

## §6 — items the human must clear

1. **(C5) Causal adequacy vs. persisting T3 deltas.** The fix removes the two
   raises and the C4 unit reproduction goes red→green, but the iteration-2
   objective from the carry-forward (brief.md:28) was to *clear the T3 deltas*.
   check-gates.json still shows addon-unit exit-2 (×60/×61) and the E2E
   `setUpClass (SmokeTest)` delta — the same signatures iteration 1 was rejected
   on. Human must decide whether removing the raises genuinely restored the
   import invariant in the runtime environments, or whether a residual
   import-time failure remains (candidate: `test_graphview_dot_handles.py` still
   does a top-level `from GraphView.graphview import DotSvgGenerator` and was
   *not* touched by this patch, so any unguarded gi/Gtk import in graphview.py
   could still abort collection on the unit hosts — I cannot confirm this from
   artifacts; build-notes withheld).

2. **(T3) Advisory-vs-blocking call.** All failing T3 rows are `gating:false`,
   so `overall:"pass"` despite them. Because these deltas mirror the prior
   rejection reason, the human must decide whether they block sign-off rather
   than accepting the green gating result at face value. The `overall:"pass"`
   here verifies only the single gating C4 row, not the change as a whole.

3. **(T5) Did the rebuild meet its objective?** The test design correctly drops
   the rejected top-level gi/Gtk pin (the named iteration-1 cause). Human must
   confirm whether the rebuild was *supposed* to clear the T3 deltas and, if so,
   why they persist — i.e. whether the rejection cause was correctly diagnosed.

4. **(V) Fitness-to-purpose.** Confirm the end-user missing-dependency behaviour
   is genuinely unchanged (plugin still excluded by `Requirements.check_plugin` /
   `_pluginreg.scan_dir` when deps absent), and that the gramps61 cherry-pick
   "remains correct" rather than merely "applies cleanly" (brief.md:12) — neither
   is derivable from the provided artifacts.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Oracle is "reviewer + human sign-off" (check-gates.json:46). Removing the raises directly targets the stated root cause (duplicated registration-layer gate, brief.md:9), which reads adequate — BUT three T3 runtime gates still FAIL with the iteration-1 rejection signature (below). I cannot re-derive from artifacts whether the import invariant is actually restored in the runtime environments, so adequacy is unconfirmed.
- [x] T5 — T5 Judgment — Oracle is "reviewer + human sign-off" (check-gates.json:115). The rebuild correctly removes iteration 1's top-level `import gi` / `gi.require_version` pin — the new test imports only stdlib at module top level and runs the production import in a child interpreter (patch.diff:76-94), relying on the inherited PYTHONPATH gi pin rather than reimplementing it (patch.diff:108-111). That addresses the stated rejection cause; whether it actually met the iteration-2 objective is contradicted by the persisting T3 deltas and needs human adjudication.
- [x] V — Validation — fitness-to-purpose — Always-human (oracle: "human at sign-off", check-gates.json:125). The brief's promise that end-user missing-dependency UX is unchanged — still gated solely by `requires_gi`/`requires_exe` at registration (brief.md:10-11) — is a fitness-to-purpose judgment not derivable from these artifacts.

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
- By / date: Eduard Ralph / 2026-06-13

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
- issue_46: T3 gate discards raw runner stderr — the addon-unit exit-2 was a `bash -c` single-quote nesting bug in `engine/scripts/ubuntu/run-addon-unit.sh:268-269`, invisible in the bundle's summarized signature; persist runner stderr + move `synth_junit` attribution outside the fragile `bash -c` body. File as testbed engine issue.
