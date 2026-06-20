# Guard Addon Manager refresh delivery from closed-window crash

## Root cause

When the Addon Manager refreshes against a project whose listing file is missing
or returns 404, the fetch is both slow (each language's listing times out in turn
after ~10 seconds) and failing (HTTP 404). The refresh runs off the GUI thread via
`GetAddons` thread (gramps/gui/plug/_windows.py:116). If the user closes the
Addon Manager dialog while the refresh is still in flight, the queued result that
arrives later invokes `load_addons` (via `GLib.idle_add`, _windows.py:130-132)
and calls back into the destroyed window, leaving a dangling pointer in the Gtk
draw cycle—crashing Gramps to desktop.

## Fix

Extract `AddonRefreshDispatch` (new gramps/gen/plug/_addonrefresh.py), a
plain-Python liveness gate that marks when the requesting window is torn down and
drops any result that arrives after teardown. Wire the gate into the refresh path:

- gramps/gui/plug/_windows.py:
  - Line 93: import `AddonRefreshDispatch` from the new gate module
  - Line 390: initialize `self._dispatch = None` early in `__init__` so `close()`
    can always cancel a pending refresh
  - Line 556-560: `refresh()` cancels any in-flight previous dispatch, creates a
    fresh one, and hands `dispatch.deliver` (not the bare `self.load_addons`) to
    `GetAddons`
  - Line 563-572: new `close()` override cancels the dispatch before calling
    `ManagedWindow.close()`

Now a result that arrives after the window is destroyed is dropped—`load_addons`
never touches the closed window. A subsequent valid refresh creates a new live
dispatch and populates normally (success criterion: "a subsequent valid refresh
still works").

## Verified against

The headless unit tests (gramps/gen/plug/test/utils_test.py) verify:

- `MissingListingFetchTest::test_missing_listing_returns_empty_without_raising`
  — `get_addons()` against a missing listing returns `[]` without raising (the
  "handled" half of the success criterion; this test is green pre- and post-fix,
  a regression guard on the already-correct fetch path)

- `AddonRefreshDispatchTest::test_live_dispatch_delivers` — a result delivered
  while the dispatch is alive is applied (validates the gate does not block live
  deliveries)

- `AddonRefreshDispatchTest::test_cancelled_dispatch_drops_late_result` — the
  dangling-window guard: a result arriving after `cancel()` is dropped, not
  applied to the destroyed window

- `AddonRefreshDispatchTest::test_subsequent_valid_refresh_still_works` — after a
  cancelled (failed) refresh, a fresh dispatch delivers normally (success
  criterion: the window is not stuck after a failed refresh)

## Test

The extracted gate is plain Python with no GUI imports, so it is driven by
headless unit tests in `gramps/gen/plug/test/utils_test.py` (lines 139-194).
The three `AddonRefreshDispatch` tests form the red→green regression path: with
the production change reverted, `_addonrefresh.py` is gone, so the test module
fails to import—the protective mechanism is absent. The test harness (C4, core
6.1.0) validates: red-without-fix=PASS (import fails, no gate), green-with-fix=PASS
(gate delivers/cancels correctly).

The GUI wiring (refresh creating the dispatch, close cancelling it) lives in
_windows.py and cannot be imported headless, so the unit test does not detect a
revert of only the wiring while the module stays. That last mile—the actual
destroyed-window draw—is reachable only through an AT-SPI interface test, which
is listed as advisory follow-up in gramps-testbed.

Fixes #13174
