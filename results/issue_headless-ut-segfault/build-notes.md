# Build notes — headless-unit-discovery-segfault

> Withheld from the reviewer. Rationale, isolation evidence, and the premise
> correction for the human at sign-off.

## TL;DR

- **Captured faulting frame** (Step 0): `gramps/gui/widgets/grampletpane.py:221-222`,
  the body of `class LinkTag(Gtk.TextTag)` — executed at *import* time — does
  `Gtk.Label(label="test")` then `get_link_color(linkcolor.get_style_context())`.
  With no display, Gtk turns this into a fatal `Gtk-ERROR: Can't create a
  GtkStyleContext without a display connection`, which raises **SIGTRAP** (exit
  133, `Trace/breakpoint trap (core dumped)`). The crash is in the **class body**
  (`grampletpane.py:214 <module>` → `:221 LinkTag` → `gi/overrides/__init__.py:313
  new_init`), so it fires the instant the module is imported.
- **Fix:** guard that one-time probe with `has_display()` (the existing
  `gramps.gen.constfunc.has_display`, a real `Gtk.init_check()`/`Gdk.Display`
  probe). With a display: identical behaviour. Without: `linkcolor = None` and
  `__init__` skips the foreground `set_property`. `grampletpane.py:48,219-235`.
- **Regression test:** `gramps/gui/test/headless_import_test.py` — spawns a child
  `python3 -c "import …"` with `DISPLAY`/`WAYLAND_DISPLAY` stripped and asserts
  `returncode == 0`. Imports the precise faulting module
  (`gramps.gui.widgets.grampletpane`) **and** the transitive chain the suite hit
  (`gramps.plugins.lib.libpersonview`). The test module imports no `gi`/`gramps.gui`
  symbol itself, so it loads under a plain headless `python3 -m unittest`.

## IMPORTANT — premise correction (read before sign-off)

The brief states the segfault is hit during discovery **on an unmodified
`maintenance/gramps61` checkout**, and asks Do to *confirm it is the unmodified
tree, not uncommitted testbed test artifacts*. **I ran that confirmation and it
falsifies that half of the premise:**

- With the working tree's **untracked testbed artifacts stashed** (an unmodified
  `maintenance/gramps61`), `python3 -m unittest discover -p "*_test.py"` ran
  **32577 tests in 221s with NO `Gtk-ERROR` and NO `Trace/breakpoint trap`**
  (exit 1, from 7 pre-existing unrelated failures only). Evidence:
  `iso_clean.log` in this bundle.
- With the artifacts **present**, discovery aborts (133). Evidence: `iso_v2.log`.
- Per-module import scan (`iso_scan.log`): every *tracked* `*_test.py` imports
  cleanly (rc 0). The first module that aborts is the untracked artifact
  `gramps/plugins/lib/test/libpersonview_test.py`, which does
  `from gramps.plugins.lib.libpersonview import BasePersonView` — and *that*
  import chain (`libpersonview → gui.views.listview → pageview →
  widgets.grampletbar → widgets.grampletpane`) hits the `LinkTag` class body.

So the trigger in the failing run is a **testbed artifact** (left over from prior
cycles: `gramps/plugins/{lib/test,test,tool/test}/…`), not a tracked upstream
test. **However**, the underlying defect it exposes *is* a genuine core
headless-safety bug: a production GUI module (`grampletpane`) aborts the
interpreter merely on import when no display is present. That is squarely
inside core gramps and minimally fixable, so per the brief's disposition hint
("likely-fix … unless the cause is materially different / outside core gramps")
I fixed it rather than iterating to Plan:

- It satisfies the success criterion's part 1 — with the fix, the artifacts (and
  any future headless importer of these modules) import cleanly, so
  `run-unit.sh` no longer emits `Trace/breakpoint trap`.
- It satisfies part 2 — the named subprocess regression test reproduces the
  crashing import chain and exits 0 post-fix.
