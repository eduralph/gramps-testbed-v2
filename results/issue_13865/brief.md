# Brief — issue 13865 / dashboard-gramplet-offscreen-high-column-count

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** dashboard-gramplet-offscreen-high-column-count
- **Defect:** On the Dashboard with "Number of Columns" set to **20**, adding a gramplet (e.g. FAQ) below the "Top Surnames" gramplet places it **off screen**, with blank space between gramplets. Setting columns back to 2 restores correct placement (the gramplet appears directly below Top Surnames). (Mantis 13865; confirmed on 6.0.1, notes 1–2, screenshots attached.)
- **Success criterion:** With the Dashboard column count set to a high value (e.g. 20), adding a gramplet places it in a **valid, visible** column position — the new gramplet is reachable on screen and laid out without stray gaps — for any column count the control accepts.
- **Invariant to restore:** A gramplet added to the Dashboard must be placed in a valid, on-screen column slot for whatever column count is configured — adding a gramplet never positions it in a nonexistent/off-screen column. (Layout placement must map to an in-range column for any configured count. Source: the gramplet-bar placement/layout path in `gramps/gui/widgets/grampletbar.py`.) SELF-TEST: stated over *any* high column count and *any* added gramplet — the defect category — not the single 20-column repro.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core).
- **Conflicts with:** 13864   (same Dashboard / gramplet-layout column code — never co-schedule in one concurrent wave; this is a placement bug, 13864 is a crash/lock — verify whether they share a root cause before treating as one fix)
- **Surfaces:** gui
- **Scope:** a high column count mis-places a newly-added gramplet off screen — make placement land in a valid visible column for any accepted column count. / **out of scope:** the crash/lock defect of 13864 (different symptom; confirm shared-vs-distinct cause from the code before bundling); any Gramplet-Layout UX redesign or max-column policy (flag to the human if the only fix is a product-level cap).
- **Repro instruction:** open `example.gramps` → Dashboard → "Gramplet Layout" → "Number of Columns" → 20; below the "Top Surnames" gramplet, right-click → add a gramplet (e.g. "FAQ"); observe it appears off screen with gaps. Set columns back to 2 → it appears correctly below Top Surnames (note in Additional Information). Root cause **not** diagnosed in-thread — Do must reproduce and trace the column-index computation in the add/placement path.
- **Test file:** prefer a **headless** core unit test on the column-allocation / placement logic if reachable without the live GUI: `gramps/gui/test/grampletbar_test.py` (or the `test/` package for the module Do pins) — `test/` singular, `*_test.py` suffix (INTEGRATION §3) — asserting that adding a gramplet under a high column count yields an in-range, visible column index. If only reproducible through the live GUI, ship `tests/interface/test_bug_13865_dashboard_columns.py` in gramps-testbed (advisory) and flag the C4 mechanic `PDCA-UNVERIFIABLE` per INTEGRATION §3.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change.
- **New/removed files:** if a new core `test/` file is added, register it in `po/POTFILES.skip` (no translatable strings) per doc 16 §Adding and removing Python files.
- **Prior-art check (triage cycles):** search by path at Do time — `git -C ../gramps log upstream/maintenance/gramps61 -- gramps/gui/widgets/grampletbar.py` (also `master`) + closed/rejected PRs for "dashboard columns" / "gramplet layout".
- **Mantis:** 13865
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
