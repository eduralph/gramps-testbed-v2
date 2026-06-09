# Fix IndexError at startup when all view plugins are hidden (#8796)

## Root cause
When every view plugin is hidden in the Plugin Manager,
`ViewManager.get_available_views()` returns `[]`, and `views_to_show([])`
collapsed to `(0, 0, [])` — claiming category 0 exists when it does not. At
startup `init_interface` then called `goto_page(0, 0)`, whose
`self.current_views[cat_num] = view_num` indexed the empty `current_views`
list and raised `IndexError: list assignment index out of range`, crashing
Gramps before the window opened (#8796).

## Fix
`views_to_show` is made total over the empty view set: with no views it now
returns `(None, None, [])` ("no category to select") instead of
`(0, 0, [])`, and `init_interface` only navigates when a category exists, so
the app opens with no active page rather than crashing. The function is moved
into a new GTK-independent module `viewmanagerutils.py` so production and the
regression test exercise the same implementation. Two sibling entry points
that reach the same empty-view state independently of startup navigation are
guarded the same way: `__change_page` (reached via `_post_load_newdb_gui`
when a tree auto-loads with zero views) and `config_view` (the ConfigView
keyboard action) now return early when there is no page / no active page.

## Verified against
- `gramps/gui/viewmanagerutils.py:39-47` — new gi-free `views_to_show`
  returns `None, None, default_cat_views` when `views` is empty (target
  branch `maintenance/gramps61`).
- `gramps/gui/viewmanager.py:80` — `viewmanager` re-imports `views_to_show`
  from `viewmanagerutils`, so the production startup path routes through the
  exact function the test drives (no parallel copy).
- `gramps/gui/viewmanager.py:638-656` — `init_interface` unpacks the tuple
  and navigates only `if current_cat is not None`, leaving no active page on
  the empty set.
- `gramps/gui/viewmanager.py:1051-1061` — `__change_page` returns early when
  `self.pages` is empty (`get_current_page()` returns -1 on an empty
  notebook, so `self.pages[-1]`/`self.pages[0]` would raise).
- `gramps/gui/viewmanager.py:1515-1524` — `config_view` returns early when
  `self.active_page is None`, so the ConfigView action does not dereference
  `None`.

## Test
`gramps/gui/test/viewmanager_test.py` (new) drives the production
`views_to_show` headlessly and asserts `views_to_show([], use_last=False)`
and `views_to_show([], use_last=True)` both return `(None, None, [])` — the
corrected, totality-restoring contract that prevents the startup `IndexError`.

Manual GUI repro on `maintenance/gramps61`: hide every "Loaded Plugins" view
entry (or list all view plugins under `[plugin] hiddenplugins` in
`gramps.ini`) and restart — pre-fix Gramps crashes with the `IndexError`;
post-fix it opens with no active page and no exception.
