# Build notes — issue 13716 / sidebar-filter-type-list-stale

Target branch: `gramps-project/gramps @ maintenance/gramps61` (verified against the
pinned `upstream/maintenance/gramps61` worktree, HEAD `b679c084f6`).

## Root cause

Every view's sidebar-filter "Type" selector (the widget the Filter Gramplet hosts)
is a `MonitoredDataType` whose custom values are read from the database exactly once,
in the subclass `__init__`, e.g. `_notesidebarfilter.py:66`
(`self.custom_types = dbstate.db.get_note_types()`) and the identical pattern in
`_eventsidebarfilter.py:71`, `_personsidebarfilter.py:94`, `_familysidebarfilter.py:79`
& `:94`, `_placesidebarfilter.py:78`, `_reposidebarfilter.py:73`. That snapshot is
handed to `MonitoredDataType` → `StandardCustomSelector`, which builds the combo model
once (`autocomp.py` `create_list`/`create_menu`) and is never rebuilt. Custom types
created in the already-open database afterwards (a "GEDCOM import" Note type, an edited
custom type) never appear until the gramplet/view is torn down and rebuilt — exactly
the maintainer's diagnosis (Mantis 13716 note 3): the editor dialogs rebuild their type
selector "anew every time" they are shown; the sidebar filters build theirs once and
"never update them again."

## Invariant restored

"A UI selector derived from the database must reflect the database's current contents
whenever it is presented." The fix gives the shared `SidebarFilter` a repopulate path
that re-reads the live database and rebuilds every registered type selector, and wires
it to fire when the selector is presented to the user (its drop-down opens) and on
database change — mirroring the editor dialogs' rebuild-per-presentation contract.

## Change (smallest change that restores the invariant, done once in the shared path)

1. New GUI-free module `gramps/gui/filters/sidebar/_typefilterlist.py` — `TypeFilterList`:
   a registry of `(fetch, apply)` pairs; `refresh()` re-calls every `fetch` (live DB
   read) and hands the result to `apply`. This is the production *repopulate path*, and
   being free of `gi`/`gramps.gui` it is unit-testable headlessly. Registered in
   `po/POTFILES.skip` (no translatable strings).

2. Shared `SidebarFilter` (`_sidebarfilter.py`):
   - import (`:49`); `self._type_filters = TypeFilterList()` + `self._register_type_filters()`
     in `__init__` (`:108`);
   - `_register_type_filters()` default no-op hook (`:252`), `add_type_filter(monitored, db_method)`
     (`:263`) — registers `fetch` that resolves `db_method` on the **live** `self.dbstate.db`
     every call (so post-construction types are seen), `apply = monitored.rebuild`, and
     connects the combo's `notify::popup-shown` to `_type_popup_shown` (`:287`);
   - refresh on `database-changed` too (`_db_changed`, `:243`).

3. Each type-bearing subclass overrides `_register_type_filters()` with one
   registration call per selector (note/event/person/place/repo: 1 each; family: 2).
   This is wiring, not duplicated logic — the refresh logic lives only in the shared
   path. Repo keeps its existing `get_event_types` source (the staleness bug is
   orthogonal to which db method it reads).

4. `MonitoredDataType.rebuild(custom_values)` (`monitoredwidgets.py:493`) and
   `StandardCustomSelector.rebuild(additional)` (`autocomp.py:237`) — refill the existing
   combo model **in place** (clear + re-append via the refactored `_fill_list`/`_fill_menu`,
   so production model-building and rebuild share one implementation) and restore the
   current selection. In-place refill means an open drop-down updates live (no one-open
   lag) and avoids re-creating the widget.

## Why this seam for the test (headless / production-routing)

The C4 runner is headless; importing a `gramps.gui` *module* is fine (it only defines
widget classes — verified: `python3 -c "import gramps.gui.filters.sidebar"` succeeds in
the runner image), but *instantiating* a Gtk widget aborts without a display. So the
test imports the sidebar classes but never constructs one: it builds `NoteSidebarFilter`
via `__new__`, sets the three attributes the repopulate path needs, and calls the real
production `NoteSidebarFilter._register_type_filters` → `SidebarFilter.add_type_filter`
→ `TypeFilterList.refresh`. Doubles stand in only for the GUI selector widget
(`_RecordingMenu`, records the custom values applied — exactly the offered options) and
the DB state. Production routes through the same `TypeFilterList`/`add_type_filter`, so
this is not a parallel copy (principles §3.4): there is one repopulate implementation.

red→green proven with the runner image (`gramps-testbed:ubuntu-6.1.0`):
- GREEN (patched `gramps-6.1` worktree): `python3 -m unittest …_sidebarfilter_test` → 3 tests OK.
- RED (clean worktree + test only, fix absent — what C4's red pass reconstructs by removing
  the new prod module and reverting `_sidebarfilter.py`): `ModuleNotFoundError: …_typefilterlist`,
  exit 1. The test fails because the production fix is absent.

`git apply --check` of `patch.diff` is clean against `upstream/maintenance/gramps61`.

## Alternatives considered (with cost)

- **Per-subclass fix (e.g. patch only `_notesidebarfilter.py`).** Rejected by the brief's
  SELF-TEST: the invariant spans all 6 sidebar filters / 7 selectors. It would also
  duplicate the same fetch+rebuild logic ~7 times instead of once in the shared path.

- **Generalize upstream PR 809's place-only refresh.** PR 809 added a refresh on the
  *place* filter only and was never generalized; it is not on gramps61. Lifting its
  approach to one namespace repeats the per-subclass problem above.

- **Refresh via DB object-change signals (note-add/update/…) through `callman`.** More
  robust ("stays current while the gramplet sits open") but requires a per-subclass
  namespace→signal-set map (notes← note-*, events← event-*, family← event-* + family-*,
  …) — i.e. data that varies per subclass, pushing namespace-specific knowledge back
  into each subclass and adding ~4 signal registrations × 6 filters. The popup-shown +
  database-changed triggers are namespace-agnostic, live entirely in the shared path,
  and directly mirror the editor "rebuild when presented" contract, which is the named
  invariant. Noted as a possible follow-up, not needed to restore the invariant.

- **Re-create `MonitoredDataType`/`StandardCustomSelector` on refresh** (new model via the
  constructor) instead of in-place refill. Rejected: `set_model` on a popped-up combo can
  tear down the open drop-down (one-open lag for the repro's "re-open the Type selector"
  step). In-place `store.clear()` + re-append keeps the same model object the popup is
  bound to, so it updates live.

## Files

Production: `gramps/gui/filters/sidebar/_typefilterlist.py` (new),
`_sidebarfilter.py`, `_notesidebarfilter.py`, `_eventsidebarfilter.py`,
`_personsidebarfilter.py`, `_familysidebarfilter.py`, `_placesidebarfilter.py`,
`_reposidebarfilter.py`, `gramps/gui/widgets/monitoredwidgets.py`,
`gramps/gui/autocomp.py`.
Test: `gramps/gui/filters/sidebar/test/__init__.py` (new),
`gramps/gui/filters/sidebar/test/_sidebarfilter_test.py` (new).
POTFILES: `po/POTFILES.skip` (+3 entries: the new module + both test files; no
translatable strings).
All touched files pass `black`.
