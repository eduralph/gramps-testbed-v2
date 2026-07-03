## Summary

When a family member (participant) is edited and saved from within the Family editor, the embedded Events tab fails to refresh its "Main Participants" column — it continues to show the participant's old name rather than the updated one.

**Fix:** Route the `person-update` signal to a dedicated handler that refreshes both the top father/mother panel (existing behavior) and the event list model (new). The pattern mirrors the Children tab in the same editor.

## What to look at

**Affected files:** `gramps/gui/editors/editfamily.py`

**How to exercise:** Open a family with events where the father is listed as a main participant (view the Events tab, "Main Participants" column). Edit the father from the Family editor (pencil button → Edit Person dialog → change name → OK). Pre-fix: Events tab shows old name. Post-fix: Events tab shows new name immediately.

**Key functions and signal flow:**
- `EditFamily._connect_db_signals` (line 507): registers signal handlers, including `person-update`
- `EditFamily.topdata_updated` (lines 579–586): existing handler, refreshes top father/mother panel via `load_data`
- `EditFamily.person_updated` (new, lines 588–602): new handler that calls both `topdata_updated()` and `event_list.rebuild_callback()`
- `EmbeddedList.rebuild_callback` (lines 635–643): triggers fresh model construction to re-read data from database

## Root cause / Fix

Currently, the `person-update` signal is routed to `topdata_updated` (editfamily.py:507), which calls `load_data` (editfamily.py:579–586) to refresh only the top father/mother panel and `self.phandles`. The embedded event list (`self.event_list`, an `EventEmbedList` created at editfamily.py:816) never listens for `person-update` — it only registers callbacks for `event-update` and `event-delete` (eventembedlist.py:139–150).

The "Main Participants" column is derived from the referenced persons' names, computed at model construction time (eventrefmodel.py:204–205 calls `get_participant_from_event(self.db, ref)` for each row). Since the event list model is never rebuilt when a participant is renamed, the column values remain stale.

The fix introduces a new `person_updated` handler that:
1. Calls `topdata_updated()` — preserving the existing top-panel refresh
2. Calls `self.event_list.rebuild_callback()` — triggering a fresh event-list model construction to re-read current participant names from the database

This pattern mirrors the existing Children tab in the same editor (editfamily.py:179, 185–190), which already listens for `person-update` and calls `rebuild()` on change. The fix reuses `rebuild_callback`, the same entry point that `event-update` already uses (eventembedlist.py:152–158), so it introduces no new module API. A `hasattr(self, "event_list")` guard protects against `person-update` firing before `_create_tabbed_pages` has constructed the tab.

## Verified against

**Claim:** `person-update` signal currently reaches only the top panel, not the event list.  
**Evidence:**
- `editfamily.py:507` routes the signal to `topdata_updated`
- `topdata_updated` (editfamily.py:579–586) calls `load_data`, which refreshes the top panel but does not rebuild `self.event_list`
- Event list only registers `event-update`/`event-delete` callbacks (eventembedlist.py:139–150), never `person-update`

**Claim:** Event-list "Main Participants" column is computed at model construction time, not dynamically.  
**Evidence:**
- `eventrefmodel.py:204–205`: column values are computed by `get_participant_from_event(self.db, ref)` during model build
- `embeddedlist.py:589–625`: model is reconstructed fresh by `rebuild()`; column values reflect current database state only at that time

**Claim:** Patch routes `person-update` to a new handler that refreshes both top panel and event list.  
**Evidence:**
- `editfamily.py:509`: signal mapping now sends `person-update` to `self.person_updated` (was `self.topdata_updated`)
- `editfamily.py:588–602`: new `person_updated` method calls `topdata_updated()` then `self.event_list.rebuild_callback()`
- `embeddedlist.py:635–643`: `rebuild_callback` triggers fresh model construction, re-reading names from the database

**Claim:** Pre-fix: participant name remains stale in Events tab after rename.  
**Evidence:** Manual GUI verification on unpatched `maintenance/gramps61` — opened Family editor with father as main participant, edited and renamed father from Family editor, Events tab continued to show old name.

**Claim:** Post-fix: participant name refreshes in Events tab immediately after rename.  
**Evidence:** Manual GUI verification on patched tree — same scenario, Events tab now shows new name immediately.

**Claim:** Pattern is consistent with existing code.  
**Evidence:** Children tab in `editfamily.py:179, 185–190` already uses `person-update` → `rebuild()` for the same reason; `event-update` already reuses `rebuild_callback` as the update entry point (eventembedlist.py:152–158).

## Test

No core unit test ships in this patch — the behaviour is a GUI signal-driven refresh, not headless-testable. Coverage is a committed AT-SPI/dogtail regression in the gramps-testbed harness (not part of this PR), `engine/interface/test_bug_0008603_family_event_participant_refresh.py`, which renames a family's father from the Family editor and asserts the Events tab's "Main Participants" column updates. Manual repro: open a family whose father is a listed main participant, rename the father from the Family editor, and confirm the Events tab shows the new name immediately (pre-fix: it keeps the old name).

---

Fixes [#8603](https://gramps-project.org/bugs/view.php?id=8603)
