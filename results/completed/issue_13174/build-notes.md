# Build notes — issue 13174 / addon-manager-refresh-missing-listing-crash

## VERIFY-FIRST outcome

The brief flags this POSSIBLY-FIXED and demands I confirm the defect still
reproduces on `maintenance/gramps61` before fixing. I split the reported
behaviour into its two halves and checked each empirically against a clean
`upstream/maintenance/gramps61` checkout (b679c084f6):

1. **The 404 fetch itself — already graceful.** I ran `get_addons()` against a
   `file://` URL with no `listings/` dir and against the real reported URL
   (`…/isotammi-addons/master/addons/gramps51`, a live HTTP 404). Both return
   `[]` without raising — `gramps/gen/plug/utils.py:217` catches every per-lang
   `urlopen` failure (`utils.py:231-241`) and the `if fptr and …` guards
   (`utils.py:242,246`) keep a missing listing from reaching `json.load`. So the
   not-found is *already* surfaced as a handled condition. A test asserting only
   "get_addons handles 404 without exception" would be **green pre-fix** — it
   cannot drive the red→green C4 mechanic, and it does not touch the actual
   crash.

2. **The crash — the dangling window pointer — still latent.** jralls' note 6
   diagnosed "a dangling window pointer passed to the Gtk draw cycle when the
   refresh fails." The refresh runs off the GUI thread:
   `AddonManager.refresh()` (`gramps/gui/plug/_windows.py:537` on target) starts
   a `GetAddons` thread (`_windows.py:116`) whose `run()` calls
   `get_all_addons()` then `GLib.idle_add(self.emit_signal)`
   (`_windows.py:130-132`); `emit_signal` calls back into
   `AddonManager.load_addons`, which does `self.lb.add(AddonRow(…, self.window))`
   (`_windows.py:606-611`). A **missing listing makes that fetch slow** (each
   `addons-<lang>.json` 404s after the 10 s `urlopen` timeout — `utils.py:208`,
   over many languages × two tries). If the user closes the Addon Manager during
   that window, `ManagedWindow.close()` destroys the dialog
   (`managedwindow.py:603-604` → `close_track` → `close_item` →
   `item.get_window().destroy()`, `managedwindow.py:210-218`), and the
   still-queued `idle_add` later fires `load_addons`, calling `self.lb.add(...)`
   on a **destroyed** `Gtk.ListBox`/window → dangling pointer in the draw cycle →
   crash to desktop. There is **no guard**: the bound `self.load_addons` callback
   is invoked unconditionally. This matches "not a Mac-specific problem" and the
   intermittent reproduction (it needs a close mid-refresh).

So the defect category in the **Invariant to restore** ("a failed refresh must
not crash the process or leave a dangling window pointer … the refresh path
tears down cleanly on failure") is still live on `gramps61`. This is a
likely-fix, not a can't-reproduce close.

## The fix

Restore the invariant with the **smallest change that makes the refresh teardown
clean**: gate the deferred delivery of a refresh result on window liveness, and
cancel the gate when the window closes.

- New import-light module `gramps/gen/plug/_addonrefresh.py` —
  `AddonRefreshDispatch`: holds the delivery callback + an `alive` flag;
  `cancel()` flips it off; `deliver(addon_list)` applies the result **iff** still
  alive, else drops it and returns `False`. No `gi`/`gramps.gui` import.
- `gramps/gui/plug/_windows.py`:
  - import the gate (`_windows.py:93`);
  - `self._dispatch = None` set first in `__init__` so `close()` can always
    cancel (`_windows.py:390`);
  - `refresh()` cancels any in-flight previous dispatch, creates a fresh one, and
    hands `dispatch.deliver` (not the bare `self.load_addons`) to `GetAddons`
    (`_windows.py:556-560`);
  - new `close()` override cancels the dispatch before
    `ManagedWindow.close()` (`_windows.py:563-572`).

Now a result that arrives after teardown is dropped — `load_addons` never touches
the destroyed window. A subsequent valid refresh creates a new live dispatch and
populates normally (success-criterion "a subsequent valid refresh still works").

## Why an extracted module rather than a one-line guard

The minimal *behavioural* fix is a single inline guard in `load_addons`
(`if not self.opened: return` — `opened` is the ManagedWindow liveness flag,
`managedwindow.py:588,600`). I rejected that as the *shipped* shape **purely on
verifiability**, not on behaviour:

- Inline guard: **1 line**, but it lives inside a `gramps.gui`-bound method.
  C4 is headless — importing `_windows.py` pulls in `gi`/Gtk and core-dumps the
  runner — so the guard could only be exercised via the interface runner, i.e.
  the fix would ship **PDCA-UNVERIFIABLE** with no red→green regression test.
- Extracted gate: **+89 lines** (new module) **+6 lines** wiring in
  `_windows.py`. The gate is plain Python, so the *same code production routes
  through* is driven directly by a headless unit test — red→green provable. Per
  the builder rule ("restructure so production and the test share one
  implementation … add a callback seam … rather than re-implementing it in a
  parallel headless copy"), this is the right trade: production's `refresh()`
  calls `AddonRefreshDispatch(...).deliver`, and the test drives that exact
  class — not a copy.

## Test

`gramps/gen/plug/test/utils_test.py` (new, GUI-import-free):

- `MissingListingFetchTest` — `get_addons` against a `file://` missing listing
  returns `[]` without raising (the "handled" half of the success criterion;
  green pre- and post-fix — a regression guard on the already-correct path).
- `AddonRefreshDispatchTest` — the red→green driver:
  - `test_live_dispatch_delivers` — open window applies the result;
  - `test_cancelled_dispatch_drops_late_result` — the dangling-window guard: a
    result arriving after `cancel()` (window closed mid-refresh) is dropped, not
    applied;
  - `test_subsequent_valid_refresh_still_works` — a fresh dispatch after a
    cancelled (failed) one delivers normally.

C4 (`run-verify.sh`, core 6.1.0): **green-with-fix=PASS / red-without-fix=PASS**.
Red leg: with the production change reverted, `_addonrefresh.py` is gone, so the
gate the production path depends on does not exist and the test module fails to
import — i.e. the protective mechanism is absent.

## Residual gap (honest)

The headless test proves the **gate logic**. The GUI **wiring** (refresh creating
the dispatch, close cancelling it) lives in `_windows.py` and cannot be imported
headless, so the unit test does not detect a revert of *only* the wiring while the
module stays. That last mile — the actual destroyed-window draw — is reachable
only through an AT-SPI interface test (`tests/interface/…`), which the brief lists
as advisory. Recommend adding that interface test in gramps-testbed as follow-up;
it is out of scope for the C4 core gate.

## Bookkeeping

- New core `.py` files registered in `po/POTFILES.skip` (no translatable
  strings): `gramps/gen/plug/_addonrefresh.py` and the test
  `gramps/gen/plug/test/utils_test.py` (doc 16 §Adding and removing Python
  files).
- `black 26.5.0` clean on all three touched `.py` files (commit-ready for the
  target's pre-commit hook).
- Out of scope per brief: locale-fallback (13906), listing format / make.py, the
  expected 404 warning itself.
