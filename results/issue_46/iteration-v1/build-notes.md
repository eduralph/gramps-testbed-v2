# Build notes — issue 46 / graphview-import-raises-on-missing-deps

## What the fix does

Removes the two module-level `raise Exception(...)` guards in
`GraphView/graphview.py` that fired at **import time** when GooCanvas or the
GraphViz `dot` binary were unavailable:

- target branch `maintenance/gramps60`, `GraphView/graphview.py:111-113`
  (`if not _GOO: raise Exception("Goocanvas …")`)
- `GraphView/graphview.py:120-122`
  (`if not _DOT_FOUND: raise Exception("GraphViz …")`)

After the change the module body runs to completion when those deps are
absent; the plugin's load decision is left to the registration-layer gate the
framework already owns (`graphview.gpr.py:16-17` declares
`requires_gi=[("GooCanvas","2.0,3.0")]` and `requires_exe=["dot"]`, enforced by
`gramps/gen/utils/requirements.py:Requirements.check_plugin` and
`gramps/gen/plug/_pluginreg.py:1478-1479` which drops a plugin whose check
fails). This restores the brief's **Invariant**: a module whose external deps
are declared through `requires_*` must import without a side-effecting failure
when those deps are absent; module import must not re-implement that gate as a
hard failure.

## Why this mechanism (remove the cause, not guard the symptom)

The brief names no probe/guard and an explicit **Invariant to restore**, so the
target is "the smallest change that restores the invariant," not the smallest
diff (principles §1.2/§2, §3.1/§3.3). The cause is the two `raise` statements;
removing them *is* the invariant restoration. I kept the surrounding machinery:

- The `for goo_ver …` loop (`graphview.py:103-110`) stays untouched because its
  body performs the real, runtime-needed `from gi.repository import GooCanvas`
  (used at `graphview.py:1077`, `:1656`, `:1887`, and throughout the SVG parser
  ~`:2013-2260`). Only the `if not _GOO: raise` consumer was removed.
- The `_DOT_FOUND = search_for(...)` computation (`:115-118`) stays. It is now
  vestigial (its only consumer was the removed raise), but deleting it is
  cleanup beyond the invariant and would widen the diff. Per "smallest change
  that restores the invariant," I left the two flag computations in place; they
  are side-effect-free and harmless. (Cost of the alternative — also stripping
  the now-dead `_GOO`/`_DOT_FOUND` bookkeeping — would turn a 6-line deletion
  into a ~14-line rewrite of the GooCanvas loop and the win32/else dot block,
  for no behavioural gain and more cherry-pick surface.)

The end-user missing-dependency UX is unchanged (out of scope per the brief):
it remains gated by `requires_gi`/`requires_exe` at registration, so a desktop
user without GooCanvas/`dot` still does not get the view — they just no longer
get an import-time crash in any direct importer.

## The test

`GraphView/tests/test_graphview_import.py` (new; addon `tests/` + `test_*.py`
convention, INTEGRATION §3). It exercises the **production** module
`GraphView.graphview` (not a copy):

- Empties `os.environ["PATH"]` so `gramps.gen.utils.file.search_for("dot")`
  (`gramps/gen/utils/file.py:236-240`) returns 0 → `_DOT_FOUND` falsy → pre-fix
  the `:120` raise fires during import.
- Pops `GraphView.graphview` from `sys.modules` first so the module body
  re-executes under the modified env (the module is imported once per process;
  the sibling `test_graphview_dot_handles.py` may have cached it).
- Asserts the import completes and `DotSvgGenerator` is reachable on the
  imported module, restoring PATH and the original cached module in `finally`.

### Headless-collection safety

The test module's top level imports only stdlib plus `import gi` +
`gi.require_version("Gtk", "3.0")`. That pin is required because
`gramps.gui.*` self-requires Gtk 3.0 at its own import, and without pinning the
default (Gtk 4.0) loads first and collides ("Namespace Gtk is already loaded
with version 4.0"). `import gi` + a version pin loads no widgets and needs no
display — this mirrors `test_graphview_dot_handles.py:34-37`, the established
C4-passing pattern. The Gtk-bound production module is imported **inside the
test method**, never at this test module's load time, so the headless collector
never runs a GUI import during collection.

## Red→green evidence

The C4 docker runner (`engine/scripts/ubuntu/run-verify.sh`) could not be
invoked from the headless builder — it shells into Docker and the sandbox
gated it behind an interactive approval the builder cannot grant. I instead
reproduced **run-verify.sh's exact contract** (run ONLY the shipped test;
GREEN with the fix, RED with the production change reverted and the test kept)
against the same pinned worktree the runner patches
(`/home/eddie/workspace/gramps-6.0` + `/home/eddie/workspace/addons-source-6.0`):

- GREEN (patched module): `Ran 1 test … OK`.
- RED (original module restored via `git show HEAD:GraphView/graphview.py`,
  test kept): `ERROR … raise Exception(… required for this view to work)`.

Note: in this local image GooCanvas itself is absent, so the `:111` GooCanvas
raise is what fires first pre-fix; in the testbed/CI image GooCanvas is present
and the PATH-emptying triggers the `:120` `dot` raise instead. Either declared
dependency being absent produces the same pre-fix import crash and the same
post-fix clean import, so the test proves the invariant under both.

## Cross-version (gramps60 → gramps61)

The brief requires a **separate** forward pick. The two raises and their
surrounding context are byte-identical on `maintenance/gramps61`
(`addons-source-6.1/GraphView/graphview.py:111-122`), and the runtime GooCanvas
usages + `requires_*` gates are the same, so the fix *remains correct* there,
not merely applies. Verified `git apply --check` of `patch.diff` against the
gramps61 worktree: clean for both files.

## Registration / formatting

- No `po/POTFILES.in`/`.skip` exists in `addons-source` (that is a gramps-core
  convention; addons ship per-addon `GraphView/po/*.po`). The sibling test
  `test_graphview_dot_handles.py` is registered nowhere either — so the new
  test needs no POTFILES entry.
- `addons-source` has no `.pre-commit-config.yaml`/`pyproject`/black config, and
  `graphview.py` is not black-formatted (single-quote style). I therefore did
  **not** reformat it (that would be a whole-file rewrite, out of scope); the
  edit matches surrounding style. The new test file passes `black --check`.
