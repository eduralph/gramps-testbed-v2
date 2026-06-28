# Brief — issue 5965 / descendantslines-stale-report-name

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** descendantslines-stale-report-name
- **Defect:** The DescendantsLines addon report emits a graphic (PNG/PDF) that carries a
  **stale report name from a previous Gramps session** rather than the name for the current
  run; the reporter also saw blank ODT/PDF alongside the correctly-graphed PNG. (Addon
  ../addons-source/DescendantsLines; reported 2012 against Gramps 3.4.0.) The "stale name"
  persisting across sessions points at a report option/name being read from saved option state
  (last-run value) instead of the current invocation, or an output filename not refreshed per
  run.
- **Success criterion:** running the DescendantsLines report twice (different report names /
  options) produces output whose embedded/﻿used name matches the *current* run, with no
  carry-over of the prior session's name. Demonstrable by C4-verify driving the addon's
  report-name/output derivation on a fixture, if a seam exists; otherwise a manual repro is
  documented (see Disposition).
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: report output reflects the current run's options/name, not state
  retained from a previous session.)
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** the report-name/output-name derivation in DescendantsLines that reuses a prior
  session's value. / out of scope: the blank-ODT symptom unless it shares the same root cause;
  the graph-drawing logic itself.
- **Repro instruction:** on ../addons-source @ maintenance/gramps60 with example.gramps, run
  Reports → Graphs → DescendantsLines once with one name, then again with a different name, and
  compare the produced graphic's name against the current run. **First confirm it still
  reproduces** — this is a 2012 report and may be stale.
- **Test file:** DescendantsLines/tests/test_descendantslines_name.py (NEW; addon `tests/`
  package, `test_*.py` prefix). Drive the production name/output derivation
  (principles.md §3.4); if the path is unreachable without the GUI, document a manual repro and
  expect C4 `PDCA-UNVERIFIABLE`.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** addon test (no core POTFILES); follow the addon `tests/` convention.
- **Prior-art check (triage cycles):** searched by path `DescendantsLines` on
  upstream/maintenance/gramps60 — recent commits are whitespace (a24fb6b38) and `import reduce
  from functools` (merge b8d2debef); neither touches report-name handling. No open/closed PR
  found for the stale-name defect.
- **Mantis:** 5965
- **Disposition hint:** likely-fix — verify reproduction first (aged report; may resolve to
  not-reproducible).
