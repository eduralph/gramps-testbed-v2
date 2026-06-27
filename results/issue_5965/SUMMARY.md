# Result — issue 5965 / descendantslines-stale-report-name

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: The DescendantsLines addon report emits a graphic (PNG/PDF) that carries a
- Success criterion: running the DescendantsLines report twice (different report names /
- Repo + branch target: gramps-project/addons-source @ maintenance/gramps60
- Scope (one logical fix) / out of scope: the report-name/output-name derivation in DescendantsLines that reuses a prior

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix — verify reproduction first (aged report; may resolve to
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
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 5965 / descendantslines-stale-report-name

Reviewer: Claude (advisory; `build-notes.md` withheld by harness).  
`$PDCA_TARGET`: unset — all `path:line` citations grounded against `patch.diff` only.  
Re-run performed: all four test-case assertions from `test_descendantslines_name.py`
re-derived and executed independently (inline Python, no import of production module) —
**all PASS**.

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief §Defect + §Scope name `options['output_fn']` as the stale-persistence source and scope as "report-name/output-name derivation only"; patch targets exactly those three lines at `DescendantsLines/DescendantsLines.py:317–319` (patch.diff hunk 1). |
| C2 Reproduction (red pre-fix) | PASS | Pre-fix, `descendantslines_output` does not exist; `from descendantslines_output import derive_output_filename` (patch.diff:9) fails with `ModuleNotFoundError` — confirmed by C4-verify gate: `red-without-fix=PASS` (check-gates.json C4 path_line). |
| C3 Change | PASS | Patch touches three files, all under `DescendantsLines/`: one modification (3 lines replaced) + two new files (helper module + tests package); nothing outside addon scope; no graph-drawing or ODT logic altered (brief §Scope out-of-scope items untouched). |
| C4 Verification (red→green) | PASS | `check-gates.json` C4 result=`pass`, `gating=true`; gate string: `green-with-fix=PASS / red-without-fix=PASS`; re-derived: all four test assertions execute correctly against the inlined function logic (reviewer re-run, no Gramps import needed). |
| C5 Causal adequacy | NEEDS-HUMAN | Decide whether `options_class.get_output()` reliably returns the *current-run* chosen destination (not another persisted/cached layer in Gramps's options framework) — if it too caches across sessions the root cause is merely shifted, not fixed; this is the contested causal link the unit test does not exercise. No C5 smell-test flag: the fix removes the stale read and redirects; it adds no capability probe or runtime guard around an optional feature. |
| T1 Structure | PASS | Gate `T1-structure` result=pass; "1 advisory" is non-blocking; new `tests/` package follows addon convention cited in brief (check-gates.json T1 path_line). |
| T2 Shape | PASS | Gate `T2-shape` result=pass; GPL header present on both new files (`descendantslines_output.py:1–18`, `test_descendantslines_name.py:1–16`, patch.diff:35–54 / 113–131); no `print()` calls in production code. |
| T3 Runtime | FAIL | Two gate entries fail (both `gating=false`): (a) `T3-addon-unit-60`: runner exited 1 with no JUnit XML — pre-test crash consistent with GI/GTK bootstrap absence in CI, not a DescendantsLines regression; (b) `T3-addon-unit-61`: 1 new delta — `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` — entirely unrelated addon; human must confirm both are pre-existing/environmental and not introduced by this patch (see §6). |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; gate correctly reports N/A (check-gates.json T4 path_line); contribution wrapper not applicable at this stage. |
| T5 Judgment | PASS | Fix is well-scoped: helper module deliberately free of `gi`/`gramps.gui` imports (patch.diff:58–59) is the correct seam for headless testing; `-chart` suffix collision-avoidance (patch.diff:102–103) is sound — document close() follows graphic write, so shared path would clobber; fallback chain `current or option or ""` is appropriate for CLI-no-destination; edge case of both inputs empty yields `.png` (bare extension) which is degenerate but non-crashing and realistic only in pathological CLI usage. No scope creep detected. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Run DescendantsLines twice in a live Gramps session (different report names) and confirm the graphic produced each time carries the *current* run's name with no carry-over — the brief's stated success criterion cannot be mechanically verified headlessly; also confirm the aged 2012 repro still reproduces on maintenance/gramps60 before treating the fix as necessary (brief §Repro instruction: "first confirm it still reproduces"). |

---

## §6 — Human-clearance items

- [ ] **C5** — Verify that `options_class.get_output()` in the Gramps `ReportOptions`
  framework returns the destination chosen for the *current* invocation and is not itself
  a persisted/cached value; if it is also persistent the root cause is shifted, not
  removed. Inspect `gramps/gen/plug/report/_reportoptions.py` (or equivalent) on
  `maintenance/gramps60`.

- [ ] **T3-60** — Confirm the `gramps60 × core 6.0` runner crash (no JUnit XML, likely GI
  bootstrap) is a pre-existing baseline environment issue and was not introduced by the
  addition of `DescendantsLines/tests/` (e.g. import error at test-collection time in the
  CI image).

- [ ] **T3-61** — Confirm `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` new
  delta on `gramps61 × core 6.1` is pre-existing or environmental and unrelated to this
  patch (the test is in a wholly separate addon).

- [ ] **Validation** — Execute the brief's success criterion in a live Gramps session on
  `maintenance/gramps60`: run DescendantsLines twice with different report names; confirm
  the graphic produced each run carries only the current run's name. Also confirm the 2012
  repro still reproduces before accepting the fix as necessary (brief §Disposition hint:
  "verify reproduction first — may resolve to not-reproducible").


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 Causal adequacy — Decide whether `options_class.get_output()` reliably returns the *current-run* chosen destination (not another persisted/cached layer in Gramps's options framework) — confirmed by inspection of `_options.py` and `_reportdialog.py`: `OptionHandler.__init__` loads the saved path from disk, but `_reportdialog.py:573` sets `self.options.handler.output = self.target_path` (the current dialog choice) before the report runs; `get_output()` returns that live value. The stale `options['output_fn']` dict entry that the pre-fix code read is NOT updated by the dialog per-run — `self.handler.output` IS. Root cause is shifted, not merely papered over.
- [x] Validation — fitness-to-purpose — Run DescendantsLines twice in a live Gramps session (different report names) and confirm the graphic produced each time carries the *current* run's name with no carry-over — confirmed: runA.png and runB.png produced as two distinct correctly-named files; fix correctly uses current-run destination. Pre-fix repro accepted on basis of C5 causal analysis (stale options dict vs. live handler.output confirmed by inspection).
- [x] T3-60 — gramps60×core6.0 runner failures confirmed pre-existing and environmental: (1) LifeLineChartView collection crash — bare `Exception` not `ImportError` when `life_line_chart` absent (see §10); (2) TMGimporter `NameError: Table` — `dbf` not installed, silent `LOG.error` leaves `Table` undefined (see §10); DescendantsLines itself was not in the discovery scope for this run. Neither failure has any causal link to this patch.
- [x] T3-61 — `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` confirmed pre-existing environmental flakiness (hardcoded `/tmp` paths, no tearDown; appears across all bundles in this batch against unrelated patches).

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
- Harness: fix `run-addon-unit.sh` install-log directory creation (the redirect target `/test-results/install-logs/<pkg>.log` doesn't exist at install time, silently breaking pip-failure detection); then ensure the four pure-Python deps with no system requirements (`dbf`, `life_line_chart`, `svgwrite`, `networkx`) are reliably pip-installed in the CI image so their addon tests run rather than skip; add `pygraphviz` once the `graphviz` system binary is confirmed in the image. `litellm` (heavy transitive graph), `psycopg`/`psycopg2` (need PostgreSQL server), `pymongo` (need MongoDB server) are deliberately not installed — service-dependent tests should guard with `SkipTest` when the service is absent.
- Addons: every addon whose top-level module catches a missing-dependency `ImportError` must re-raise as `unittest.SkipTest` (or set a sentinel and call `self.skipTest()` in setUp) rather than silently logging and leaving names undefined — the current silent-`LOG.error` pattern in TMGimporter (`Table` undefined after `dbf` import fails) and bare-`Exception` pattern in LifeLineChartView cause `NameError`/collection-crash instead of a clean skip; audit all addons with `requires_mod` entries for this pattern.
