# build-notes — issue 9267 (name-format change rebuilds sort)

## Success criterion / invariant

After changing Edit→Preferences→Display→"Name format", the People (flat) list
must re-sort to the new display name **without reopening the database**. Invariant
to restore: a list view's row order is consistent with the display-name format
currently in effect — the same config change that redisplays the rows must also
refresh the sort key.

## Root cause (two sentences)

`FlatBaseModel._rebuild_search` / `_rebuild_filter`
(`gramps/gui/views/treemodels/flatbasemodel.py:608` and `:643` on
maintenance/gramps61) reuse the cached `(sortkey, handle)` map
`node_map.full_srtkey_hndl_map()` whenever it is non-empty, recomputing
`sort_keys()` only when the cache is empty (`if not allkeys:`). That cache is
correct for search/filter rebuilds (which only restrict *which* handles show, not
their order) but is stale when the sort key itself changes — and the People view
wires `nameformat-changed` straight to a plain rebuild
(`gramps/plugins/lib/libpersonview.py:181`), so a format change redrew every row
(the per-handle `SORT_NAME` cache is cleared by `clear_cache()` at the top of the
rebuild) yet left the *ordered* `_fullhndl` list untouched. Reopening the DB
rebuilds the model from scratch (empty cache → `sort_keys()` recomputed), which is
why a reopen "fixes" the order.

Confirmed the sort key really does track the display format: the People model's
`sort_name` calls `name_displayer.raw_sorted_name`
(`gramps/gui/views/treemodels/peoplemodel.py:165`), which for the usual
`sort_as == DEFAULT (0)` resolves through `name_formats[0]`; `set_default_format`
(called by the preferences callback, `configure.py:1490`) rewrites
`name_formats[0]`'s render functions in place on the shared `displayer` singleton.
So after the format change `sort_keys()` yields a *different* order — the only
thing missing was an instruction to recompute it.

## The fix (smallest change that restores the invariant)

1. `FlatBaseModel.rebuild_sort()` — a new method that sets a `self._sort_dirty`
   flag (initialised `False` in `__init__`). `_rebuild_search` / `_rebuild_filter`
   change their cache-reuse guard from `if not allkeys:` to
   `if self._sort_dirty or not allkeys:` and clear the flag after recomputing. This
   keeps the search/filter optimisation intact (the cache is still reused for those
   rebuilds) and only forces a `sort_keys()` recompute when the sort key changed.
2. `BasePersonView` connects `nameformat-changed` / `placeformat-changed` to a new
   `_format_changed` handler that calls `self.model.rebuild_sort()` (guarded by
   `if self.model`) before `self.build_tree()`.

A flag (set outside the rebuild, consumed inside it after `set_model(None)`) was
chosen over clearing `node_map` directly in the view: clearing the node map while
the treeview is still attached to the model would briefly expose an empty, then
repopulating, map to GTK. The flag mutates nothing until the rebuild runs in
`build_tree`'s detached `set_model(None) … set_model(model)` window.

Both name- and place-format signals route through `_format_changed`: the staleness
mechanism is format-agnostic (any sort-key change invalidates the cache) and the
two signals sit on adjacent lines already both calling `build_tree`; fixing only
one would leave an identical, obvious bug in the same two-line block. This is
within the People-view scope and adds no cost beyond the shared handler. (It does
*not* touch other views' columns — out of scope per the brief.)

### Why not the alternatives

- **Force a full `make_model` rebuild on format change** (set `self.dirty = True`
  in the view before `build_tree`). Correct, but heavier: `build_tree`'s dirty
  branch (`listview.py:347-356`) `self.model.destroy()`s and reconstructs the whole
  GTK model + node map every format change, where the surgical recompute reuses the
  existing model object and only re-derives the sort list. More importantly this is
  an *invariant-restoration* task, where the target is the smallest change that
  restores the invariant, not the smallest diff — and "recompute the sort keys" is
  exactly the invariant, so the flag expresses it directly. Diff cost is comparable
  (a 1-line view change either way) but the runtime cost differs: full destroy/
  rebuild of a 2000-row model vs. one `sort_keys()` pass.
- **Drop the `full_srtkey_hndl_map` cache from the view** (`self.model.node_map.
  clear_map()` before `build_tree`). Same end effect but reaches two layers down
  from the view into the node map, and clears the map while the model is still
  attached to the treeview (GTK-visibility window described above). The flag keeps
  the invalidation inside the model's own rebuild.

## Tests

### Core, headless (gated red→green) — `gramps/gui/views/treemodels/test/flatbasemodel_sort_test.py`

Drives the **real** production methods `FlatBaseModel._rebuild_filter` (the People
flat view's default sidebar-filter rebuild path), `_rebuild_search` (top-search-bar
path) and `rebuild_sort` over the **real** `FlatNodeMap`, stubbing only the data
source (`sort_keys` / `db.is_open`) so it runs under the headless C4 runner — no
display, D-Bus or AT-SPI, and no GObject construction (the methods are invoked
unbound on a duck-typed `self`). A mutable `fmt` selecting surname-vs-given as the
sort key models a name-format change; the two orders are reverses, so a re-sort is
unambiguous. The test asserts: (a) initial surname order, (b) a plain rebuild after
the format change reuses the cached order (documents the cache that must be
invalidated), (c) after `rebuild_sort()` the rows re-sort to given order.

This is **not** a hand-copy of production: the production view path is
`view._format_changed → model.rebuild_sort() → build_tree → model.rebuild_data()
(== _rebuild_filter)`, and the test drives the same `rebuild_sort` +
`_rebuild_filter` units. Pre-fix `rebuild_sort` does not exist → step (c) raises
`AttributeError` → red; post-fix → green.

`run-verify.sh` (C4-verify, core, gramps-6.1) result:
`green-with-fix=PASS / red-without-fix=PASS`.

`flatbasemodel.py` imports cleanly headless (it backs `node_test.py` /
`treebasemodel_test.py`, already in the suite); the Gtk-CRITICAL screen warnings in
the run are the usual headless noise and do not affect the test.

### Interface, AT-SPI (advisory) — `engine/interface/test_bug_9267_name-format-sort.py`

Launches directly on the flat People list (`use-last-view` + `last-view:
personlistview`) with `name-format:1` (surname sort), reads the top-to-bottom
sequence of the **format-independent Gramps-ID cells** (`I0001`…), drives
Edit→Preferences→Display→"Name format" to a different format, and re-reads the ID
sequence. A re-sort shows up as a *changed* ID sequence (pre-fix: frozen →
unchanged → FAIL; post-fix: changed → PASS). Using the ID column sidesteps the fact
that the Name column text itself reformats. Every AT-SPI step that the environment
cannot drive (opening Preferences, finding the Display category / the "Name format"
combo) `skipTest`s rather than false-failing, per the established advisory pattern
(cf. bug 13532); the load-bearing proof is the headless unit test.

## Files / housekeeping

- `gramps/gui/views/treemodels/flatbasemodel.py` — `_sort_dirty` flag + `rebuild_sort()` + the two guard edits.
- `gramps/plugins/lib/libpersonview.py` — `_format_changed` handler + signal rewiring.
- `gramps/gui/views/treemodels/test/flatbasemodel_sort_test.py` — new core test; registered in `po/POTFILES.skip` (it has no translatable strings).
- `engine/interface/test_bug_9267_name-format-sort.py` — AT-SPI repro (testbed mount, not in patch.diff).
- `black` (26.5.0) run over all three gramps files: left unchanged (commit-ready for gramps' pre-commit hook).
