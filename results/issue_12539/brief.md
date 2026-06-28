# Brief — issue 12539 / families-children-tab-refresh

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** families-children-tab-refresh
- **Defect:** In the Families view, the bottom "Children" tab does not refresh to match
  the family that becomes selected after a filter/Find operation. After typing a filter
  (e.g. Father = "Simpson") and pressing Find, the family list changes and a different
  family is current, but the Children tab still shows the previously-selected family's
  children (or none), until the selection is manually re-clicked.
- **Success criterion:** After a filter/Find changes the Families list and the active
  family, the Children tab shows the currently-selected family's children without a manual
  re-selection.
- **Invariant to restore:** The detail tabs of a view track the view's current selection —
  when the active row changes (including programmatically after a filter), the embedded
  Children tab is rebuilt for the new selection. (Behavioural consistency invariant;
  rationale: the detail tab is a projection of the selected object and must follow it.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — touches the Families view's selection→detail-tab refresh
  coupling (`familyview.py` and its `signal_map`); a reviewer must confirm the
  filter-driven selection change reaches the children tab.
- **Scope:** the missing Children-tab refresh on a filter/Find-driven selection change in
  the Families view (`gramps/plugins/view/familyview.py`). / out of scope: the filter
  engine itself, the People/other views, manual click-driven selection (which already
  works).
- **Repro instruction:** load a tree with several Simpson families (reporter's
  attachment, or example.gramps families) → Families view → ensure the Children tab is
  shown → in the filter pane set Father = "Simpson", press Find → list narrows and a
  family becomes current → the Children tab does not match the now-current family until
  re-clicked.
- **Test file:** engine/interface/test_bug_12539_families-children-refresh.py (committed
  AT-SPI repro; `Surfaces: gui` → `C4-verify-interface`). If the selection→children
  refresh is reachable headlessly, additionally ship a core `*_test.py` driving the
  production refresh path (principles §3.4); otherwise record C4 (unit) unverifiable for
  human sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected for the gramps tree; a new core `*_test.py` →
  `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/view/familyview.py`
  on `upstream/maintenance/gramps61` — null-parent-handle guard and calendar/reformat
  commits only; no children-tab refresh-on-filter fix. No matching fork PR by this path. →
  unfixed.
- **Mantis:** 12539
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
