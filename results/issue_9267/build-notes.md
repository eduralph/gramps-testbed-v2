# build-notes — issue 9267 (name-format change rebuilds sort) — iteration 2

## Carry-forward addressed (the iteration-1 reject)

Iteration 1 was rejected at sign-off (C3/T3 FAIL): `BasePersonView._format_changed`
calls `self.model.rebuild_sort()`, but `BasePersonView` is shared by **both** the flat
People view and the Person **Tree** view. `PersonTreeModel` inherits `TreeBaseModel`
(`gramps/gui/views/treemodels/peoplemodel.py:592`), not `FlatBaseModel`
(`peoplemodel.py:557`), and iteration 1 added `rebuild_sort()` only to `FlatBaseModel`.
So a name/place-format change while the Person Tree view was active would raise
`AttributeError` at runtime.

Fix in this iteration: define `rebuild_sort()` as a **no-op default on the common base
`BaseModel`** (`gramps/gui/views/treemodels/basemodel.py:31`), which both
`FlatBaseModel` and `TreeBaseModel` inherit, and **override** it on `FlatBaseModel`.
The shared view callback is now safe on any person model. This is *not* the rejected
approach re-submitted — it is the rejected approach made correct for the shared base,
via the cause the reviewer named.

Why a base-class no-op rather than a `hasattr` guard in the view (the other option the
carry-forward floated): the no-op is polymorphic and self-documenting — the method
exists on every list model and means "make your sort order stale", which the tree model
satisfies trivially (see next section). A `hasattr(self.model, "rebuild_sort")` guard in
the view would instead encode "some models can't do this" at the call site, an
LBYL smell that silently no-ops if a future flat model forgets the method. Same line
count either way (one method body); the base-class form restores the invariant uniformly.

## Success criterion / invariant

After changing Edit→Preferences→Display→"Name format", the People (flat) list must
re-sort to the new display name **without reopening the database**. Invariant: a list
view's row order is consistent with the display-name format currently in effect — the
same config change that redisplays the rows must also refresh the sort key.

## Root cause (two sentences)

`FlatBaseModel._rebuild_search` / `_rebuild_filter`
(`gramps/gui/views/treemodels/flatbasemodel.py:582`, `:615` on maintenance/gramps61)
reuse the cached `(sortkey, handle)` map `node_map.full_srtkey_hndl_map()` whenever it
is non-empty, recomputing `sort_keys()` only when the cache is empty (`if not allkeys:`,
`:590` / `:624`). That cache is correct for search/filter rebuilds (which only restrict
*which* handles show, not their order) but is stale when the sort key itself changes —
and the People view wires `nameformat-changed`/`placeformat-changed` straight to a plain
`build_tree` (`gramps/plugins/lib/libpersonview.py:181-182`), so a format change redrew
every row yet left the *ordered* `_fullhndl` list untouched until the DB is reopened.

Confirmed the tree path has **no** equivalent staleness: `TreeBaseModel.rebuild_data`
(`gramps/gui/views/treemodels/treebasemodel.py:499`) calls `self.clear()` and re-adds
every row via `add_row`→`add_node`, recomputing each row's sort key from `sort_func`
each rebuild — so it already re-sorts from scratch on `build_tree`. That is why the
tree model's `rebuild_sort` correctly needs to do nothing.

The format change really does alter the sort key: the preferences callback emits
`nameformat-changed` (`gramps/gui/configure.py:1491`) after rewriting the default name
format in place on the shared `name_displayer` singleton, so `sort_keys()` then yields a
different order — the only thing missing was the instruction to recompute it.

## The fix (smallest change that restores the invariant)

1. `BaseModel.rebuild_sort()` — new no-op default
   (`gramps/gui/views/treemodels/basemodel.py:31`). Documents the contract and makes the
   shared view callback safe for the tree model (which re-sorts on every rebuild).
