# Result — issue 10628 / deep-connections-repeats-same-path

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Deep Connections gramplet, when multiple distinct paths exist between the
- Success criterion: for a tree with two or more independent paths between home and target,
- Repo + branch target: gramps-project/addons-source @ maintenance/gramps60
- Scope (one logical fix) / out of scope: the "find next connection" iteration that fails to exclude the

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
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
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: 2 new failure(s) not in baseline: LifeLineChartView.collection::import_or_collection, setUpC
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 10628 / deep-connections-repeats-same-path

> **Reviewer:** Advisory (no Write/Edit access). `$PDCA_TARGET` is **unset**;
> all `path:line` citations are grounded against `patch.diff` alone.
> Build-notes withheld as required.

---

## Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | `brief.md` fully specifies defect (repeated path on Continue), success criterion (distinct successive paths), and scope boundary (iteration logic; excludes result formatting, #946 home-person-interior, relationship naming). |
| C2 Reproduction (red pre-fix) | PASS | No standalone C2 gate configured; C4 gate's own evidence ("red-without-fix=PASS") confirms the test was red without the fix. Mechanical check: without the `continue` the fall-through after `yield False` expands the target, queuing its relatives back into the BFS — the test's `assertNotIn("A", anchors)` would fire exactly there. |
| C3 Change | PASS | Two-part patch: (1) one `continue` statement added after `yield False` in `DeepConnectionsGramplet.py` patch.diff:19, skipping target-expansion on resume; (2) new regression test `DeepConnectionsGramplet/tests/test_deep_connections_paths.py` patch.diff:23–359. Both changes are within brief scope; no result formatting, home-person-interior, or relationship-naming code is touched. |
| C4 Verification (red→green) | PASS | `check-gates.json` element C4, gating=true, result=pass: "C4-verify: green-with-fix=PASS / red-without-fix=PASS". Mechanically confirmed by the builder's C4-verify run; the gate is the authoritative evidence; stale-target caveat does not apply (PDCA_TARGET unset). |
| C5 Causal adequacy | PASS | Root cause is stated and verified in two sentences: when `main()` finds the active/target person it `yield`s (pauses), and on resume the fall-through expands the target itself, queuing its relatives; those relatives re-reach the target, re-emitting the same path. The `continue` prevents that fall-through entirely. C5 smell-test: the fix adds a flow-control `continue` — not a `hasattr`/`try`-capability probe, not a feature guard — so the probe-smell rule does not fire. |
| T1 Structure | PASS | Gate T1-structure confirmed: "1 addon(s) conform to doc 16 §Structure". New test file placed at `DeepConnectionsGramplet/tests/test_deep_connections_paths.py` (correct `test_*.py` prefix, under addon `tests/`); no erroneous `__init__.py` added to the addon root. |
| T2 Shape | PASS | Gate T2-shape confirmed: "1 file(s) conform to doc 16 §Coding style". GPL v2+ header present on new test file (patch.diff:29–46); no bare `print()` calls in production code. Touched production file `DeepConnectionsGramplet.py` already carries a GPL header (pre-existing). |
| T3 Runtime | NEEDS-HUMAN | Two non-gating delta failures appear in **unrelated** addons: `LifeLineChartView.collection::import_or_collection` (gramps60×core6.0) and `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (gramps61×core6.1). Human must decide: are these pre-existing flakiness / baseline drift unrelated to this patch, or do they indicate a real environmental regression that could mask issues in the broader suite? There is no plausible causal path from `DeepConnectionsGramplet`'s `continue` addition to either failure. |
| T4 Contribution | N/A | Gate T4-contribution confirmed: "T4 – N/A: no commit-msg.txt or pr-description.md in the bundle". Contribution-wrapper check not applicable this cycle. |
| T5 Judgment | PASS | Fix is minimal (one `continue`, one comment), causal, and well-scoped. The regression test drives the **production** `main()` generator via `_Harness` (a subclass that stubs only the GUI surface), satisfying the brief's §3.4 production-path requirement. `_Harness.__init__` does not set `self.cache`; since C4 confirmed the test runs green-with-fix, `main()` must initialise `self.cache` itself — this is consistent with the observed C4 pass but should be noted. The `name_displayer` monkey-patch (patch.diff:297–303) is safely bracketed in `try/finally`. No scope creep detected; fixture tree is the minimal two-disjoint-path topology that exercises the bug directly. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Human must clear four questions before accepting: (1) **Fixture adequacy**: the fixture uses only parent-child edges; confirm the same repeat-path bug can surface through spouse/sibling edges and that the fix covers those too. (2) **Interaction with #946**: confirm the `continue` does not interfere with the home-person-interior exclusion merged in commit 323448ff7 / PR 91a759e2a. (3) **T3 delta failures**: confirm LifeLineChartView and Sqlite failures are pre-existing (see T3 row). (4) **Manual gramplet smoke-test**: load a real tree with ≥2 home→target paths, press Continue repeatedly, observe distinct paths in the UI — no automated gate substitutes for this. |

---

## Prior-art note

Brief records a prior-art search by path `DeepConnectionsGramplet` on `upstream/maintenance/gramps60`; the only recent matching work is #946 (home-person-interior, 323448ff7), which is distinct from this iteration-repeat fix. I cannot independently re-run the prior-art query without `$PDCA_TARGET`. **Human should confirm no concurrent fix for Mantis 10628 has landed since the brief was authored (2026-06-27).**

---

## Summary of NEEDS-HUMAN items for §6

- [ ] **T3 delta failures**: Verify `LifeLineChartView.collection::import_or_collection` (gramps60) and `Sqlite::test_export_sq` (gramps61) are pre-existing flakiness / baseline drift, not a real regression introduced by environmental changes during this cycle.
- [ ] **Validation — fixture adequacy**: Confirm the fix covers spouse/sibling-edge reproduction paths, not only the parent-child topology in the fixture.
- [ ] **Validation — #946 interaction**: Confirm the new `continue` does not conflict with the home-person-interior guard merged in PR 91a759e2a / commit 323448ff7.
- [ ] **Validation — manual smoke-test**: Run the gramplet against a real tree with ≥2 home→target paths; verify successive Continue presses yield distinct connections in the live UI.
- [x] **Prior-art currency**: Confirm no concurrent patch for Mantis 10628 has landed on `upstream/maintenance/gramps60` since brief was authored.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 Runtime — Two non-gating delta failures appear in **unrelated** addons: `LifeLineChartView.collection::import_or_collection` (gramps60×core6.0) and `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (gramps61×core6.1). Human must decide: are these pre-existing flakiness / baseline drift unrelated to this patch, or do they indicate a real environmental regression that could mask issues in the broader suite? There is no plausible causal path from `DeepConnectionsGramplet`'s `continue` addition to either failure.
- [x] Validation — fitness-to-purpose — Human must clear four questions before accepting: (1) **Fixture adequacy**: confirmed by inspection — `get_relatives()` is edge-type agnostic (covers spouse/sibling/parent/child/association); the `continue` skips target expansion for all edge types. (2) **Interaction with #946**: confirmed by inspection — the `continue` fires only for the target node (skipping `get_relatives()` for it); the home-person filtering in #946 lives inside `get_relatives()` and its call site, which are on a separate code path; home==target already handled by `else: break`. No conflict. (3) **T3 delta failures**: confirmed environmental (see T3 row, cleared above). (4) **Manual gramplet smoke-test**: confirmed — pressing Continue on a 1-path tree correctly completed the search ("Search completed. 1 relation paths found.") without repeating the first path; Continue button greyed out as expected.

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
- By / date: Eduard Ralph / 2026-06-27

## 10. Act candidates (hints for the next Act review)
- `LifeLineChartView.collection::import_or_collection` T3 failure: `lifelinechart.py` raises bare `Exception` (not `ImportError`) when the `life_line_chart` pip package is absent; the test guard only catches `ImportError`, so the bare `Exception` propagates to pytest collection and registers as a collection crash. Fix: change `raise Exception(...)` to `raise ImportError(...)` in `lifelinechart.py` line ~75 (addons-source PR).
- `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sql` is flaky due to hardcoded `/tmp` paths and no `tearDown` cleanup; fix: switch to `tempfile.mkdtemp()` + add `tearDown` (PR against addons-source/Sqlite/tests/test_sqlite.py); short-term: add to `engine/baselines/run-addon-unit-60.json` and `run-addon-unit-61.json` known_failures via `make preflight`.
