# Check-Review — issue 10415 / familylines-graph-prunes-direct-ancestors

**Reviewer:** Claude subagent (advisory; no Write/Edit access)  
**Date:** 2026-06-27  
**Grounding:** `patch.diff` only — `PDCA_TARGET` is unset; citations are against patch.diff line numbers.  
**build-notes.md:** deliberately withheld.

---

## Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief precisely names root cause (surname-equality test, `remove_uninteresting_parents`, lines 772-791/804-806), success criterion (direct-line ancestors retained regardless of surname spelling), scope (pruning decision only), testable-seam requirement, and POTFILES registration — spec is complete and unambiguous. |
| C2 Reproduction (red pre-fix) | PASS | No standalone C2 gate configured (check-gates.json result="none"), but C4 gate explicitly reports "red-without-fix=PASS"; pre-fix, the surname-equality guard in `remove_uninteresting_parents` would fail to match I0005 "Smyth" against interest-set surname "Smith", causing `assertIn(I0005_handle, people)` at gvfamilylines_test.py:644-648 to fail — consistent with the described defect. |
| C3 Change | PASS | Three-file change: (1) `FamilyLinesSelection` extracted with `_direct_ancestors()` BFS guard injected before surname-equality check (patch.diff:244-251, 260-293); (2) new test exercising production `find_parents`+`remove_uninteresting_parents` on a real in-memory DB fixture (patch.diff:483-677); (3) test file registered in `po/POTFILES.skip` (patch.diff:685). All edits are within the brief's stated scope; surname-colour, sibling/spouse heuristics, and limit-ancestors option are untouched. |
| C4 Verification (red→green) | PASS | check-gates.json C4-verify (gating=true): "green-with-fix=PASS / red-without-fix=PASS". PDCA_TARGET unset so independent re-run not possible; accepting the gate's evidence as stated. |
| C5 Causal adequacy | PASS | The fix adds a missing lineage-membership criterion — a BFS over parent-family links (`_direct_ancestors()`, patch.diff:260-293) — directly to the pruning decision that previously consulted only surname text. The guard is not a capability probe (no `hasattr`/`try-import`); it removes a class of people from the pruneable set by correcting the root cause. C5 smell-test does not fire. |
| T1 Structure | N/A | Core-only change; no addons-source path in patch.diff. §Structure (doc 16) is addon-only — confirmed by check-gates.json "T1 – N/A". |
| T2 Shape | PASS | GPL header present (gvfamilylines_test.py lines 1-16, patch.diff:489-506); new test file registered in `po/POTFILES.skip` (patch.diff:685); gate confirms both T2-shape and T2-potfiles pass. |
| T3 Runtime | NEEDS-HUMAN | Confirm whether the 1 new delta failure (`Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq`, check-gates.json path_line) is pre-existing/flaky or a regression — patch touches only the graph plugin and POTFILES.skip, so a causal link to SQLite export is implausible, but the baseline delta must be cleared by a human before the cycle can close. |
| T4 Contribution | N/A | No commit-msg.txt or pr-description.md in the bundle — confirmed by check-gates.json "T4 – N/A". |
| T5 Judgment | PASS | Approach is sound: `FamilyLinesSelection` correctly separates GUI-free selection logic from the report class, enabling direct unit testing per principles.md §3.4. `_direct_ancestors()` BFS is unconditionally complete (does not respect `limitparents`), which is a safe over-approximation — `remove_uninteresting_parents()` only inspects people already in `_people` (bounded by `find_parents()`), so surplus ancestors in the BFS set are never seen by the pruning loop. Two minor notes: (a) the test inspects `selection._people` directly (private attribute — acceptable for a regression unit test); (b) `import_as_dict(person_prefix=…, family_prefix=…)` kwargs at gvfamilylines_test.py:599-601 are not verified against the target API signature (PDCA_TARGET unset), but C4 green implies the call succeeded in the build environment. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Decide whether the synthetic 7-person fixture (Smith/Smithe/Smyth chain) is sufficient coverage for the reporter's real-world tree before merge — the success criterion in the brief requires that the actual Family Lines Graph (GUI report with a real Gramps tree exhibiting surname drift) matches with removeextra ON vs OFF for the direct line; a manual smoke-test against the reporter's original fixture tree (exclude.pdf ≈ include.pdf) is needed to close this. |

---

## Notes

### C5 smell-test detail
`_direct_ancestors()` (patch.diff:260-293) is a lazy-cached BFS that walks `person.get_parent_family_handle_list()` iteratively. The call site at patch.diff:250 (`if person.get_handle() in self._direct_ancestors(): continue`) is inside `remove_uninteresting_parents`, which only runs when the capability (follow parents) was already exercised — but the guard is not a *capability probe* in the C5 sense: it does not check whether `_direct_ancestors` is available; it *is* the correction. The original code had no ancestry criterion at all; the guard adds one. No C5 flag.

### T3 delta failure
`Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` is unrelated to `gvfamilylines.py`. The most likely causes are flakiness (SQLite locking, temp-dir contention) or a pre-existing regression on the baseline branch. Human confirmation is the required clearing action (see §6 below).

### Scope-creep check
The refactor of `FamilyLinesReport.__init__` / `begin_report` into `FamilyLinesSelection` is motivated by the brief's testable-seam requirement (brief.md:41). `FamilyLinesReport.begin_report()` now delegates to `FamilyLinesSelection.select()` and copies back `_people`, `_families`, `_deleted_people`, `_deleted_families` (patch.diff:429-431). The public interface and the write path (`write_people`, `write_families`, `write_report`) are unchanged. This is within scope.

---

## §6 — Human-clearance checklist

- [ ] **T3 delta:** Confirm `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` failure is pre-existing or flaky on `maintenance/gramps61`, not introduced by this patch, before closing the cycle.
- [ ] **Validation — fitness-to-purpose:** Run the Family Lines Graph report (GUI, full Gramps tree with a person of interest whose direct ancestors exhibit surname-spelling drift) with "follow parents" ON and "remove extra people" ON, and confirm the direct line matches the removeextra=OFF output (reporter's exclude.pdf ≈ include.pdf for the direct line).
