# PR description

## Root cause

The bottombar `FamilyChildren` gramplet rebuilds only on the Family `active-changed` signal (gramps/plugins/gramplet/children.py:229, `connect_signal("Family", self.update)`). When a filter/Find runs and the previously-active family is filtered out, `ListView.build_tree` → `goto_active` path cannot select it and only unselects (gramps/gui/views/listview.py:485-487), so the active family handle never actually changes, `active-changed` never fires, and the Children tab is left showing the now-hidden family until a manual re-click.

## Fix

Override `FamilyView.build_tree` to detect when the previously active family was filtered out and is no longer visible. After the base `ListView.build_tree` rebuild, the override calls `change_active` with the first visible family handle (gramps/gui/views/navigationview.py:206-212), which fires the `active-changed` signal the Children gramplet listens to. The active-family selection decision is extracted into a new, gi-free helper module `gramps/plugins/view/familyview_selection.py` with a pure function `resolve_active_after_filter(active_handle, visible_handles)` that applies these rules:

- no active family → `None` (preserve "nothing selected at startup" behavior)
- active still visible → keep it (no spurious signals)
- active filtered out, list non-empty → first visible (the Mantis 12539 fix)
- active filtered out, nothing visible → `None`

Both the filter sidebar gramplet (gramps/plugins/gramplet/filter.py:76-77) and the quick SearchBar route through `FamilyView.build_tree`, so the fix covers both the brief's sidebar repro and the quick filter.

## Verified against

- gramps/plugins/gramplet/children.py:229 — Children gramplet updates only on Family active-changed signal
- gramps/gui/views/listview.py:375,404-405,485-487 — build_tree/goto_active and the unselect-on-missing-active path
- gramps/plugins/gramplet/filter.py:76-77 — sidebar filter calls build_tree  
- gramps/gui/views/navigationview.py:206-212 — change_active pushes handle and fires active-changed
- gramps/plugins/view/familyview.py:144-148 — insertion point for the override

## Test

**Unit test (headless, gated red→green):** `gramps/plugins/view/test/familyview_selection_test.py` drives `resolve_active_after_filter` directly, covering the 12539 scenario (active filtered out → first visible), active-still-visible (no spurious signal), no-active-no-autoselect, and the empty-list cases. The decision logic is tested as a pure function before GUI wiring; production and test call the same function so they cannot drift.

**Interface test (AT-SPI, advisory):** `engine/interface/test_bug_12539_families-children-refresh.py` opens the Families view, shows the Children tab, finds two families with distinct non-empty children, selects one, then drives the sidebar Family Filter so the first is filtered out and asserts the Children tab refreshes to the second family's children with no manual re-click. This covers the end-to-end GUI refresh on a filter-driven selection change.

Fixes #12539
