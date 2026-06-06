# Build notes — issue 13636 / uimanager-toolbar-detach-on-close

> Rationale artifact. Withheld from the reviewer by the driver. Cites
> `path:line` on the target branch `maintenance/gramps61` (clean tree).

## Target branch / provenance

- Branch checked out: `gramps` @ `maintenance/gramps61`, tracking
  `upstream/maintenance/gramps61` (`git -C gramps status` → "up to date with
  upstream/maintenance/gramps61"; remotes: `upstream =
  github.com/gramps-project/gramps`). Branched-from base is upstream, not the
  fork's tracking copy, per INTEGRATION §2 (`doc16:115`).
- All line cites below are against that clean checkout.

## Root cause (two sentences)

During a page change, `ViewManager` queues `page_changer` via
`GLib.idle_add(..., priority=GLib.PRIORITY_DEFAULT_IDLE - 10)`
(`gramps/gui/viewmanager.py:1061-1066`), and that callback calls
`UIManager.update_menu()`. If the main window is torn down before the idle
callback fires, the previous toolbar has already been detached, so
`toolbar.get_parent()` returns `None` at `gramps/gui/uimanager.py:258` and the
unguarded `toolbar_parent.remove(toolbar)` at `:260` raises
`AttributeError: 'NoneType' object has no attribute 'remove'`.

This was verified, not recalled: the local pre-fix test run crashes exactly at
`gramps/gui/uimanager.py:260`, in `toolbar_parent.remove(toolbar)`, with that
AttributeError (traceback captured during the red run).

## The fix

`gramps/gui/uimanager.py:257-260` (target branch). After
`toolbar_parent = toolbar.get_parent()` (`:258`), guard for `None` and return
early before `toolbar_parent.remove(toolbar)` (`:260`):

```python
toolbar_parent = toolbar.get_parent()
if toolbar_parent is None:
    # bug 13636 (sibling of bug 12048): ... window torn down before the
    # queued page_changer idle ran; previous toolbar already detached.
    LOG.info("*** Update ui: toolbar already detached, skipping rebuild")
    return
tb_show = toolbar.get_visible()
toolbar_parent.remove(toolbar)
```

- Returns cleanly (no toolbar rebuild) precisely on the shutdown race, matching
  the success criterion: "the toolbar-rebuild path is skipped/handled gracefully
  instead of crashing".
- `LOG` is the module logger already defined at `gramps/gui/uimanager.py:34`; the
  `LOG.info("*** Update ui")` line at the *end* of the normal path
  (`uimanager.py:274`) is the sibling log call, so the style matches.
- Minimal: one guard, no change to the rebuild logic, the `GLib.idle_add` /
  `page_changer` scheduling, or window-teardown ordering — all explicitly out of
  scope per the brief.

### Why guard on `toolbar_parent is None`, not on `toolbar is None`

The brief's success criterion names `toolbar.get_parent()` returning `None` as
the failure condition. In `update_menu(init=False)`, `toolbar` is the *previous*
toolbar captured at `gramps/gui/uimanager.py:224-225` from the old builder; in
the race it is still a live Gtk object (so `toolbar` itself is not `None`) but it
has already been removed from its container, so `get_parent()` is `None`. Guarding
the parent is therefore the exact condition and the smallest change that removes
the crash at `:260`.

## Test — `gramps/gui/tests/uimanager_test.py` (authored fresh)

The live trigger is a timing race not deterministically reproducible through the
interface runner (brief §Repro). Reproduced at the unit layer instead:

- `gi` / `gi.repository` are stubbed in `sys.modules` *before* importing
  `gramps.gui.uimanager`, so `from gi.repository import GLib, Gio, Gtk`
  (`gramps/gui/uimanager.py:29`) needs no GTK typelib and no display. `config`
  (`uimanager.py:32`) and `glocale` (`:31`) are the real modules and import
  headless. `sys.modules.setdefault` is used so a fresh `-m unittest` process
  (where `gi` is not yet imported) deterministically gets the stub, in both the
  local box and the C4 Docker image.
- `_make_manager(parent)` builds a `UIManager` whose previous builder
  (`mgr.builder`) yields a toolbar whose `get_parent()` returns `parent`.
- `test_update_menu_detached_toolbar_does_not_raise` (`parent=None`) is the
  regression: pre-fix it raises `AttributeError` at `uimanager.py:260` and
  `self.fail`s; post-fix `update_menu(init=False)` returns `None`.
- `test_update_menu_attached_toolbar_rebuilds` (`parent=<mock>`) is a sanity
  guard that the non-race path is untouched: the previous toolbar is still
  detached via `parent.remove(prev_toolbar)`, proving the guard only fires on
  `None`.

### Local red→green (run via `unittest` with `gi` stubbed, `GRAMPS_RESOURCES` set)

- Pre-fix: `test_update_menu_detached_toolbar_does_not_raise` FAILS with the
  AttributeError at `uimanager.py:260`; the sanity test passes. → red.
- Post-fix: both tests pass (`Ran 2 tests ... OK`). → green.

This is the `python3 -m unittest gramps.gui.tests.uimanager_test` form the C4
`run-verify.sh` gate computes from the patch's `*_test.py` path
(`gramps/gui/tests/uimanager_test.py` → module `gramps.gui.tests.uimanager_test`).

### No `__init__.py` added

`gramps/gui/tests/` is left as an implicit namespace package; verified it
resolves (`importlib.import_module('gramps.gui.tests')` →
`_NamespacePath([...'/gramps/gui/tests'])`) and that `loadTestsFromName` imports
the test. Adding an `__init__.py` would put a second production file in the patch
that the C4 red check reverts alongside `uimanager.py`, muddying the red signal;
the existing sibling `gramps/gui/test/` (singular) keeps its `__init__.py`, but
the brief names the plural `tests/` path and the namespace import works without
one.

## Ruled out

- **Changing the scheduling / teardown** (`viewmanager.py:1061-1066`, window
  teardown ordering): explicitly out of scope; would be a larger redesign for a
  race the one-line guard already neutralises at the crash site.
- **Guarding by wrapping the whole block in try/except**: broader than needed,
  would swallow unrelated errors in the rebuild path; the precise `None` check
  matches the documented failure condition.
- **Bug 12048**: separate, already fixed (referenced in the `page_changer`
  comment at `viewmanager.py:1057-1060`); out of scope.

## Prior-art

Brief's triage found no existing fix for the None-parent shutdown race on
`upstream/maintenance/gramps61` or `upstream/master`; the unguarded
`toolbar_parent.remove(toolbar)` is still present at `uimanager.py:260` on the
checked-out target branch (confirmed by reading the file). The closed/rejected-PR
search across `gramps-project/*` by path remains the TODO the brief flagged
(needs network) — left for Check/human.

## STOP

Builder scope only: produced `patch.diff`, the named test, and these notes; the
gramps working tree was restored to clean after generating the diff (so the C4
gate can apply `patch.diff`). No push, no PR, no ready-mark.
