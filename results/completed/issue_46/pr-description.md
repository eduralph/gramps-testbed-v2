# Let GraphView import when GooCanvas or GraphViz is absent (#46)

## Root cause
`GraphView/graphview.py` raised a bare `Exception` at **module import** when
GooCanvas (`GraphView/graphview.py:111-113`) or the GraphViz `dot` binary
(`GraphView/graphview.py:120-122`) was unavailable, so any direct importer
crashed before Gramps' declared-requirement gate could run. The plugin already
declares those same dependencies at registration (`requires_gi` / `requires_exe`
in `GraphView/graphview.gpr.py:16-17`), which the framework's plugin manager
enforces, so the module-level raises duplicate a gate the framework already owns
while breaking every direct importer — including the addon's own test collection,
which imports the module at top level and aborts with a traceback on a host
lacking `dot`.

## Fix
Remove the two import-time `raise` blocks (`GraphView/graphview.py:111-113` and
`:120-122` on `maintenance/gramps60`). The GooCanvas import-attempt loop
(`GraphView/graphview.py:103-110`) is kept because GooCanvas is used throughout
the view's runtime methods, and `_DOT_FOUND = search_for(...)`
(`GraphView/graphview.py:115-118`) is kept as-is — the minimal edit deletes only
the offending raises. The missing-dependency behaviour for end users is unchanged:
whether the plugin loads stays governed by the registration-level `requires_*`
gate.

## Verified against
- `GraphView/graphview.py:111-113`, `:120-122` (`maintenance/gramps60`) — the two
  module-level raises removed; confirmed both are present unchanged on
  `maintenance/gramps61`, so the forward cherry-pick is correct, not merely
  appliable.
- `GraphView/graphview.gpr.py:16-17` (`maintenance/gramps60`) — the
  `requires_gi=[("GooCanvas","2.0,3.0")]` / `requires_exe=["dot"]` declarations
  that already gate loading remain untouched, so end-user behaviour is unchanged.
- `GraphView/graphview.py:103-110`, `:115-118` (`maintenance/gramps60`) — the
  GooCanvas import loop and `_DOT_FOUND` probe are retained.

## Test
`GraphView/tests/test_graphview_import.py` (new) imports the production
`GraphView.graphview` module — and `from GraphView.graphview import
DotSvgGenerator` — in a fresh child interpreter with `PATH` emptied so
`search_for("dot")` returns 0 (the no-GraphViz condition). The test fails if the
child import raises (non-zero exit): red pre-fix, green post-fix. Its top-level
imports are stdlib-only, so the test collector never executes a GUI import during
collection. Verified red-without-fix / green-with-fix on both the 6.0 and 6.1 legs.

Fixes #46. Forward cherry-pick to `maintenance/gramps61` will be opened as a
separate PR.
