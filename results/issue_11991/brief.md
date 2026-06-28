# Brief — issue 11991 / citation-list-refresh-after-source-edit

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** citation-list-refresh-after-source-edit
- **Defect:** In the Sources view, editing a citation and saving it does not update the
  displayed citation list — the row keeps showing the pre-edit values. The user must
  select another source and come back for the change to appear.
- **Success criterion:** After a citation is edited and saved while the Sources view is
  showing that source's citations, the visible citation row reflects the saved change
  without navigating away and back.
- **Invariant to restore:** A list view reflects the current database state for the
  objects it displays — when a `citation-update` occurs, the rows showing that citation
  are refreshed. (Behavioural consistency invariant; rationale: the view subscribes to
  object-change signals precisely so the display never lags the database.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — the citation/source views already maintain `signal_map`
  subscriptions; the change is to ensure the displayed list reacts to the citation update
  in this view context, which a reviewer must trace through the view's signal wiring.
- **Scope:** the stale citation row after an in-place citation edit in the Sources view
  (`gramps/plugins/view/sourceview.py` / the citation list rendering it drives, and their
  `citation-update` handling). / out of scope: the citation editor's save logic, the
  Citations (standalone) list view's own behaviour, source-level edits.
- **Repro instruction:** example.gramps → Sources view → expand/select a source showing
  its citations → edit one citation, change a field, save → the row does not update;
  switch source and back → row now correct.
- **Test file:** engine/interface/test_bug_11991_citation-list-refresh.py (committed
  AT-SPI repro; `Surfaces: gui` → `C4-verify-interface`). If the row-update path is
  reachable headlessly, additionally ship a core `*_test.py` driving the production
  refresh handler (principles §3.4); otherwise record C4 (unit) as unverifiable for human
  sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected for the gramps tree; a new core `*_test.py` →
  `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/view/sourceview.py`
  and `citationlistview.py` on `upstream/maintenance/gramps61` — only reformat / web-
  connection-menu commits; `citation-update` signal_map exists but the stale-row case is
  unaddressed. No matching fork PR by this path. → unfixed.
- **Mantis:** 11991
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
