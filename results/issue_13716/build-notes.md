# Build notes — issue 13716 / sidebar-filter-type-list-stale (Iteration 2)

Target branch: `gramps-project/gramps @ maintenance/gramps61` (verified against the
pinned upstream worktree `gramps-6.1` / `gramps-6.1-lane0`, HEAD `b679c084f6`).

## What this iteration changes vs. iteration 1

The iteration-1 design was reviewed PASS on C1–C5; sign-off carried forward two items
(brief.md:90). This iteration addresses both and keeps the accepted design:

1. **Repository filter now reads the correct db method.** Iteration 1 deliberately
   preserved the pre-existing `get_event_types()` source for the *repository* sidebar
   filter's Type selector, which is a pre-existing bug: a repository Type selector must
   offer repository custom types, not event types. Sign-off (brief.md:90) directs fixing
   it here because the goal is a *working* Type selector. `get_repository_types()` exists
   on the db base API (`gramps/gen/db/base.py:826`). Changed both the construction-time
   snapshot and the live refresh source in `_reposidebarfilter.py`:
   - `:73` `self.custom_types = dbstate.db.get_event_types()` → `get_repository_types()`
   - `_register_type_filters` → `self.add_type_filter(self.event_menu, "get_repository_types")`
   (the in-patch "preserves the wrong method" comment is removed). This is a UI-side
   call-site correction, not a db-layer change — within scope; the brief's out-of-scope
   db clause (brief.md:44-45) is about how the db *stores/reads* custom types, untouched.

