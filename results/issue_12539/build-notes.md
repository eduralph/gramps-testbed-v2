# Build notes — issue 12539 / families-children-tab-refresh

## Success criterion (from brief)

> After a filter/Find changes the Families list and the active family, the
> Children tab shows the currently-selected family's children without a manual
> re-selection.

Invariant to restore: the detail tabs track the view's current selection;
when the active row changes (including programmatically after a filter), the
embedded Children tab is rebuilt for the new selection.

## Root cause (two sentences)

The bottombar `FamilyChildren` gramplet rebuilds **only** on the Family
`active-changed` signal (`gramps/plugins/gramplet/children.py:229`,
`connect_signal("Family", self.update)`). A filter/Find runs
`FamilyView.build_tree` → `ListView.build_tree` → `goto_active`
(`gramps/gui/views/listview.py:375`); when the previously-active family is
filtered out, `goto_handle` cannot select it and only unselects
(`listview.py:485-487`), so the active family handle never changes,
`active-changed` never fires, and the Children tab is left showing the now-hidden
family until a manual re-click.

This matches the tracker diagnosis: snoiraud (~0065528) — *"we need to deselect
the active row when we click Search"* — and prculley (~0065526) — the bottom
gramplets aren't told to update.

## The fix

`FamilyView.build_tree` is overridden (`gramps/plugins/view/familyview.py`) to,
after the base rebuild, re-point the active family at the **first visible row**
when the previously active family was filtered out. Re-pointing is done with the
existing `change_active(handle)` (`navigationview.py:206`), which pushes the new
handle and fires `active-changed` — the exact signal the Children gramplet
listens to — so the tab rebuilds for the now-current, visible family.

The post-rebuild decision is a pure function,
`resolve_active_after_filter(active_handle, visible_handles)`, extracted into a
new **gi-free** module `gramps/plugins/view/familyview_selection.py`. Rules:

- no active family → `None` (never auto-select on a plain build / startup — this
  preserves today's "nothing selected at startup" behaviour);
- active still visible → keep it (no spurious `active-changed`);
- active filtered out, list non-empty → first visible (the 12539 fix);
- active filtered out, nothing visible → `None`.

`build_tree` builds `visible_handles` from the live model and **routes through**
that helper (it is not a copy) — production and the unit test call the same
function, so they cannot drift (principles §3.4 / the issue-8653 mirror trap).

### Why this scope (not `listview.build_tree`)

The brief scopes the fix to the Families view and rules People/other views out
of scope. Both filter entry points for the Families view land in
`FamilyView.build_tree`: the sidebar Family Filter gramplet calls
`self.gui.view.build_tree()` directly (`gramps/plugins/gramplet/filter.py:76-77`)
and the quick SearchBar calls `search_build_tree` → `build_tree`
(`gramps/gui/views/listview.py:404-405`). Overriding `build_tree` on `FamilyView`
therefore covers **both** the brief's repro (sidebar "Father = Simpson", Find)
and the quick filter, while leaving every other list view untouched. A change in
the shared `ListView.build_tree` would have been the smaller diff but would alter
People/Events/Sources/… selection behaviour — explicitly out of scope — so it was
rejected on correctness, not size.

Overriding `search_build_tree` alone was rejected: it would miss the sidebar
Filter gramplet path, which is *the* path in the brief's repro.

## Files

- `gramps/plugins/view/familyview.py` — import + `build_tree` override +
  `_visible_handles` helper (uses the same `for row in model` idiom as the
  existing `write_tabbed_file`, `listview.py:1326`, with the public
  `get_handle_from_iter`).
- `gramps/plugins/view/familyview_selection.py` — **new**, gi-free helper.
- `gramps/plugins/view/test/__init__.py` — **new**, test package.
- `gramps/plugins/view/test/familyview_selection_test.py` — **new**, headless
  red→green unit.
- `po/POTFILES.skip` — registers the three new `.py` files (no translatable
  strings; doc 16 §Adding and removing Python files).

## Tests

### Core unit (headless, gated red→green) — `familyview_selection_test.py`

Drives `resolve_active_after_filter` directly. Covers the 12539 scenario
(active filtered out → first visible, asserting it does **not** stay on the
hidden family), active-still-visible, no-active-no-autoselect, and the
empty-list cases.

Verified locally with the exact module path the C4 runner uses
(`gramps.plugins.view.test.familyview_selection_test`) from a clean
`gramps-6.1-lane0` worktree at the target tip:

- GREEN with the patch applied — 5/5 pass.
- RED with the production change reverted (helper module removed, test kept) —
  `ModuleNotFoundError: gramps.plugins.view.familyview_selection`.

The engine `run-verify.sh` (the C4 gate, headless `python3 -m unittest`) was
**not** runnable in this Do session because spawning its Docker container
required an interactive approval the builder can't grant; the local run above
mirrors its red/green mechanic exactly for this gi-free unit (no display/D-Bus
needed). Check re-runs the real gate.

Note on the red: because the production change includes the *new* helper module,
the unit's red is an import failure when that module is reverted — the standard
new-module pattern. The unit proves the **decision logic** is correct and
present; the GUI wiring (`build_tree` building the handle list and calling
`change_active`) is exercised by the AT-SPI repro below and is the reviewer's
confirmation point.

### Interface (AT-SPI, advisory) — `engine/interface/test_bug_12539_families-children-refresh.py`

Opens the Families view, shows the Children tab, finds two families A/B with
distinct non-empty children, selects A, then drives the sidebar Family Filter on
B's father token so A is filtered out, and asserts the Children tab refreshes to
B's children with no manual re-click. Graceful skips throughout (advisory tier).
Identifies the Children gramplet's table unambiguously by its "Child" column
header vs. the family list's "Father" header.

## Commit-readiness

`black` (gramps' pre-commit formatter) reports all four changed/new `.py` files
already compliant (`black --check`, "4 files would be left unchanged").

## Citations (target branch maintenance/gramps61 @ cbe5699b2e)

- `gramps/plugins/gramplet/children.py:229` — Children gramplet updates only on
  Family active-changed.
- `gramps/gui/views/listview.py:375,404-405,485-487` — build_tree/goto_active and
  the unselect-on-missing-active path.
- `gramps/plugins/gramplet/filter.py:76-77` — sidebar filter calls build_tree.
- `gramps/gui/views/navigationview.py:206-212` — change_active pushes + fires
  active-changed.
- `gramps/plugins/view/familyview.py:144-148` (pre-fix) — insertion point.
