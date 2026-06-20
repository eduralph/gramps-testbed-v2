# Brief — issue 13864 / dashboard-column-count-crash-locks-tree

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** dashboard-column-count-crash-locks-tree
- **Defect:** On the Dashboard, "Configure the active view" → "Gramplet Layout" → "Number of Columns:" set to a large value (reporter used **1000**) freezes Gramps ("Not responding"), then it disappears with no error; on restart the family tree is **locked**. (Mantis 13864; confirmed on 6.0.1, note 1.)
- **Success criterion:** Setting the Dashboard "Number of Columns" to any value the field accepts (including a large one such as 1000) does **not** crash Gramps and does **not** leave the family tree locked — the gramplet layout either applies a sane (clamped/validated) column count or rejects the input, and Gramps stays responsive.
- **Invariant to restore:** Any column-count value the "Number of Columns" control accepts must yield a survivable Dashboard layout — applying it never crashes the process or leaves the tree locked. (A user-supplied layout parameter must be bounded/validated before it drives widget allocation. Source: the gramplet-bar layout path in `gramps/gui/widgets/grampletbar.py` and the Dashboard view's config handler.) SELF-TEST: clamping in one setter would help, but the invariant is stated over *any accepted column value → no crash/lock*, i.e. the defect category, not the single 1000 repro.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core).
- **Conflicts with:** 13865   (same Dashboard / gramplet-layout column code — never co-schedule in one concurrent wave; verify shared cause before assuming one fix)
- **Surfaces:** gui
- **Scope:** an extreme/large Dashboard column count crashes Gramps and locks the tree — make the column-count path survivable for any accepted value. / **out of scope:** redesigning the Gramplet-Layout UX or imposing a product-level max-columns policy (that is a UX-direction call — flag to the human if the only viable fix is a hard cap); the separate gramplet-placement defect in 13865 (verify whether one root cause covers both **before** writing a shared fix — the verdict says these likely differ).
- **Repro instruction:** open `example.gramps` → Dashboard → "Configure the active view" → "Gramplet Layout" → set "Number of Columns" to 1000 → observe freeze, crash, then locked tree on restart. Root cause **not** diagnosed in-thread (note 1 is only "Confirmed on 6.0.1!") — Do must reproduce and trace; likely an unbounded loop/allocation over the column count in the gramplet-bar layout. A headless repro via the Dashboard/grampletbar layout model is preferred if the path is reachable without the live GUI.
- **Test file:** prefer a **headless** core unit test if the column-count → layout path is reachable without a running GUI: `gramps/gui/test/grampletbar_test.py` (or the appropriate `gramps/gui/.../test/` package for the module Do pins) — `test/` singular, `*_test.py` suffix (INTEGRATION §3) — asserting a large column count does not raise/hang and produces a bounded layout. If the crash is only reproducible through the live GUI, ship an interface test `tests/interface/test_bug_13864_dashboard_columns.py` in gramps-testbed (advisory; subclass `GrampsInterfaceTestCase`) and flag the C4 red→green mechanic as **unverifiable** (`PDCA-UNVERIFIABLE`) per INTEGRATION §3 for the human to clear at C6.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change.
- **New/removed files:** if a new core `test/` file is added, register it in `po/POTFILES.skip` (no translatable strings) per doc 16 §Adding and removing Python files.
- **Prior-art check (triage cycles):** search by path at Do time — `git -C ../gramps log upstream/maintenance/gramps61 -- gramps/gui/widgets/grampletbar.py` (also `master`) + closed/rejected PRs for "dashboard" / "gramplet" / "columns".
- **Mantis:** 13864
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: The shipped test (grampletconfig_test.py) exercises only the extracted helper clamp_column_count, not the GUI crash path in GrampletPane; revoking the production clamp calls in grampletpane.py leaves the test green — C4 red→green is decoupled from the actual fix. This is the second occurrence of this pattern. Do must: (1) remove the helper-only test; (2) add a PDCA-UNVERIFIABLE flag per brief.md:17 (GUI-crash path is headless-unverifiable); (3) ship an interface test in gramps-testbed (tests/interface/test_bug_13864_dashboard_columns.py) as the reproduction vehicle. C5 is confirmed clean (self._config.set always routes through set_columns via the registered setter). T3 delta is pre-existing/environmental. T5/V (MAX_GRAMPLET_COLUMNS=100, silent-clamp) to be raised with the maintainer in the PR.
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: gramps core unit suite (whole-suite baseline) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest) — raw runner o
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
