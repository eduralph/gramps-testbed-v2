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
