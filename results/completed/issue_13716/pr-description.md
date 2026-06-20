## Root cause

A view's sidebar-filter "Type" selector (the same widget the Filter Gramplet hosts) reads the database's custom types exactly once at widget construction time via `dbstate.db.get_note_types()` (and similar per-filter methods), storing the result in `self.custom_types`. The selector's model (`StandardCustomSelector`) is built once from that snapshot and never rebuilt. When custom types are added to the already-open database after the filter widget is constructed (e.g., a "GEDCOM import" Note type created by importing a GEDCOM with errors), the new types never appear until the filter widget is torn down and rebuilt. This differs from the editor dialogs, which rebuild their type selector from the database "anew every time" they are shown (Mantis note 3).

## Fix

**New GUI-free module: `gramps/gui/filters/sidebar/_typefilterlist.py` (lines 1–82)**

Introduces `TypeFilterList` — a registry of `(fetch, apply)` pairs that orchestrates the refresh of a sidebar filter's type selectors without GUI imports. The `refresh()` method re-calls each registered `fetch` (which re-reads the *live* database) and passes the result to `apply` (which rebuilds the selector widget in place).

**Shared path: `gramps/gui/filters/sidebar/_sidebarfilter.py`**

- Line 178: Imports `TypeFilterList`
- Lines 186–187: `SidebarFilter.__init__` initializes `self._type_filters` and calls the new `_register_type_filters()` hook
- Line 195: `_db_changed` calls `self._type_filters.refresh()` to update selectors when the database changes
- Lines 203–244: Three new methods in `SidebarFilter`:
  - `_register_type_filters()` (lines 203–212): Hook for subclasses; default does nothing
  - `add_type_filter(monitored, db_method)` (lines 214–236): Registers a type selector; resolves `db_method` on the *live* database, connects the combo's `notify::popup-shown` signal for refresh-on-open
  - `_type_popup_shown(combo, pspec)` (lines 238–244): Signal handler that calls `refresh()` when a selector's drop-down opens

**Sidebar filter subclasses: `_notesidebarfilter.py`, `_eventsidebarfilter.py`, `_familysidebarfilter.py`, `_personsidebarfilter.py`, `_placesidebarfilter.py`, `_reposidebarfilter.py`**

Each now overrides `_register_type_filters()` and calls `add_type_filter()` once per type selector:
- `_notesidebarfilter.py:85–87`: Registers Note's Type selector with `get_note_types`
- `_eventsidebarfilter.py:84–85`: Registers Event's Type selector
- `_familysidebarfilter.py:98–100`: Registers Event and Family Relation type selectors
- `_personsidebarfilter.py:126–128`: Registers Event type selector
- `_placesidebarfilter.py:99–101`: Registers Place type selector
- `_reposidebarfilter.py:73, 92–94`: **Fixes pre-existing bug** — reads `get_repository_types()` (not `get_event_types()`) for the repository Type selector; registers the correct method

**Refactor for in-place rebuild: `gramps/gui/autocomp.py` and `gramps/gui/widgets/monitoredwidgets.py`**

- `autocomp.py:154`: Stores `self.completion_store` for later reuse
- `autocomp.py:179–225`: Extracts model-filling logic into `_fill_menu()` and `_fill_list()` (clearing first, then re-appending), callable on existing store objects
- `autocomp.py:258–272`: New `rebuild()` method re-fills the selector's model in place, preserving the widget object the GUI is bound to (critical for live update of an open drop-down)
- `monitoredwidgets.py:588–600`: New `rebuild()` method on `MonitoredDataType` preserves the current selection while rebuilding via `StandardCustomSelector.rebuild()`

**Test: `gramps/gui/filters/sidebar/test/_sidebarfilter_test.py`**

Adds unit tests that drive the production repopulate path (`TypeFilterList.refresh()` and `SidebarFilter.add_type_filter()` wiring) headlessly:
- `test_type_selector_reflects_new_custom_type_after_refresh()` (lines 490–513): Verifies a custom Note type added to the open database is offered after refresh, and absent beforehand (the bug)
- `test_refresh_reflects_removed_custom_type()` (lines 515–526): Verifies removed types are also tracked
- `test_typefilterlist_refetches_live_source()` (lines 528–541): Verifies `TypeFilterList` re-reads its source on every refresh
- `test_repo_filter_reads_repository_types_not_event_types()` (lines 553–575): Locks in the fix for the repository filter's pre-existing bug (reading event types instead of repository types)

**POTFILES: `po/POTFILES.skip`**

Lines 611–613: Registers the new files (no translatable strings):
- `gramps/gui/filters/sidebar/_typefilterlist.py`
- `gramps/gui/filters/sidebar/test/__init__.py`
- `gramps/gui/filters/sidebar/test/_sidebarfilter_test.py`

## Verified against

Target branch: `gramps-project/gramps @ upstream/maintenance/gramps61` (commit b679c084f6).

**Red→green proof (C4 verify gate, clean upstream/maintenance/gramps61):**
- GREEN (fix applied): Headless unit test runs 4 tests OK
- RED (production reverted, test kept): Test fails — the `TypeFilterList` repopulate path does not exist

The interface repro test (`engine/interface/test_bug_0013716_sidebar_filter_type.py`, testbed harness only, not in `patch.diff`) opens the Notes category, reads the sidebar Type filter's offered options, adds a Note carrying a sentinel custom type via the Note editor, then re-opens the same sidebar Type combo (no view recreation) and asserts the sentinel is now offered. Advisory GUI layer; the gated proof remains the headless unit test.

## Test

**Shipped regression test** (part of `patch.diff`): `gramps/gui/filters/sidebar/test/_sidebarfilter_test.py`

Tests the production repopulate path (`TypeFilterList.refresh()` + `SidebarFilter.add_type_filter()` wiring) without a display. The test imports the sidebar filter classes (safe at import time — only class definitions, no Gtk widget construction) but builds filter instances via `__new__` to avoid `__init__`'s Gtk widget creation. Test doubles stand in for the GUI selector widget (`_RecordingMenu`, records the custom values offered) and database state (`_FakeDb`, tracks custom types and returns them on demand). The production wiring is exercised directly: `_register_type_filters()` calls `add_type_filter()`, which routes through `TypeFilterList.refresh()` — same path the shipping GUI uses.

**Testbed interface repro** (optional, advisory GUI layer, NOT in `patch.diff`): `engine/interface/test_bug_0013716_sidebar_filter_type.py`

Interactive test that opens the Notes category, adds a custom type via the Note editor, and asserts the sidebar Type filter's options now include it without recreating the view. Gracefully skips if the Gramps GUI infrastructure (`dogtail` / AT-SPI) is unavailable; the shipped unit test is the gating proof.

Fixes #13716

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
