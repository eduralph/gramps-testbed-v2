# Build notes — issue 8617 / bottombar-filter-gramplet-ignored

## Summary of the change

Two-token condition change at the two spots in the shared `ListView` base that
select `filter_info` on Search-bar visibility, so a *set* `generic_filter` is
applied regardless of whether the Search bar is visible.

- `gramps/gui/views/listview.py:335` (`build_tree`)
- `gramps/gui/views/listview.py:786` (`column_clicked`)

Both change from:

```python
if not self.search_bar.is_visible():
    filter_info = (True, self.generic_filter, False)
```

to:

```python
if self.generic_filter is not None or not self.search_bar.is_visible():
    filter_info = (True, self.generic_filter, False)
```

## Root cause (cited on `upstream/maintenance/gramps61`)

- The Filter gramplet — the *same* `Filter` gramplet class whether docked in the
  sidebar or the bottombar — sets the view's filter and rebuilds the tree:
  `gramps/plugins/gramplet/filter.py:76` (`self.gui.view.generic_filter =
  self.filter.get_filter()`) then `:77` (`self.gui.view.build_tree()`).
- `ListView.build_tree` decided whether to use that `generic_filter` or the
  Search bar's value **purely on Search-bar visibility**:
  `gramps/gui/views/listview.py:335-338`. The identical pattern is in
  `column_clicked` at `listview.py:786-789` (so a header-click re-sort recomputes
  `filter_info` the same way).
- `sidebar_toggled` shows the Search bar *exactly when the sidebar is hidden*:
  `gramps/gui/views/listview.py:432-440` (`_searchbar.py:188-197`
  `show`/`hide`/`is_visible`).

So: sidebar hidden ⟹ Search bar visible ⟹ `build_tree` takes the
`self.search_bar.get_value()` branch and the gramplet's `generic_filter` is
silently dropped. This is precisely bamaustin's diagnosis on the Mantis thread
("Could the filter being bypassed be related to the Search bar -- that is only
enabled when the Sidebar is disabled?").

`self.search_bar.get_value()` returns `(False, (index, text, inv), False)` for an
empty search (`_searchbar.py:171-178`), i.e. "match everything" — which is why
the list is left unfiltered rather than erroring.

## Why this restores the Invariant (and holds for every `ListView` subclass)

The brief's Invariant: a filter the user explicitly set via the Filter gramplet
(`view.generic_filter`) must be applied to the list, whichever bar hosts the
gramplet. The new condition makes a non-`None` `generic_filter` win over
Search-bar visibility at *both* decision points. The change is in the shared
`ListView` base (`listview.py`), not in any concrete view, so it holds for every
`ListView` subclass (People/Person{Tree,List}View, Events, Sources, Places,
Citations, Repositories, Media, Notes, Families) — satisfying the brief's
SELF-TEST that the property must not be a single-view special case.

Semantics preserved for the `generic_filter is None` cases:
- sidebar shown (Search bar hidden), no gramplet filter → `(True, None, False)`
  = show all, unchanged.
- sidebar hidden (Search bar visible), no gramplet filter → falls to the
  Search-bar branch (text search), unchanged.

Only the previously-broken case changes: a *set* `generic_filter` with the
Search bar visible now applies the filter.

## Precedence (deliberately per the brief's scope)

When both a Search-bar text search **and** a gramplet `generic_filter` are set at
once, the gramplet filter now wins. The brief puts "combining a Search-bar text
search AND a gramplet filter at once" **out of scope** ("restore the dropped
filter first") and the Invariant demands the `generic_filter` not be dropped, so
"explicit gramplet filter wins" is the correct minimal precedence here — a fuller
AND/compose design is a separate, larger change. A user who wants the text search
back clears the gramplet filter (Reset/empty + Find sets `generic_filter` back to
`None` via `get_filter()` returning `None`, `_personsidebarfilter.py:234-235`),
after which the Search bar behaves exactly as before.

## Alternatives considered and rejected

1. **Remove the cause in `sidebar_toggled` — decouple Search-bar visibility from
   sidebar visibility, or clear `generic_filter` on toggle.** Rejected: it
   doesn't restore the invariant (the gramplet filter would still be governed by
   an unrelated bar's visibility), and it perturbs the established
   sidebar↔searchbar UX the brief lists as out of scope. It is also *larger*: the
   Search bar is shown/hidden from `sidebar_toggled` (`listview.py:432-440`) and
   its visibility is read in `build_tree` **and** `column_clicked`; making
   visibility no longer imply "use the search value" would touch all three sites
   plus the toggle, vs. the 2 one-line edits here.

2. **Special-case the People view / the gramplet.** Rejected: fails the brief's
   SELF-TEST (must hold for every `ListView` subclass) and would duplicate logic
   per view.

3. **Extract the filter-selection decision into an import-light helper module and
   unit-test it headlessly.** Rejected on two grounds: (a) the brief's Plan is
   explicit — "New/removed files: none in gramps — `patch.diff` modifies existing
   files only" — so adding a `gramps/**/*.py` module (which would also need a
   `po/POTFILES.skip` entry) is out of the plan; (b) the decision is one boolean
   already inlined at both sites, and the *behaviour under test* (the filter
   actually reducing the visible list) lives in the rest of `build_tree` —
   `self.model.destroy()`, `make_model(..., search=filter_info)`,
   `build_columns`, GTK column sizing, `list.set_model`, `show_filter_results`
   (`listview.py:346-381`) — which is irreducibly GUI/DB-bound. Testing only an
   extracted boolean would be a proxy, not the Success criterion (rows actually
   filtered). See the test section.