2. `FlatBaseModel.rebuild_sort()` — override that sets `self._sort_dirty = True`
   (`_sort_dirty` initialised `False` in `__init__`, `flatbasemodel.py:492`). The two
   cache-reuse guards change from `if not allkeys:` to `if self._sort_dirty or not
   allkeys:` and clear the flag after recomputing (`flatbasemodel.py:590`, `:624`). The
   search/filter optimisation is untouched (cache still reused for those rebuilds); only
   a sort-key change forces a `sort_keys()` recompute.
3. `BasePersonView._format_changed` — new handler that calls
   `self.model.rebuild_sort()` (guarded `if self.model:` only for the pre-first-build
   None case) before `self.build_tree()`, wired to both `nameformat-changed` and
   `placeformat-changed` (`gramps/plugins/lib/libpersonview.py:181-198`).

A flag (set outside the rebuild, consumed inside it after `set_model(None)`) was chosen
over clearing `node_map` directly in the view: clearing the node map while the treeview
is still attached would briefly expose an empty map to GTK. The flag mutates nothing
until the rebuild runs in `build_tree`'s detached `set_model(None) … set_model(model)`
window.

Both name- and place-format signals route through `_format_changed`: the staleness
mechanism is format-agnostic (any sort-key change invalidates the cache), the two signals
already sat on adjacent lines both calling `build_tree`, and fixing only one would leave
an identical bug in the same block for the place column. (Scope note: the reviewer's T5
flagged whether broadening from name to name+place is acceptable — this is the human's
sign-off call; routing both is the consistent, zero-extra-risk choice now that
`rebuild_sort` is safe on every model. It does not touch other views' columns.)

### Why not the alternatives (with cost)

- **Force a full `make_model` rebuild on format change** (`self.dirty = True` before
  `build_tree`). Correct, but `build_tree`'s dirty branch (`gramps/gui/views/listview.py`
  ~`:347`) `self.model.destroy()`s and reconstructs the entire GTK model + node map every
  format change. This is an *invariant-restoration* task: the target is the smallest
  change that restores the invariant, and "recompute the sort keys" *is* the invariant,
  which the flag expresses directly. Diff cost is comparable (≈1 view line), but the
  runtime cost differs — a full destroy/rebuild of an N-row model vs. one `sort_keys()`
  pass over the same N rows.
- **Drop the `full_srtkey_hndl_map` cache from the view**
  (`self.model.node_map.clear_map()` before `build_tree`). Same end effect but reaches
  two layers down from the view into the node map and clears the map while the model is
  still attached to the treeview (the GTK-visibility window above). The flag keeps the
  invalidation inside the model's own rebuild.
- **`hasattr` guard in the view instead of a base no-op** — discussed above; same body
  size, worse encapsulation.

## Tests

### Core, headless (gated red→green) — `gramps/gui/views/treemodels/test/flatbasemodel_sort_test.py`

Two test classes:

