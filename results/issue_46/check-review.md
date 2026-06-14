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
