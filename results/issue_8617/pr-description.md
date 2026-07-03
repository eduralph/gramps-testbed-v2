# Filter gramplet in Bottombar now respects filter when sidebar hidden

## Summary

When a user adds the Filter gramplet to the Bottombar and hides the sidebar, applying a filter through the gramplet has no effect—the list view remains unfiltered. This defect affects all list views (People, Events, Sources, Places, etc.). With the sidebar shown, the same gramplet works correctly. The fix restores the filter behavior by checking for an explicitly-set filter before deciding whether to use the Search bar, making the filter apply regardless of sidebar visibility.

## What to look at

The fix is a two-token condition change at the filter-selection logic in the shared `ListView` base class:
- `gramps/gui/views/listview.py:335` — decision in `build_tree()` when rebuilding the model
- `gramps/gui/views/listview.py:786` — decision in `column_clicked()` when re-sorting

To reproduce the issue pre-fix: open the People view, add the Filter gramplet to the Bottombar, hide the sidebar (View → Sidebar), type a surname in the gramplet's Name field, and press Find. Pre-fix: the list is unchanged. Post-fix: the list is filtered to show only matching rows.

## Root cause

The Filter gramplet (the same UI component whether docked in the sidebar or Bottombar) sets `view.generic_filter` and calls `build_tree()` to apply the user's chosen filter. However, `build_tree()` and `column_clicked()` decided whether to use that `generic_filter` or the Search bar's value **purely on Search-bar visibility**. The sidebar toggle directly couples Search-bar visibility to sidebar visibility: the Search bar is shown exactly when the sidebar is hidden. So: sidebar hidden → Search bar visible → `build_tree` uses the empty Search value and the gramplet's filter is silently dropped.

## Fix

Change the filter-selection condition at both sites to check whether `generic_filter is not None` before checking Search-bar visibility. This makes an explicitly-set filter win over Search-bar visibility, restoring the invariant that a filter the user has explicitly set via the gramplet must be applied to the list, whichever bar hosts it.

The change is in the shared `ListView` base class (`gramps/gui/views/listview.py`), so it applies to every `ListView` subclass (People, PersonTree, Events, Sources, Places, Citations, Repositories, Media, Notes, Families) rather than being a single-view special case.

## Verified against

- `gramps/gui/views/listview.py:335` — the filter-selection condition in `build_tree()` that decides between `generic_filter` and Search-bar value
- `gramps/gui/views/listview.py:786` — the identical filter-selection condition in `column_clicked()` for re-sort model rebuilds
- `gramps/plugins/gramplet/filter.py:76-77` — the Filter gramplet sets `self.gui.view.generic_filter` and calls `self.gui.view.build_tree()` to apply the user's selection
- `gramps/gui/views/listview.py:432-440` — `sidebar_toggled()` method coupling Search-bar visibility to sidebar visibility

## Test

Regression test: `engine/interface/test_bug_0008617_bottombar_filter.py` (AT-SPI/dogtail repro in the testbed, `Bug8617BottombarFilterTest`)

- **Red (unpatched worktree):** sidebar hidden, Filter gramplet in Bottombar, apply "Warner" surname filter → list unchanged, status bar shows matched/total unchanged (e.g., `People: 100/100`)
- **Green (patched worktree):** same sequence → list filtered to matching surnames, status bar shows fewer matched (e.g., `People: 14/100`)

The oracle is the status-bar filter label, which reflects the actual count of model rows displayed—immune to GtkTreeView row virtualization and works even for the grouped default People view.

Fixes [#8617](https://gramps-project.org/bugs/view.php?id=8617)