2. **Interface repro test added** at
   `engine/interface/test_bug_0013716_sidebar_filter_type.py` so the advisory GUI
   red→green gate is exercisable in the next Check pass (sign-off item 2, brief.md:90).
   It opens the Notes category, reads the sidebar Type filter's offered options, adds a
   Note carrying a sentinel custom type via the Note editor (which writes the type into
   the open db), then re-opens the *same* sidebar Type combo (no view recreation) and
   asserts the sentinel is now offered. Follows the existing `engine/interface/` pattern
   (graceful `skipTest` when infra can't drive a widget; only a delivered-but-stale Type
   selector reports the #13716 symptom). It is a testbed-harness file, not part of the
   gramps `patch.diff`. The interface tier is advisory per INTEGRATION §3; the gated
   proof remains the headless unit test.

3. **Headless test extended** with `test_repo_filter_reads_repository_types_not_event_types`
   — constructs `RepoSidebarFilter` via `__new__`, a fake db whose `repository_types` and
   `event_types` are disjoint, and asserts the repo filter's selector offers the
   repository types and not the event types. This locks in fix (1) against regression.

## Essential-dependency note (resolved)

Iteration 1 stamped `essential-dependency.json` (PASS-only-on-essential, depends on
`headless-ut-segfault`). On this iteration `run-verify.sh` (PDCA_LANE=0, clean upstream
`gramps-6.1-lane0`) ran the green leg headlessly with **4 tests OK** and the runner
**cleared the stale stamp** — C4 now passes on clean upstream/maintenance/gramps61, no
essential dependency. (The §6.1 sign-off concern about the missing stamp is moot.)

## Root cause (unchanged)

Every view's sidebar-filter "Type" selector is a `MonitoredDataType` whose custom values
are read from the database exactly once, in the subclass `__init__`
(`_notesidebarfilter.py:66` and the identical pattern in event/family/person/place/repo).
That snapshot feeds `StandardCustomSelector`, whose combo model is built once
(`autocomp.py` `create_list`/`create_menu`) and never rebuilt — so custom types created
in the already-open db afterwards never appear until the gramplet/view is rebuilt
(Mantis 13716 note 3: editor dialogs rebuild "anew every time"; sidebar filters build
once and "never update them again").

## Invariant restored (unchanged design)

A UI selector derived from the database must reflect the database's current contents
whenever it is presented. Done once in the shared `SidebarFilter` path:

1. New GUI-free `gramps/gui/filters/sidebar/_typefilterlist.py` — `TypeFilterList`: a
   registry of `(fetch, apply)` pairs; `refresh()` re-calls every `fetch` (live db read)
   and hands the result to `apply`. This is the production repopulate path, unit-testable
   headlessly. Registered in `po/POTFILES.skip` (no translatable strings).
2. Shared `SidebarFilter` (`_sidebarfilter.py`): constructs `self._type_filters` +
   `self._register_type_filters()` in `__init__`; `add_type_filter(monitored, db_method)`
   registers a `fetch` resolving `db_method` on the **live** `self.dbstate.db` every call,
   `apply = monitored.rebuild`, and connects the combo's `notify::popup-shown` to refresh;
   `_db_changed` also refreshes. Subclasses each call `add_type_filter` are present
   before `SidebarFilter.__init__` runs because every subclass builds its
   `MonitoredDataType` *before* `SidebarFilter.__init__(...)` (verified e.g.
   `_notesidebarfilter.py:70-84`, `_reposidebarfilter.py:77-93`).
3. Each type-bearing subclass overrides `_register_type_filters()` with one registration
   per selector (note→get_note_types, event/family/person→get_event_types[+ family
   get_family_relation_types], place→get_place_types, **repo→get_repository_types**).
   Wiring only — the refresh logic lives once in the shared path.
4. `MonitoredDataType.rebuild` (`monitoredwidgets.py`) + `StandardCustomSelector.rebuild`
   (`autocomp.py`) refill the existing combo model in place (clear + re-append via shared
   `_fill_list`/`_fill_menu`) and restore the current selection, so an open drop-down
   updates live and production model-building and rebuild share one implementation.

## Why this seam for the headless test (production-routing, GUI-import-free)

The test imports the sidebar classes (import only *defines* widget classes — safe
headless) but never constructs a Gtk widget: it builds `NoteSidebarFilter` /
`RepoSidebarFilter` via `__new__`, sets the three attributes the repopulate path needs,
and calls the real production `_register_type_filters` → `add_type_filter` →
`TypeFilterList.refresh`. Doubles stand in only for the GUI selector widget
(`_RecordingMenu`, records the applied custom values = the offered options) and the db
state. Production routes through the same `TypeFilterList`/`add_type_filter`, so this is
one implementation, not a parallel copy (principles §3.4).

## red→green proof

`PDCA_BUNDLE=… PDCA_LANE=0 ./engine/scripts/ubuntu/run-verify.sh` against clean
`upstream/maintenance/gramps61` (gramps-6.1-lane0):
- GREEN (fix applied): `…_sidebarfilter_test` → **4 tests OK**.
- RED (production reverted, test kept): the test fails — `_typefilterlist` is gone and
  the shared `add_type_filter`/`_register_type_filters` wiring is reverted, so the
  production repopulate path the test drives does not exist.
- `C4-verify: green-with-fix=PASS / red-without-fix=PASS` and the stale
  `essential-dependency.json` was cleared (now passes on clean upstream).

## Alternatives considered (with cost)

- **Keep `get_event_types` for the repo filter (iteration-1 choice).** Rejected by
  sign-off: it leaves the repository Type selector populated with the wrong type set —
  a working selector is the goal. Cost of the fix: 2 one-line call-site edits in
  `_reposidebarfilter.py` (lines 73 and the `_register_type_filters` body), no new
  machinery; the db method already exists (`base.py:826`).
- **Per-subclass fix.** Rejected by the brief SELF-TEST (brief.md:35): the invariant
  spans all 6 sidebar filters / 7 selectors; per-subclass would duplicate the
  fetch+rebuild logic ~7×. Shared-path is once.
- **Refresh via DB object-change signals through `callman`.** More robust but needs a
  per-subclass namespace→signal map (≈4 signal registrations × 6 filters), pushing
  namespace-specific knowledge back into each subclass. The popup-shown +
  database-changed triggers are namespace-agnostic, live in the shared path, and mirror
  the editor "rebuild when presented" contract (the named invariant). Possible follow-up.
- **Re-create the selector on refresh** instead of in-place refill. Rejected:
  `set_model` on a popped-up combo can tear down the open drop-down (one-open lag for the
  repro's "re-open the Type selector" step); in-place `store.clear()` + re-append keeps
  the model object the popup is bound to, updating live.

## Files

Production (patch.diff): `gramps/gui/filters/sidebar/_typefilterlist.py` (new),
`_sidebarfilter.py`, `_notesidebarfilter.py`, `_eventsidebarfilter.py`,
`_personsidebarfilter.py`, `_familysidebarfilter.py`, `_placesidebarfilter.py`,
`_reposidebarfilter.py`, `gramps/gui/widgets/monitoredwidgets.py`, `gramps/gui/autocomp.py`.
Test (patch.diff): `gramps/gui/filters/sidebar/test/__init__.py` (new),
`gramps/gui/filters/sidebar/test/_sidebarfilter_test.py` (new).
POTFILES (patch.diff): `po/POTFILES.skip` (+3: the new module + both test files, no
translatable strings).
Testbed harness (NOT in patch.diff):
`engine/interface/test_bug_0013716_sidebar_filter_type.py` (new, advisory interface repro).
All touched gramps files pass `black` (`--fast`, py target).
