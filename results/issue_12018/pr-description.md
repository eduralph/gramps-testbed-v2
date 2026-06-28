# Organize Tags dialog: bind type-ahead search to Name column

## Root cause

The Organize Tags dialog builds its tag list in a `Gtk.TreeView` that ships with interactive type-ahead search enabled by default, but the code never called `set_search_column()`, leaving the search at GTK's default value of -1. With no target column, the equal-func has nowhere to match, so pressing Ctrl-F (or typing) displays the search box but never moves the selection to the matching tag.

## Fix

Add module-level helpers to bind the TreeView's interactive search to the visible Name column (model index 2):

- **`_TAG_NAME_COL = 2`** — module constant naming the Name column index
- **`_tag_list_columns()`** — returns the tag list's column definitions (extracted from `_create_dialog` to be shared with the test)
- **`_setup_tag_search(treeview)`** — calls `treeview.set_search_column(_TAG_NAME_COL)` to bind the search

The dialog now calls `_setup_tag_search(self.namelist)` after creating the TreeView and model, so the type-ahead search actually jumps to the matching tag by name instead of being inert.

## Verified against

- **`gramps/gui/views/tags.py:370-374`** — the `make_callback` function, where the new module-level helpers are inserted after (lines 377–421 pre-patch)
- **`gramps/gui/views/tags.py:478-485`** — the `name_titles` list and TreeView creation in `_create_dialog`, now refactored to use `_tag_list_columns()` and call `_setup_tag_search()`
- **`gramps/gui/listmodel.py`** — verified that `ListModel` never sets a search column, confirming the root cause is not elsewhere
- **`po/POTFILES.skip:469-472`** — the `gui/views` section where the new test package (`gramps/gui/views/test/__init__.py` and `gramps/gui/views/test/tags_test.py`) must be registered (no translatable strings)

## Test

The patch ships a regression test at `gramps/gui/views/test/tags_test.py` (2 test cases):

1. **`test_name_column_index_matches_visible_name_column`** — asserts that `_TAG_NAME_COL` points at the visible Name column in the production column layout
2. **`test_search_bound_to_name_column`** — drives the production helper `_setup_tag_search()` with a recording stand-in (since `Gtk.TreeView()` cannot be instantiated on the headless runner) and asserts that the search column is set to `_TAG_NAME_COL` and not left at the inert default of -1

The test imports the production helpers and driven by the production column layout and binding code, not copies of them. The helper extraction ensures the test verifies the actual binding through the production seam (principle §3.4: *drive the production widget, not a copy*).

End-to-end manual verification: open People list → Edit → Tag → Organize Tags…, add several tags, then type a tag's name — the selection now jumps to the matching tag instead of the search box doing nothing.

Fixes #12018
