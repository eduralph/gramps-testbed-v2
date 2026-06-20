# Fix Dashboard gramplet placement at high column counts

## Root cause

`GrampletPane.drop_widget` (gramps/gui/widgets/grampletpane.py:1351–1356 on
the target branch) computes the destination column for a newly-added gramplet
by dividing the viewport width into N equal slices and testing the drop
position x against them. However, the click position x comes from a right-click
event captured on the event-box wrapping the columns (content coordinates),
which spans all columns together. When the Dashboard is configured with a high
column count, the content is wider than the visible viewport (a horizontal
scrollbar appears), so x is in a larger coordinate space than the viewport width.
The old formula `x < (sx / n) * (i + 1)` scales x up and selects a far-right
column scrolled off screen; when `x >= sx`, the loop never breaks and col
silently falls back to 0. Either way, the new gramplet lands in the wrong
(often off-screen) column.

## Fix

Map the drop x against each column's own allocation bounds (content/event-box
coordinates, the same space as x) instead of dividing the viewport width.

**New helper file** `gramps/gui/grampletlayout.py` (lines 37–67):
pure Python utility with no gi/gramps imports, so it is unit-testable headless.
`column_index_for_x(x, column_bounds)` returns the index whose
`[start, start+width)` interval contains x, clamped to `range(len(column_bounds))`.

**Modified** `gramps/gui/widgets/grampletpane.py`:
- Line 60: import the helper
- Lines 1351–1356 replaced: call `column_index_for_x(x, [(c.get_allocation().x,
  c.get_allocation().width) for c in self.columns])` instead of the viewport
  division loop.

When content fits the viewport (no horizontal scroll — the common low-column
case), per-column allocations equal `sx / len(self.columns)`, so behaviour is
byte-for-byte unchanged; the change only diverges in the broken, scrolled case,
guaranteeing an in-range column.

## Verified against

Target branch: `origin/maintenance/gramps61` (5568a39d1984a77abc753f12d1f8c37238c08f2e).

The fix adds a new gi-free helper function and updates the drop-widget placement
logic to use per-column allocations instead of viewport division. No previously-working
scenario regresses because the new mapping is identical to the old one whenever
content is not horizontally scrolled.

## Test

**New headless test** `gramps/gui/test/grampletlayout_test.py` (lines 114–139):
reproduces the 13865 geometry (20 homogeneous columns at 300px each totalling
6000px content over an 800px viewport; click at content-x 150 below "Top
Surnames") and asserts:
- The drop lands in column 0 (the clicked column, on screen)
- That column's start is within the viewport (not scrolled off)
- For any column count 1..30 and any drop position (left of all, inside, right
  of all), the returned index is always in `range(column_count)` — never an
  off-screen slot

The test imports only the gi-free helper, so it runs under the headless C4
runner (`python3 -m unittest`, no display). The test exercises the real
production decision because `drop_widget` calls the same helper function.
C4-verify: green with fix, red without (ModuleNotFoundError when the helper is
absent — standard extracted-helper red→green).

## Files

**New core files** registered in `po/POTFILES.skip` (no translatable strings):
- `gramps/gui/grampletlayout.py`
- `gramps/gui/test/grampletlayout_test.py`
