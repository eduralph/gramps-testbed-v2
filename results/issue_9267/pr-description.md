# PR description — issue 9267

## Root cause

The flat People list caches the `(sortkey, handle)` map across rebuilds to avoid recomputing sort keys when the database hasn't changed (e.g. search or filter narrowing). When the user changes the Display Name format in Edit→Preferences→Display, the sort key itself changes (e.g. surname-first → given-first), but the view's rebuild path (`nameformat-changed` → `build_tree`) redisplays the rows without invalidating the cache, leaving the list sorted by the *previous* format until the database is reopened.

## Fix

Add a `rebuild_sort()` method to the model layer:

1. **BaseModel** (`gramps/gui/views/treemodels/basemodel.py:59-71`) — define `rebuild_sort()` as a no-op default. The hierarchical (tree) model clears and re-adds every row on each rebuild, so it re-sorts from scratch; the flat model caches the sort order and needs to override this to invalidate the cache.

2. **FlatBaseModel** (`gramps/gui/views/treemodels/flatbasemodel.py:494-497`, `:548-562`) — add a `_sort_dirty` flag initialized `False` in `__init__`. Override `rebuild_sort()` to set it `True`. In `_rebuild_search` and `_rebuild_filter`, change the cache-reuse guard from `if not allkeys:` to `if self._sort_dirty or not allkeys:` (lines 612 and 647), and clear the flag after recomputing.

3. **BasePersonView** (`gramps/plugins/lib/libpersonview.py:191-202`) — add a `_format_changed()` handler that calls `self.model.rebuild_sort()` (guarded for the pre-build `None` case) before `build_tree()`. Wire it to both `nameformat-changed` and `placeformat-changed` signals.

The same view callback is safe on both flat and tree person models because `rebuild_sort()` now exists on the common base; the tree model's no-op does nothing (it re-sorts on every rebuild anyway), and the flat model's override sets the flag. This addresses iteration 1's rejection: iteration 1 added `rebuild_sort()` only to `FlatBaseModel`, so a name-format change on the Person Tree view would raise `AttributeError` at runtime.

## Verified against

- `gramps/gui/views/treemodels/basemodel.py:59-71` — `rebuild_sort()` default
- `gramps/gui/views/treemodels/flatbasemodel.py:491-626` — cache initialization and reuse guards
- `gramps/plugins/lib/libpersonview.py:178-202` — signal routing and format-changed handler

(Target branch: `upstream/maintenance/gramps61`)

## Test

**Core regression test** (red→green): `gramps/gui/views/treemodels/test/flatbasemodel_sort_test.py`

Two test classes:

1. **`FlatBaseModelSortRebuildTest`** — drives the production `_rebuild_search()` / `_rebuild_filter()` methods over a real `FlatNodeMap` with a mutable sort-key function (surname vs. given name; the two orders are reverses, so re-sort is unambiguous). Pre-fix, `rebuild_sort()` doesn't exist → `AttributeError` → red; post-fix, rows re-sort to the new format → green.

2. **`TreeModelSortRebuildSafetyTest`** — guards the iteration-1 rejection by asserting `BaseModel` provides `rebuild_sort()` and that `TreeBaseModel.rebuild_sort()` is a harmless no-op (returns `None` without raising). Pre-fix → `AttributeError` on tree format change; post-fix → green.

**Interface regression test** (advisory AT-SPI): `engine/interface/test_bug_9267_name-format-sort.py` — launches the flat People list, captures the display-order Gramps-ID sequence, applies a format change via UI automation, and re-captures. Pre-fix, IDs unchanged → FAIL; post-fix, IDs reordered → PASS.

Fixes #9267
