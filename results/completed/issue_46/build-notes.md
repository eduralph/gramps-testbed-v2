# Build notes — issue 46 / graphview-import-raises-on-missing-deps

## Success criterion (the end result I built to)
On the target branch, `import GraphView.graphview` and
`from GraphView.graphview import DotSvgGenerator` complete **without raising** when
GooCanvas / the `dot` binary are absent; the shipped regression test drives that
import with `dot` unavailable (red pre-fix, green post-fix) so `GraphView/tests/`
collects and runs on a host lacking `dot`. End-user missing-dependency behaviour is
unchanged — it stays gated by the registration-level `requires_*`.

## Root cause (verified on target branch)
`GraphView/graphview.py` raised a bare `Exception` at **module import** in two
places on `maintenance/gramps60`:
- `graphview.py:111-113` — `if not _GOO: raise Exception("Goocanvas …")`
- `graphview.py:120-122` — `if not _DOT_FOUND: raise Exception("GraphViz …")`

These fire at top level, so any direct importer crashes before the framework's
declared-requirement gate runs. The `.gpr.py` already declares the same
dependencies (`graphview.gpr.py:16-17`: `requires_gi=[("GooCanvas","2.0,3.0")]`,
`requires_exe=["dot"]`), and Gramps' plugin manager already enforces them
(`gramps/gen/utils/requirements.py:129-133` `Requirements.check_plugin`;
`gramps/gen/plug/_pluginreg.py:1478-1479` `scan_dir` drops a plugin whose check
fails) — so the module is never imported when a requirement is absent. The
module-level `raise` therefore duplicates a gate the framework owns and breaks
every direct importer (including the addon's own test collection).

## Fix — remove the cause (not guard the symptom)
Pure removal of the two import-time `raise` blocks (`graphview.py:111-113` and
`:120-122` on the target branch). This is the smallest change that restores the
brief's **Invariant** ("a module whose deps are declared via `requires_*` must
import without a side-effecting failure when those deps are absent; the
registration gate is the sole arbiter of whether the plugin loads").

- The GooCanvas import-attempt loop (`graphview.py:103-110`) is **kept** — GooCanvas
  is used throughout the view's runtime methods (e.g. `:1077`, `:1656`, the
  `GraphvizSvgParser` at `:1920+`), so the import attempt must still run.
- `_DOT_FOUND = search_for(...)` (`:115-118`) is **kept** as-is. It becomes an
  unused assignment, but leaving it is the minimal edit; rewriting/removing it is
  extra scope the brief does not ask for and the invariant does not require.

### Rejected alternative: relocate the checks into `__init__`/a guard
The brief explicitly names no probe/guard and prefers removing the cause
(principles §3.1/§3.3). A relocated availability check would *re-implement* the
registration gate one layer down — exactly what the invariant forbids — and would
add code (a guarded `raise`/log in the constructor, ~5–8 lines) rather than delete
the 6 offending lines. Cost comparison is moot here anyway: the deciding axis is
the named invariant (smallest change that restores it), not diff size. Removal wins
on both.

## Test — `GraphView/tests/test_graphview_import.py` (new)
Drives the **production** import path in a fresh child interpreter with `dot` made
unfindable (empty `PATH`, so `search_for("dot")` returns 0 —
`gramps/gen/utils/file.py:236-240`). The child runs
`import GraphView.graphview; from GraphView.graphview import DotSvgGenerator`; a
non-zero child exit means the import raised. Pre-fix the child raises at
`graphview.py:121` and exits 1 (red); post-fix it imports cleanly and exits 0
(green). Verified via `run-verify.sh`: `green-with-fix=PASS / red-without-fix=PASS`
on **both** the 6.0 and 6.1 legs — confirming the cherry-pick forward remains
correct, not merely appliable.

## Addressing Iteration 1 carry-forward (the rejection)
The v1 test was rejected because it reimplemented GTK load/version-pinning at the
test-module top level (`import gi` + `gi.require_version("Gtk","3.0")`), which is
already owned by gramps at runtime and by the testbed's `gi_bootstrap`
sitecustomize for unit runs — redundant, and the likely cause of the T3 addon-unit
exit-2 collection aborts (xmlrunner imports the test module to collect it; a
top-level GI call that errors aborts collection → exit 2) and the E2E `setUpClass`
delta.

This rebuild removes that machinery **entirely**. The new test module's top-level
imports are stdlib-only (`os, subprocess, sys, unittest, pathlib`) — no `gi`, no
`gi.require_version`, no `gramps.gui`. The Gtk/GooCanvas-bound production module is
imported only *inside the spawned child process* during test execution, never at
collection time, so xmlrunner can no longer abort while importing this module. GI
version pinning is left to the environment (`gi_bootstrap` sitecustomize, which the
addon-unit runner puts on `PYTHONPATH`; the child inherits it). The production
change (removal of the two raises) is kept as in v1, since it was not the reason for
rejection.

The sibling `test_graphview_dot_handles.py` is unaffected — the addon-unit runner
runs each test module in its own subprocess (`run_addon_modules.py`).

## Notes
- Addon target → no `po/POTFILES.in` registration applies (that MUST is core-only;
  addons-source uses per-addon `po/` + root `addons.pot`). The test has no
  translatable strings regardless.
- New test file is `black`-clean (`black 26.5.0`, `--check` passes). The production
  edit only deletes lines and introduces no formatting violation; addons-source
  ships no `black`/pre-commit config.
- Citations are to `maintenance/gramps60` (addons-source-6.0 worktree @
  `ca98b2ed4`); the same lines are present unchanged on gramps61, and the 6.1 leg
  of C4-verify passes identically.