- It is forward-mergeable to `master` and is the correct upstream fix regardless
  of the testbed cruft.

**Flagged for the human:** the `engine/baselines/run-unit.json`
`run_level_signatures` entry attributes the segfault to "the unmodified tree";
that attribution is inaccurate (it is the artifacts triggering a real core bug).
Two follow-ups for the human/Act, neither in this Do's scope:
1. After this fix lands, drop the core-dump signature from
   `engine/baselines/run-unit.json` and re-promote `T3-unit` to gating (brief's
   own closing instruction).
2. Consider whether the leftover testbed artifacts under
   `gramps/plugins/{lib/test,test,tool/test}/` should be cleaned up / relocated to
   the interface suite — several were authored "to run under the display/D-Bus/
   AT-SPI engine runner" (see their own docstrings) yet sit where `run-unit.sh`
   discovers them headless.

## Isolation method (Step 0)

`faulthandler` does **not** trap SIGTRAP by default, and a `Gtk-ERROR` aborts via
`G_BREAKPOINT()` → SIGTRAP (hence 133, not 134), so a bare `-X faulthandler` run
gave no Python frame. I:
1. Reproduced the abort with the full `python3 -m unittest discover` run (133).
2. Confirmed individual `import gramps.gui.*` of the tracked test deps do **not**
   abort (only a non-fatal `Gtk-CRITICAL` icon-theme warning).
3. Scanned every `*_test.py` by importing each in a fresh process → first abort
   is the untracked `libpersonview_test`.
4. Stashed the untracked artifacts → full discovery is clean (32577 tests).
5. Imported `gramps.plugins.lib.libpersonview` in a child with
   `faulthandler.register(signal.SIGTRAP, chain=False)` to force the Python
   traceback — pinned `grampletpane.py:221 LinkTag` (class body) → `new_init`.

## Why this fix, and alternatives ruled out

- **`has_display()` guard on the class-body probe** (chosen): minimal, reuses the
  existing helper (brief forbids adding a new `has_gtk_display()`), zero behaviour
  change with a display, and fixes the exact faulting frame. The companion
  `if self.linkcolor is not None` guard in `__init__` is a no-op when a display is
  present (the colour is always a hex string then) and only protects the
  never-painting headless path.
- **Lazy/cached property** (compute on first use): also viable but larger; changes
  the attribute from a class constant to a descriptor/`@classmethod`, touching
  every `self.linkcolor` reader. Heavier than warranted for an import-safety fix.
- **PR #2354's blanket `widgets/__init__.py` `else: __all__ = []`** (and the
  falsified persistenttreeview-subclass theory): explicitly out of scope; breaks
  ~30 importers and does not address this frame. Not adopted. The faulting frame
  here is NOT persistenttreeview subclassing — it is a class-body *instantiation*
  in grampletpane, a different module/line than #2354 targets, so #2354 is not
  even the same bug.
- **Removing the testbed artifacts** (would also green `run-unit.sh`): not a core
  fix, not forward-mergeable, and leaves the real headless-import abort latent.
  Surfaced as a follow-up for the human instead.

## Citations (target branch `maintenance/gramps61`, commit d6a61b942f)

- Faulting frame: `gramps/gui/widgets/grampletpane.py:221-222` (pre-fix).
- Fix: `gramps/gui/widgets/grampletpane.py:48` (import `has_display`),
  `:219-235` (guarded class body + `__init__`).
- Helper reused: `gramps/gen/constfunc.py:106` (`has_display`), already imported
  by `gramps/gui/utils.py:61`.
- Crash chain entry from the artifact:
  `gramps/plugins/lib/libpersonview.py:49` → `gramps/gui/views/listview.py:58`
  → `gramps/gui/views/pageview.py:54` → `gramps/gui/widgets/grampletbar.py:67`
  → `gramps/gui/widgets/grampletpane.py:214`.
