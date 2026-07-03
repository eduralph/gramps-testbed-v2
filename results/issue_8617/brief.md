# Brief — issue 8617 / bottombar-filter-gramplet-ignored

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** bottombar-filter-gramplet-ignored
- **Defect:** The Filter gramplet filters the list view only while the sidebar filter is
  also visible. When the sidebar is hidden (so the Filter gramplet in the Bottombar is
  the user's only filter UI), applying the gramplet's filter does nothing — the list is
  not filtered. sam888 (4.1.3) and bamaustin (5.1.3) confirmed across multiple views;
  bamaustin correctly suspected the Search bar (which is enabled precisely when the
  sidebar is hidden) is bypassing the filter.
- **Success criterion:** After the fix, applying a filter from the Filter gramplet in the
  Bottombar filters the list view regardless of whether the sidebar is shown or hidden
  (i.e. regardless of Search-bar visibility). Demonstrable by the committed AT-SPI repro:
  with the sidebar hidden and the Filter gramplet in the Bottombar, applying a filter
  reduces the visible rows (red pre-fix — rows unchanged; green post-fix).
- **Invariant to restore:** A filter the user has explicitly set via the Filter gramplet
  (`view.generic_filter`) must be applied to the list, whichever bar hosts the gramplet —
  the view's applied filter must reflect a set `generic_filter`, not be silently dropped
  because the Search bar happens to be visible. (Gramps list-view filtering rule; no
  external canon.) SELF-TEST: the property fails for a fix that only special-cases one
  view — it must hold for every `ListView` subclass.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium
- **Scope:** In `ListView.build_tree`, the choice between the gramplet's `generic_filter`
  and the Search bar's value is gated purely on Search-bar visibility (`sidebar_toggled`
  shows the Search bar exactly when the sidebar is hidden), so a Bottombar gramplet's
  `generic_filter` is ignored whenever the sidebar is hidden. Make a set `generic_filter`
  take effect independent of Search-bar visibility. / out of scope: redesigning the
  sidebar↔searchbar↔bottombar UX; the sidebar filter itself; combining a Search-bar text
  search AND a gramplet filter at once (note the precedence question below), which is a
  larger design change — restore the dropped filter first.
- **Repro instruction:** On `maintenance/gramps61`, People view: add the Filter gramplet
  to the Bottombar, hide the sidebar (View menu), enter a name or pick a custom filter in
  the gramplet, press Find — the list is not filtered. Show the sidebar again and it
  works.
- **Test file:** `engine/interface/test_bug_0008617_bottombar_filter.py` (committed
  AT-SPI/dogtail repro in the testbed; NOT in `patch.diff`). Red on the unpatched
  worktree, green on the patched one.
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause: `gramps/gui/views/listview.py:335-338` `build_tree` selecting
  `filter_info` on `search_bar.is_visible()`, and the same pattern at
  `listview.py:786-789`; `listview.py:432-440` `sidebar_toggled` ties Search-bar
  visibility to sidebar visibility; the gramplet sets `view.generic_filter` in
  `gramps/plugins/gramplet/filter.py:72-75`).
- **New/removed files:** none in gramps — `patch.diff` modifies existing files only; the
  AT-SPI repro ships in the testbed `engine/interface/`, outside gramps' POTFILES scope.
- **Prior-art check (triage cycles):** searched `gramps/gui/views/listview.py` on
  `upstream/maintenance/gramps61` — SearchBar refactors (`Extend SearchBar…`, `Change
  filter to search…`, `Fix crash… wrong filter_info`) but none restoring the Bottombar
  gramplet filter; no open/closed PR found for this defect on this path. Not already
  upstream.
- **Mantis:** 8617
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.
