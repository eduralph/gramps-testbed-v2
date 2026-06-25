# check-review.md — Issue 3068 / detdescendant-duplicate-person-number (Iteration 2)

> Reviewer: Claude (advisory, artifact-only). `PDCA_TARGET` is unset — all
> `path:line` citations ground on `patch.diff` and the three supplied artefacts
> only. No builder rationale (`build-notes.md`) was received.

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | brief.md clearly states defect (last-path number wins), success criterion (first/smaller Henry number for duplicated descendant), and scope boundary (Henry only; d'Aboville/Modified-Henry flagged as possible residuals, explicitly out of scope). |
| C2 Reproduction (red pre-fix) | NEEDS-HUMAN | Verify-first scenario: PR #100 already merged the fix; no pre-fix tree is available to demonstrate red. Human must accept PDCA-UNVERIFIABLE as the evidence basis (brief.md:32–34) and confirm the git history shows the unconditional assignment before merge commit 9a516b1. |
| C3 Change | PASS | patch.diff touches one file only (`gramps/plugins/test/reports_test.py`; +116 lines, no deletions). `_HenryProbe` assigns `DetDescendantReport.apply_henry_filter` at class-definition time (patch.diff:29) and initialises the five attributes the method reads (`_db`, `max_generations`, `dnumber`, `map`, `gen_keys`; patch.diff:33–36). Test builds the exact cousins-have-a-child structure from the bug report and asserts `probe.dnumber[self.f] == "1111"` (patch.diff:125–129). No production code is changed. |
| C4 Verification (red→green) | NEEDS-HUMAN | Gating gate (check-gates.json C4, `gating:true`) carries result `"unverifiable"` (verify-first). Previous iteration failed run-verify.sh with "a real failure, not a missing prerequisite" (brief.md:55). This iteration moves the test from a new standalone file into the existing `reports_test.py`; this addresses runner-discovery but does NOT change test logic — if iteration-v1 failed on test execution rather than discovery, the same failure may recur. Human must run the new test under `run-verify.sh` on the 6.1 tree to confirm green before accepting C4. |
| C5 Causal adequacy | PASS | No capability probe or runtime guard added (no `hasattr`, `try`/`except`-import, `getattr`, or feature-check anywhere in patch.diff). `_HenryProbe` is a test harness, not a production guard. The test exercises the real production keep-the-smaller-number guard (PR #100, `apply_henry_filter`) without papering over a load-time side effect. C5 smell-test: no trigger. d'Aboville / Modified-Henry unconditional-assignment residuals are correctly noted out of scope. |
| T1 Structure | N/A | Core-only change; no `addons-source` path appears in patch.diff. Addon §Structure rules (folder==id, target_version, fname, no `__init__.py`) do not apply. Confirmed by check-gates.json T1 result. |
| T2 Shape | PASS | The touched file already carries a GPL header. No new `.py` file is added by the patch (builder changed from two new files in iteration-v1 to modifying an existing file), so no POTFILES.in / .skip registration is required. check-gates.json T2-shape and T2-potfiles both `pass`; T2-potfiles is gating. |
| T3 Runtime | PASS | check-gates.json T3-unit result `pass`: baseline matches 7 known reds. ⚠ Tree drift noted (`detached@674e3b`); gate treats this as non-blocking. |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle. check-gates.json T4 result `pass` (N/A). |
| T5 Judgment | PASS | Embedding the test in the existing `reports_test.py` is a sound strategy: the file is known to be picked up by the runner and already exercises report infrastructure. The `_HenryProbe` technique is correct Python 3 — assigning an unbound function as a class attribute and calling it on an instance binds `self` correctly, so the production method's recursive `self.apply_henry_filter(...)` calls resolve through the probe without indirection. Sanity assertions on a, b, c, d, e (patch.diff:115–119) make the test self-diagnosing. Risk: if the iteration-v1 failure was in `make_database("sqlite")` / `db.load(":memory:")` rather than file discovery, the same failure will recur — this is the C4 NEEDS-HUMAN item above. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Three decisions required before sign-off: (1) confirm the new test passes green under `run-verify.sh` on the 6.1 tree (resolves C4); (2) confirm PR #100's keep-the-smaller-number guard is present at `apply_henry_filter` lines ~239–243 on `maintenance/gramps61` (the production fix this test covers); (3) record a disposition for the d'Aboville / Modified-Henry unconditional-`dnumber` assignments (same wrong-number bug for those modes) — note for a follow-on issue or mark WONTFIX for this cycle. |

---

## §6 Human-clearance items

- [ ] **C2** Confirm git log on `maintenance/gramps61` shows `apply_henry_filter` assigned `dnumber` unconditionally before merge commit 9a516b1 (establishes the red pre-fix basis).
- [ ] **C4** Run the new test under `run-verify.sh` on the 6.1 tree and confirm it exits green. If it fails, determine whether the failure is in `make_database("sqlite")` / `db.load(":memory:")` initialisation (test infrastructure) or in the assertion itself (fix not present / wrong number).
- [ ] **V(1)** Confirm PR #100's keep-the-smaller-number guard exists at the expected location (`apply_henry_filter` ~lines 239–243 on `maintenance/gramps61`).
- [ ] **V(2)** Disposition for `apply_daboville_filter` and `apply_mhenry_filter` unconditional `dnumber` assignments — these exhibit the same wrong-number symptom for d'Aboville and Modified-Henry numbering modes. Record as a follow-on issue or close as WONTFIX for this cycle.

---

## Notes

**Scope delta from brief:** brief.md:37–38 anticipated two new files (`gramps/plugins/textreport/test/__init__.py` and `detdescendantreport_test.py`). The patch instead adds test code directly to the existing `gramps/plugins/test/reports_test.py`. This is a deliberate change of approach from iteration-v1 and is not a defect — T2-potfiles passed because no new file requires registration. No production file is modified in either iteration.

**Prior-art check:** brief.md:39–43 records the triage search. PR #100 (merge commit 9a516b1, "bug3068", SNoiraud) is the only prior work on this defect; no duplicate or conflicting fix was found. Mechanically settleable from the brief's record; no further prior-art NEEDS-HUMAN item raised.

**Fork-discipline note:** `maintenance/gramps61` is a downstream maintenance branch, not the canonical upstream `master`. The test targets the 6.1 branch's version of `apply_henry_filter`. If the method's attribute surface differs between `master` and `maintenance/gramps61`, the `_HenryProbe` initialiser (patch.diff:31–36) may need adjustment — this is covered by the C4 human-run item above.
