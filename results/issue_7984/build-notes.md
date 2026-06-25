# Build notes — issue 7984 / search-no-surname-typeahead

**Disposition: VERIFY-FIRST (POSSIBLY-FIXED).** No code patch. Deliverables are
a committed AT-SPI repro + fixture in the testbed mount, an **empty** `patch.diff`
(no fix to ship — the relevant rework is already on `maintenance/gramps61`), and a
`close-disposition` of `manual-verification` routing the final call to the human at
sign-off.

## What the bug was

Mantis 7984 (Gramps 4.x, grouped People view): on a tree where a person has **no
surname**, that person lands in the collapsed "no surname" group. Ctrl+F type-ahead
would not descend into that **collapsed** group — the user had to expand the folder
by hand first (reporter notes ~0037726, ~0044606 in `notes.json`). The reporter also
found that with the default "Surname, Given" name format you had to type `", "` then
the given initial; switching name display to "Given name only" let a bare given name
match — *but the no-surname folder still had to be opened manually* (~0044606). That
last sentence is exactly the residual defect 7984 is about.

## Why it is POSSIBLY-FIXED on the target branch (path:line on maintenance/gramps61)

`InteractiveSearchBox.search_iter_slow` now searches **both expanded and collapsed**
rows and auto-expands to the hit:

- `gramps/gui/widgets/interactivesearchbox.py:443-481` — `search_iter_slow`.
  - line 447 docstring: "Both expanded and collapsed rows are searched."
  - lines 465-466: `if is_tree and model.iter_has_child(cur_iter): cur_iter =
    model.iter_children(cur_iter)` — descends into children **unconditionally**,
    i.e. regardless of whether the group row is expanded in the view.
  - line 459: `self._treeview.expand_to_path(found_path)` — on a match it expands
    the ancestors so the (previously collapsed) group opens.
  - lines 460-462: `scroll_to_cell` + `selection.select_path` + `set_cursor` —
    reveals and selects the reached person.
- Match column = the configured search column, matched `startswith`:
  `gramps/gui/widgets/interactivesearchbox.py:483-488` (`search_equal_func`).

The search column is the **sorted** column, wired only in `column_clicked`:
`gramps/gui/views/listview.py:826-827` (`search_col = self.column_order()[data][1]`
then `self.list.set_search_column(search_col)`). It is **not** set at view build
(`build_tree`, listview.py:330-387, and `build_columns`, listview.py:243-291, never
call it), so a fresh GtkTreeView's `search-column` stays at GTK's default (-1) until
a header is clicked — see the repro design note below.

Supporting facts:
- No-surname group header text = `preferences.no-surname-text`
  (`gramps/gui/views/treemodels/peoplemodel.py:638` `column_header` returns
  `no_surname`; default `"[%s]" % _("Missing Surname")` at
  `gramps/gen/config.py:320`).
- The grouped People view (`PersonTreeView`) is registered **first** in the People
  category (`gramps/plugins/view/view.gpr.py:198-211`, before `personlistview` at
  217-227), and `use-last-view` defaults False (`gramps/gen/config.py:332`,
  `views_to_show` → category 0 / view 0, `gramps/gui/viewmanager.py:1996-2023`), so a
  fresh launch lands on the grouped tree view.
- Name format "Given" is `Name.FN = 4` (`gramps/gen/lib/name.py:63`), selected via
  `preferences.name-format` (`gramps/gen/config.py:313`, default 1 = LNFN).

## The repro (engine/interface/test_bug_7984_search_no_surname.py + data fixture)

Fixture `engine/interface/data/Bug7984NoSurname.gramps`: four persons, each with a
**given name only, no surname** (Aatos, Eero, Onni, Ukko). All land in the single
`[Missing Surname]` group, collapsed on launch.

The test (subclasses the AT-SPI `GrampsInterfaceTestCase`):
1. launches with `preferences.name-format:4` so the searchable Name column holds the
   given name verbatim (this is the reporter's own "Given name only" configuration —
   it isolates the *folder-reaching* defect from the out-of-scope comma-prefix
   limitation);
2. navigates to the grouped People view, clicks the "Name" column header to **pin the
   type-ahead search column to Name** (required — see below) which also rebuilds and
   collapses the groups;
3. asserts the precondition: `[Missing Surname]` present and the target person `Onni`
   **not** realised (group collapsed);
