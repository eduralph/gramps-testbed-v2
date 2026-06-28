# Build notes — issue 12018 / tag-organize-dialog-search

## Root cause

The "Organize Tags" dialog builds its tag list in a `Gtk.TreeView`
(`gramps/gui/views/tags.py`, `OrganizeTagsDialog._create_dialog`, the
`self.namelist = Gtk.TreeView()` / `ListModel(...)` pair). GtkTreeView ships
interactive type-ahead search **enabled by default** (`enable-search` is
`True`), but the dialog never called `set_search_column(...)`, so the TreeView
kept GTK's default `search-column = -1`. With `-1`, pressing Ctrl-F (or just
typing) pops up the search entry but the equal-func has no column to match, so
the selection never moves — an enabled-but-inert control, exactly the defect the
report describes.

Verified empirically in the testbed Docker image (`gramps-testbed:ubuntu-6.1.0`):
a freshly constructed `Gtk.TreeView()` reports `get_search_column() == -1` and
`get_enable_search() == True`. `ListModel` (`gramps/gui/listmodel.py`) never sets
a search column either, so nothing downstream fixes it.

## Fix

Bind the TreeView's interactive search to the visible **Name** column (model
column index 2, after Priority(0) and Handle(1)). One added call in
`_create_dialog`: `_setup_tag_search(self.namelist)` →
`treeview.set_search_column(_TAG_NAME_COL)` with `_TAG_NAME_COL = 2`.

This is the "make it work" arm of the success criterion: typing now jumps the
selection to the matching tag by name. The Name column is a `str` column, so
GTK's default case-insensitive substring equal-func works against it.

Ordering note: `set_search_column` is called once, *after* the only
`ListModel(...)`/`set_model` call. `_populate_model` later uses
`namemodel.clear()` (not `new_model()`), so `set_model` is not called again and
the search column is not reset. Safe.

### Why functional, not disabled

The report's author (bamaustin) preferred *removing* the search
(`set_enable_search(False)`). Both arms satisfy the success criterion and the
invariant equally, and both are one production line. I chose the functional arm
because:
- The success criterion's functional phrasing — "actually scrolls/focuses the
  matching tag by name" — is the higher-value outcome for users.
- It is no larger than the disable arm (one call either way) and keeps a useful
  affordance instead of deleting one.

If Check prefers the disable arm, it is a one-line swap
(`set_enable_search(False)` and assert `get_enable_search() is False`); the test
seam (`_setup_tag_search`) is the only thing that changes.

## Why the seam (and not a one-line inline edit)

The brief flags this as an **Invariant to restore**, so the target is the
smallest change that restores the invariant — restored by a single
`set_search_column(2)`. I extracted three tiny module-level helpers
(`_TAG_NAME_COL`, `_tag_list_columns()`, `_setup_tag_search()`) purely to make
the fix verifiable headlessly *through the production path* rather than re-tested
against a copy:

- `_tag_list_columns()` is the column list lifted verbatim out of
  `_create_dialog` (no behaviour change) so the test reads the **production**
  column layout, not a copy of it.
- `_setup_tag_search()` is the exact call `_create_dialog` makes, so the test
  drives the production binding, not a re-implementation (principles §3.4).

The cost is +~25 lines of helpers, no behaviour change to the dialog beyond the
new bind. The inline alternative (`self.namelist.set_search_column(2)` with no
helper) is ~1 line smaller but would leave **no headless-testable seam**: see
below.

## Testability — why import-light + a recording stand-in

The C4 core runner is headless (`python3 -m unittest`, no DISPLAY/xvfb).
Constructing the real widget there aborts: in `gramps-testbed:ubuntu-6.1.0`,
`Gtk.TreeView()` with no display dies with

```
Gtk-ERROR: Can't create a GtkStyleContext without a display connection
exit=133
```

So the dialog/TreeView genuinely cannot be built headlessly (the brief's
anticipated case). Importing `gramps.gui.views.tags` itself is fine headless
(only class/def bodies, no widget construction — confirmed `import` exits 0).

The test therefore imports the production helpers and drives `_setup_tag_search`
with a minimal `_RecordingTreeView` that captures the single `set_search_column`
side effect. This is **not** a copy of production logic — the column layout and
the binding both come from production functions the test imports. A skip-on-no-
display test (the `@skipUnless(_HAS_GTK_DISPLAY)` pattern used by
`gallerytab_test.py`) was rejected: a skipped test "passes" on the headless
runner, which makes C4's red-without-fix leg a false PASS and fails the gate.

## Red→green proof (run in gramps-testbed:ubuntu-6.1.0)

- GREEN (fix applied): `gramps.gui.views.test.tags_test` → `Ran 2 tests ... OK`.
- RED (production `tags.py` reverted, test kept):
  `ImportError: cannot import name '_TAG_NAME_COL' from 'gramps.gui.views.tags'`
  → `FAILED (errors=1)`.

The red leg fails on the absent binding helpers — i.e. the test is red exactly
when the fix (the production seam that performs the bind) is removed, which is
the C4 contract. `git apply --check` of the bundle `patch.diff` against clean
`maintenance/gramps61` passes.

## Citations (maintenance/gramps61, pre-patch line numbers)

- `gramps/gui/views/tags.py:478-485` — the `name_titles` list + `Gtk.TreeView()`
  / `ListModel(...)` with no `set_search_column` (the defect site).
- `gramps/gui/views/tags.py:370-374` — `make_callback`, where the new module-
  level helpers are inserted after.
- `gramps/gui/listmodel.py` — `ListModel` never sets a search column (confirms
  the cause is not elsewhere).
- `po/POTFILES.skip:470-472` — `gui/views` section where the new test package is
  registered (no translatable strings).

## Files

- `gramps/gui/views/tags.py` — helpers + the `_setup_tag_search` bind.
- `gramps/gui/views/test/__init__.py` — new test package (empty).
- `gramps/gui/views/test/tags_test.py` — regression test.
- `po/POTFILES.skip` — registers the two new `.py` files (no translatable
  strings). `tags.py` already lives in `po/POTFILES.in` and is unchanged there.

`black` clean on all touched `.py` files.