1. `FlatBaseModelSortRebuildTest` (unchanged from iteration 1, which passed C4) drives
   the **real** production methods `FlatBaseModel._rebuild_filter` (the flat People
   view's default sidebar-filter rebuild), `_rebuild_search` (top-search-bar path) and
   `rebuild_sort` over the **real** `FlatNodeMap`, stubbing only the data source
   (`sort_keys`/`db`) so it runs under the headless C4 runner — no display/D-Bus/AT-SPI,
   no GObject construction (methods invoked unbound on a duck-typed `self`). A mutable
   `fmt` selecting surname-vs-given as the sort key models a name-format change; the two
   orders are reverses, so a re-sort is unambiguous. It is **not** a hand-copy of
   production: the production path is `view._format_changed → model.rebuild_sort() →
   build_tree → model.rebuild_data() (== _rebuild_filter)`, and the test drives the same
   `rebuild_sort` + `_rebuild_filter` units. Pre-fix `rebuild_sort` does not exist →
   `AttributeError` → red; post-fix the rows re-sort → green.

2. `TreeModelSortRebuildSafetyTest` (**new, guards the iteration-1 reject**) asserts
   `BaseModel` provides `rebuild_sort` and that `TreeBaseModel.rebuild_sort(object())`
   returns `None` without raising — i.e. the shared person-view callback cannot raise
   `AttributeError` on a Person Tree format change. Pre-fix (`basemodel.py` reverted)
   `BaseModel` has no `rebuild_sort` → `hasattr` is False and the `TreeBaseModel` call
   raises `AttributeError` → red; post-fix → green. This imports `TreeBaseModel`, which
   the sibling `treebasemodel_test.py` already imports in the gramps suite, so it is
   headless-safe in the docker C4 environment.

### Verification status — C4 docker gate could not be executed in this builder session

The authoritative C4 runner (`engine/scripts/ubuntu/run-verify.sh`, which runs the test
in the pinned `gramps-testbed:ubuntu-6.1` docker image) is **approval-gated for docker in
this session** and could not be invoked. What I verified instead:

- `git apply --check` of `patch.diff` against a **clean** `gramps-6.1-lane0` worktree
  (the shared `gramps-6.1` worktree is contended — it currently carries unrelated
  in-flight changes from other bundles, e.g. bug 12110 editname/callname and several
  view files; I left those untouched and verified/cleaned only my own files): applies
  cleanly, all five hunks.
- The host cannot run the suite directly: its system Gtk is newer than gramps 6.1 expects
  (`Gtk.IconSize.MENU` AttributeError when importing `gramps.gui.widgets`), which is
  precisely why the docker image is mandatory — a host run would be a false negative.
- The flat re-sort test class is byte-for-byte the iteration-1 test that **passed C4**
  (`iteration-v1` recorded green-with-fix=PASS / red-without-fix=PASS); the only test
  delta this iteration is the additive `TreeModelSortRebuildSafetyTest`, whose import
  (`TreeBaseModel`) is shared with an existing in-suite test.

Red→green reasoning for the C4 red leg (reverts `basemodel.py`, `flatbasemodel.py`,
`libpersonview.py`; keeps the test): flat tests raise `AttributeError` on the missing
`FlatBaseModel.rebuild_sort`; the tree-safety tests fail on the missing
`BaseModel.rebuild_sort`. Green leg: all four tests pass. **The driver's Check beat will
re-run C4 in docker as the binding gate.**

### Interface, AT-SPI (advisory) — `engine/interface/test_bug_9267_name-format-sort.py`

Unchanged from iteration 1 (the fix's observable behaviour is identical). Launches on the
flat People list (`use-last-view` + `last-view: personlistview`, `name-format:1`), reads
the top-to-bottom sequence of the format-independent Gramps-ID cells, drives
Edit→Preferences→Display→"Name format" to a different format, and re-reads. A re-sort
shows up as a changed ID sequence (pre-fix frozen → FAIL; post-fix changed → PASS). Steps
the AT-SPI environment cannot drive `skipTest` rather than false-fail; the load-bearing
proof is the headless unit test.

## Files / housekeeping

- `gramps/gui/views/treemodels/basemodel.py` — `rebuild_sort()` no-op default.
- `gramps/gui/views/treemodels/flatbasemodel.py` — `_sort_dirty` flag + `rebuild_sort()`
  override + the two cache-reuse guard edits.
- `gramps/plugins/lib/libpersonview.py` — `_format_changed` handler + signal rewiring.
- `gramps/gui/views/treemodels/test/flatbasemodel_sort_test.py` — new core test;
  registered in `po/POTFILES.skip` (no translatable strings).
- `engine/interface/test_bug_9267_name-format-sort.py` — AT-SPI repro (testbed mount, not
  in patch.diff).
- `black` (26.5.0) run over all four changed gramps files: left unchanged
  (commit-ready for gramps' pre-commit hook).