## Test — committed AT-SPI/dogtail repro (not in `patch.diff`)

`engine/interface/test_bug_0008617_bottombar_filter.py`
(`Bug8617BottombarFilterTest`). This is a `Surfaces: gui` bundle; per
INTEGRATION.md §3 the per-fix behavioral C4 is `run-verify-interface.sh`, which
runs this committed repro **red on the unpatched worktree, green on the patched**
one (the repro lives in the testbed mount, not `patch.diff`, so red↔green is
simply patch-applied-vs-not).

Why an interface repro (not a headless unit): the Success criterion is that
applying the gramplet filter **reduces the visible rows** with the sidebar
hidden. That end result is produced by the whole `build_tree` GUI/DB path
(model rebuild + tree rendering), driven through the real Filter gramplet — it
cannot be exercised without a running GUI. The test drives **production**: it
seeds the People view's real gramplet-bar `.ini` files so the actual `Filter`
gramplet loads in the Bottombar with the sidebar hidden, then types into the
gramplet's real Name entry and applies it (Return → `SidebarFilter.clicked` →
`Filter.__filter_clicked` → `view.generic_filter = get_filter()` →
`build_tree`) — i.e. the exact production code the fix changes. No stand-in, no
re-implementation.

Oracle: the status-bar filter label `<title>: matched/total`
(`ListView.build_tree` → `uistate.show_filter_results` → `Statusbar.set_filter`,
`gramps/gui/widgets/statusbar.py:137`) reflects `model.displayed()/total()`,
so it is immune to GtkTreeView row virtualisation (only on-screen rows surface as
AT-SPI cells) and works for the grouped default People view.

- **Red (unpatched):** sidebar hidden ⟹ Search bar visible ⟹ `build_tree` uses
  the empty Search value ⟹ `matched == total` after applying the `Warner`
  filter ⟹ `assertLess(matched, total)` **fails**.
- **Green (patched):** `generic_filter` is applied ⟹ `matched < total` ⟹ passes.

Preconditions are guarded so the repro only *fails* on the delivered #8617
symptom: it confirms the Search bar is visible (a showing "Clear" push button —
`_searchbar.py:60`; the sidebar's reset button is "Reset",
`_sidebarfilter.py:120`) AND exactly one showing "Name" label (the Bottombar
gramplet). If the infra can't establish this (e.g. the `.ini` seed didn't take),
it `skipTest`s — which `run-verify-interface.sh`'s red-leg skip-guard correctly
routes to PDCA-UNVERIFIABLE, never a false red-PASS.

No POTFILES change: the repro ships in the testbed `engine/interface/` (outside
gramps' POTFILES scope) and `patch.diff` adds/removes no gramps `.py`, so
`T2-potfiles` is N/A (brief "New/removed files: none").

## Verification performed here

- `git -C <gramps-6.1 worktree> apply --check` — **patch applies cleanly** to
  `upstream/maintenance/gramps61` (worktree HEAD = `0d9e148908`,
  `upstream/maintenance/gramps61`).
- `python3 -m py_compile` — the repro compiles.
- Formatting: the two changed lines are 83 and 79 columns (< 88), so `black`
  (gramps' pre-commit formatter, default line length) leaves them unchanged;
  nothing else in the file is touched. (`black` is not installed in this sandbox
  to run `--check`; verified by column count.)

## Verification NOT run in this session (needs Docker) — for the human at sign-off

`run-verify-interface.sh` (the behavioral red→green) and `run-verify.sh` could
not be executed in-place here: this session's shell blocks the `docker`/`env`
invocations they require (they prompt for approval). Run at sign-off:

```
PDCA_BUNDLE=results/issue_8617 ./engine/scripts/ubuntu/run-verify-interface.sh
```

Expect: `C4-verify-interface: green-with-fix=PASS / red-without-fix=PASS`.

Note the unit C4 (`run-verify.sh`) is **PDCA-UNVERIFIABLE by design** for this
bundle — `patch.diff` ships no core `*_test.py` (the test is the AT-SPI repro in
the testbed), so it emits exit 77; that routes to §6 NEEDS-HUMAN and the human
confirms the GUI red→green at sign-off, which is exactly right for a GUI fix.

### Manual validation (matches the brief's Repro instruction)

1. On `maintenance/gramps61`, open the People view; add the **Filter** gramplet
   to the **Bottombar** (Bottombar menu → Add → Person Filter).
2. Hide the sidebar (View → Sidebar, or `Shift+Ctrl+R`). The Search bar appears.
3. In the Bottombar Filter gramplet, type a surname (e.g. `Warner`) in **Name**
   and press **Find**.
   - Pre-fix: the list is unchanged (status bar `People: N/N`).
   - Post-fix: the list is filtered (status bar `People: <fewer>/N`).
4. Show the sidebar again — filtering still works (regression check).
