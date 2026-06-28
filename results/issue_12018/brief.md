# Brief — issue 12018 / tag-organize-dialog-search

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** tag-organize-dialog-search
- **Defect:** The "Organize Tags" dialog's tag list has GTK's interactive type-ahead
  search (Ctrl-F textbox) enabled, but it does not work — typing does not scroll/focus the
  matching tag, because the tree view's search is bound to the wrong (non-name) column.
  The control is present but non-functional, which is misleading.
- **Success criterion:** In the Organize Tags dialog, the type-ahead search either is
  removed (no nonfunctional Ctrl-F box) or actually scrolls/focuses the matching tag by
  name — i.e. the dialog no longer exposes a search control that does nothing.
- **Invariant to restore:** A list dialog does not present an interactive control that has
  no effect — either the type-ahead search targets the visible Name column or it is
  disabled. (Behavioural UI-consistency invariant; rationale: an enabled-but-inert control
  is a defect; the dialog's search state must match its actual capability.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** low — a single TreeView's search configuration in one dialog
  (`tags.py`), no cross-file reach.
- **Scope:** the nonfunctional interactive search on the tag list TreeView in the
  Organize Tags dialog (`gramps/gui/views/tags.py`, the `namelist` TreeView built from the
  `name_titles`/`ListModel` whose first column is the hidden handle). / out of scope: the
  tag colour/up/down/add/edit/remove buttons, tag application elsewhere, the "Edit the tag
  list" button hint (separate minor note in the report).
- **Repro instruction:** example.gramps → People list → Edit→Tag→Organize Tags… → add
  enough tags (e.g. a–z) to make the list scroll → press Ctrl-F (or just type) → the
  search box appears but does not move the selection to the matching tag.
- **Test file:** gramps/gui/views/test/tags_test.py (core, `*_test.py` suffix). Construct
  the dialog's tag TreeView via the production code path and assert its search
  configuration matches the chosen resolution (search disabled, or search column = the
  Name column) — drive the production widget, not a copy (principles §3.4). If the dialog
  cannot be built headlessly, ship `engine/interface/test_bug_12018_tag-search.py` and
  record C4 (unit) unverifiable for human sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** if `gramps/gui/views/test/` or `tags_test.py` is added, register
  the new test module in `po/POTFILES.skip` (no translatable strings).
- **Prior-art check (triage cycles):** searched by path `gramps/gui/views/tags.py` on
  `upstream/maintenance/gramps61` — no search-configuration fix for the Organize Tags
  TreeView. No matching fork PR by this path. → unfixed.
- **Mantis:** 12018
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
