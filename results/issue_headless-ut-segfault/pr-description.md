# Fix headless crash: don't build a Gtk widget at import in LinkTag

`Fixes #0000` is a stand-in — no Mantis bug is filed yet; it will be replaced
before this is marked ready.

## Root cause

The body of `class LinkTag(Gtk.TextTag)` in `gramps/gui/widgets/grampletpane.py`
computes the theme link colour **at import time**: it constructs a `Gtk.Label` and
reads its style context (`grampletpane.py:221-222`). With no display Gtk escalates
"Can't create a GtkStyleContext without a display connection" into a fatal
`Gtk-ERROR`, which raises `SIGTRAP` and aborts the process. Any headless import of
this module — directly, or transitively (`gramps.plugins.lib.libpersonview` →
`gramps/gui/views/listview.py` → `pageview.py` → `grampletbar.py` →
`grampletpane.py`) — therefore kills the interpreter; under
`python3 -m unittest discover` it takes down the whole core unit suite during
discovery.

## Fix

A `LinkTag` is only ever constructed while rendering links — i.e. always with a
display — so compute the colour **lazily on first construction** (cached on the
class) instead of in the class body. Importing the module then builds no widget, so
it is safe headless; with a display the behaviour is unchanged (the colour is still
computed once and reused). No display probe is introduced — the work that needs a
display simply no longer runs at import time.

## Verified against

- `gramps/gui/widgets/grampletpane.py:221-222` (maintenance/gramps61) — the
  class-body `Gtk.Label` + `get_link_color(get_style_context())` that aborts on
  headless import; moved into `__init__`, computed once on first use.
- `gramps/gui/widgets/grampletpane.py:555,627` (maintenance/gramps61) — the only
  `LinkTag(...)` call sites, both on link-rendering paths that run under a display,
  so deferring the computation changes nothing user-visible.
- Headless red→green: with the change reverted, importing the module in a
  display-less subprocess dies on `SIGTRAP`; with it, the import — and the whole
  `python3 -m unittest discover` run — completes.

## Test

New `gramps/gui/test/headless_import_test.py`: it spawns a child
`python3 -c "import …"` with `DISPLAY`/`WAYLAND_DISPLAY` stripped and asserts the
child exits `0`, for both the faulting module (`gramps.gui.widgets.grampletpane`)
and the transitive chain the suite hit (`gramps.plugins.lib.libpersonview`). A
`SIGTRAP` abort cannot be caught in-process, so the test uses a subprocess; red
pre-fix (returncode -5 / 133), green post-fix. The test module imports no
`gi`/`gramps.gui` symbol itself, so it runs under a plain headless
`python3 -m unittest`.

---
Unrelated to draft PR #2354, which addresses a different headless-import frame
(`PersistentTreeView` subclassing in `widgets/__init__.py`); this change is confined
to `LinkTag` and does not touch `widgets/__init__.py`.

Fixes #0000