4. focuses the tree, presses **Ctrl+F**, types `Onni`;
5. asserts `Onni`'s cell becomes visible — i.e. the search descended into the
   collapsed group and `expand_to_path` opened it. `Onni` is a *non-first* child, so a
   hit proves traversal into the group, not just a match on its first row.

The observable is sound: in this controlled single-group fixture, the only thing that
realises a child cell of a collapsed group is the search's `expand_to_path`. Cell
presence-after-absence is the load-bearing oracle; AT-SPI selection state is checked
advisorily (printed, never failed on) because reading it is flakier than presence.

Infra that can't drive a widget `skipTest`s (mirrors
`test_bug_0011786_tag_rename_listview.py`), so only a *delivered* collapsed-folder
miss reports the 7984 symptom — a missing-widget environment skips rather than
false-reds.

### Why the test must click the Name header (search-column determinism)

I read the production path carefully: `set_search_column` is called **only** from
`column_clicked` (listview.py:826-827); nothing sets it at view build. A GtkTreeView's
`search-column` defaults to -1, and `do_get_value(iter, -1)` resolves to `fmap[-1]`
(the last visible column, `treebasemodel.py:940-996`), i.e. Death Date for the People
view default columns (`libpersonview.py:117`), which is empty for these persons. So on
a *truly fresh* view a typed given name would match nothing irrespective of the bug.
Clicking the Name header pins the search column to Name (col 0) deterministically — so
the test exercises the real fix rather than a mis-targeted column. If the header can't
be driven, the test **skips** (never false-reds).

## Alternatives considered / ruled out

- **Type the `", Onni"` comma-prefix under the default LNFN format** (avoids the
  name-format override). Rejected: it folds in the *residual* limitation
  (`search_equal_func` matches only the search column `startswith`, so a bare given
  name still can't be found — brief's out-of-scope item) and muddies which behaviour
  the green proves. `name-format:4` isolates the folder-reaching fix cleanly and is
  the reporter's documented working setup.
- **Assert on selection state instead of cell presence.** Kept as an advisory print
  only; selection-state reads via AT-SPI are markedly flakier than cell presence, and
  presence-after-absence already proves the collapsed group was auto-expanded.
- **Ship a non-empty `patch.diff` to make C4 run a red→green leg.** There is no fix to
  ship — the rework is already on the target. An empty `patch.diff` is the honest
  state; `pdca publish` treats a 0-byte/whitespace patch as a no-fix close
  (`src/pdca_harness/publish.py:117-126`, issue #95), so it does not break publish.

## Out of scope — flag for a future Plan (brief's residual-limitation item)

`search_equal_func` (interactivesearchbox.py:483-488) matches only the configured
search column with `startswith`. With the default `name-format:1` (LNFN →
"Surname, Given"), a no-surname person's Name cell renders as ", Given", so typing a
bare **given** name does not match it (the user must type `", "` first). That is a
separate UX decision (auto-open the no-surname folder on a comma, or search additional
columns), not the reported "must open the folder manually" symptom this verify covers.

## Proven / not proven

- **Static, proven here:** the production rework that addresses the reported symptom is
  present on `maintenance/gramps61` (citations above); the repro and fixture compile /
  parse (`py_compile`, XML well-formedness); the repro drives the real production path
  (the live `InteractiveSearchBox` via Ctrl+F in a launched gramps), not a copy.
- **Not proven here:** the live red→green / green-on-current GUI run. This is a
  verify-first with no patch, so the C4 red↔green mechanic cannot run by design
  (brief). The interface gate (`run-verify-interface.sh`, Docker + Xvfb + AT-SPI) was
  **not runnable in this build sandbox** (Docker invocation blocked), so the GUI green
  is to be confirmed by the human at sign-off — exactly the `manual-verification`
  outcome the brief anticipates. `run-verify-interface` seeds every
  `engine/interface/data/*.gramps`, so `Bug7984NoSurname` is seeded automatically when
  the human runs it.

## Files

- `engine/interface/test_bug_7984_search_no_surname.py` — committed AT-SPI repro
  (testbed mount; not in patch.diff; no POTFILES change per brief).
- `engine/interface/data/Bug7984NoSurname.gramps` — surname-less fixture tree.
- `patch.diff` — empty (verify-first, no code fix).
- `close-disposition` — `manual-verification`.
