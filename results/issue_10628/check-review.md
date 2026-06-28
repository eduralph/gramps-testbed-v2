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
- [ ] **Prior-art currency**: Confirm no concurrent patch for Mantis 10628 has landed on `upstream/maintenance/gramps60` since brief was authored.
