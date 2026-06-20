# Build notes — issue 13865 (dashboard gramplet off-screen at high column count)

## Root cause (two sentences)

`GrampletPane.drop_widget` picks the destination column by dividing the
**viewport** width (`sx = source.get_allocation().width`, the visible
`Gtk.ScrolledWindow` area) into N equal slices and testing the drop `x` against
them — but for the right-click "Add a gramplet" path `x` is `event.x` captured
on `self.eventb` (the event-box that wraps the column `hbox`), i.e. it is in
**content** coordinates that span all the columns. With a high column count the
homogeneous content `hbox` is wider than the viewport (a horizontal scrollbar
appears), so `x` is in a larger coordinate space than `sx`: the formula
`x < (sx / n) * (i + 1)` scales `x` up and selects a far-right column whose real
allocation is scrolled off screen — and when `x >= sx` the loop never breaks and
`col` silently falls back to `0`. Either way the new gramplet lands in the wrong
(often off-screen) column with empty columns showing as "blank space".

## The defect is in grampletpane.py, not grampletbar.py

The brief names `gramps/gui/widgets/grampletbar.py`, but the Dashboard's
"Number of Columns" layout is `GrampletPane` in
`gramps/gui/widgets/grampletpane.py` — `gramps/plugins/view/dashboardview.py:53`
states "Popup in GrampletPane", and the column code (`self.columns`,
`column_count`, `set_columns`, `drop_widget`) all lives in `grampletpane.py`.
`grampletbar.py` is the notebook-tab sidebar/bottombar bar, which has no
multi-column layout. I fixed the file that actually carries the bug.

## Fix

Map the drop `x` against **each column's own allocation** (content/event-box
coordinates, the same space as `x`) instead of against an even division of the
viewport width.

- New gi-free helper `gramps/gui/grampletlayout.py:30` —
  `column_index_for_x(x, column_bounds)` returns the index whose
  `[start, start+width)` interval contains `x`, clamped into
  `range(len(column_bounds))` (left of all → first, right of all → last, empty →
  0). Pure arithmetic, imports nothing from `gi`/`gramps.gui`, so it is unit
  tested headlessly.
- `gramps/gui/widgets/grampletpane.py:60` imports it; `drop_widget`
  (`gramps/gui/widgets/grampletpane.py:1351` area) now calls
  `column_index_for_x(x, [(c.get_allocation().x, c.get_allocation().width) for c
  in self.columns])` in place of the old viewport-division loop.

This restores the invariant for **any** configured column count: the gramplet
lands in the column actually under the cursor (visible, in range), not a
scrolled-off slot. When the content fits the viewport (no horizontal scroll —
the common low-column case) the per-column allocations equal `sx / n`, so
behaviour is byte-for-byte unchanged; the change only diverges in the broken,
scrolled case, so no previously-working scenario regresses.

## Why not the column cap (the rejected alternative — and 13864)

The conflicting bundle 13864 (`fix/bug-13864-dashboard-column-cap`) caps columns
at `MAX_GRAMPLET_COLUMNS = 10` via a new `clamp_column_count`. That is a
**different symptom** (13864 is a crash/lock) and a product-level max-column
policy, which this brief puts explicitly out of scope ("any Gramplet-Layout UX
redesign or max-column policy"). A cap would not satisfy 13865's success
criterion either: the criterion demands a valid, visible placement *"for any
column count the control accepts"* — capping just narrows the accepted range, it
does not fix the placement arithmetic, so a gramplet added at the cap (10
columns, still wider than a narrow window) could still be mis-placed. The two
fixes are independent and touch the same file (`grampletpane.py`) but different
methods (`set_columns`/`__init__`/config vs `drop_widget`); they must not be
co-scheduled in one wave but do not share a root cause.

## Scope held deliberately tight

- I left the RTL flip (`x = sx - x`) and the drag-and-drop entry to
  `drop_widget` untouched. DnD delivers `x` in viewport coordinates (a separate,
  pre-existing space question) and the reported defect is the right-click "Add a
  gramplet" path (content coordinates via `_popup_xy`). Because the new mapping
  is identical to the old one whenever the content is not horizontally scrolled,
  DnD in every previously-working case is unchanged; only the already-broken
  scrolled case differs, and there the clamp still guarantees an in-range column.
  Widening the fix to re-derive DnD/RTL scroll offsets would be the redesign the
  brief excludes.

## Test

`gramps/gui/test/grampletlayout_test.py` (core `test/` singular, `*_test.py`
suffix per INTEGRATION §3) imports only the gi-free helper — the same function
`drop_widget` routes through — so it runs under the headless C4 runner
(`python3 -m unittest`, no display). It reproduces the 13865 geometry (20
columns, 6000px content over an 800px viewport, click at content-x 150 → must
return column 0, on screen), documents the old viewport-division picking an
off-screen column, and asserts the in-range invariant across column counts 1..30
and arbitrary drop positions.

C4-verify: **green with fix, red without** (red = `ModuleNotFoundError` when the
production helper is removed — the standard extracted-helper red→green here,
matching 13864's `grampletconfig_test`). The test exercises the real production
decision because `drop_widget` calls the same helper.

## File registration

Both new core `.py` files are registered in `po/POTFILES.skip` (no translatable
strings): `gramps/gui/grampletlayout.py` and
`gramps/gui/test/grampletlayout_test.py` (doc 16 §Adding and removing Python
files).

## Commit-readiness

`black` (target's pre-commit formatter) run over all touched `.py` files —
`grampletlayout.py` and `grampletpane.py` unchanged, the test reformatted and
saved.
