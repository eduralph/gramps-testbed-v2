# Build notes — issue 8603 / family-event-list-stale-participant

## Success criterion (restated)
After renaming a family member (participant) from *inside* the Family editor and
saving, the embedded Events tab's "Main Participants" column must show the
participant's **current** name — red pre-fix (old name persists), green post-fix.
The brief names it an **Invariant to restore**: a `person-update` for a
referenced person must refresh the views that render that person's data.

## Root cause (cited on target branch `maintenance/gramps61`)
- `EditFamily._connect_db_signals` maps `person-update` → `topdata_updated`
  (`gramps/gui/editors/editfamily.py:507`).
- `topdata_updated` calls only `load_data` (`editfamily.py:579-586` →
  `editfamily.py:782-796`), which refreshes the **top father/mother panel** and
  `self.phandles` — nothing else.
- The embedded event list `self.event_list` (an `EventEmbedList` created at
  `editfamily.py:816`) registers only `event-update` / `event-delete` callbacks
  (`gramps/gui/editors/displaytabs/eventembedlist.py:139-150`). It never listens
  for `person-update`.
- Its "Main Participants" column is *derived* from the referenced persons' names:
  `EventRefModel.column_participant` → `get_participant_from_event(self.db, ref)`
  (`gramps/gui/editors/displaytabs/eventrefmodel.py:204-205`), built at model
  construction time.

So when a participant is renamed and committed, `person-update` fires, the top
panel refreshes, but the event list model is never rebuilt → the Main
Participants column keeps the stale name. That is exactly the reporter's symptom.

## Fix (smallest change that restores the invariant)
`gramps/gui/editors/editfamily.py`:
1. Route `person-update` to a new dedicated handler `person_updated` (change at
   the registration line, was `topdata_updated`).
2. `person_updated` calls `topdata_updated()` (top panel, unchanged behaviour)
   **and**, when the tab exists, `self.event_list.rebuild_callback()`.

`rebuild_callback` (`embeddedlist.py:635-643`) sets `changed = True` then
`rebuild()` (`embeddedlist.py:589-625`), which calls `construct_model()` →
`build_model(self.get_data(), self.dbstate.db)` (`embeddedlist.py:584-587`). That
constructs a **fresh** `EventRefModel` with a **fresh** `CacheProxyDb`
(`eventrefmodel.py:123`), so `column_participant` re-reads the committed name from
the db. Result: the Main Participants column shows the new name.

The `hasattr(self, "event_list")` guard: `person_updated` can, in principle, fire
before `_create_tabbed_pages` has built `self.event_list`; the guard keeps the
top-panel refresh (`load_data`, which `person_delete` at `editfamily.py:514-522`
already relies on early) working and simply skips the not-yet-built tab. Cheap and
safe.

### Why this is the right seam (and mirrors existing code)
The Children tab in the *same file* already does exactly this: `ChildEmbedList`
registers `person-update` → `person_change` → `self.rebuild()`
(`editfamily.py:179,185-190`). So the Family editor already treats "a referenced
person changed → rebuild the tab that renders them" as the correct pattern; the
event list was simply never wired the same way. `rebuild_callback` is also the
same entry point `EventEmbedList.event_change` uses on `event-update`
(`eventembedlist.py:152-158`) — i.e. the supported "data changed outside this
tab, rebuild" seam. No new module, no new API.

### Alternatives considered and rejected
- **Rebuild only the participant column, not the whole model.** There is no
  per-column refresh API on `EmbeddedList`; the model is a `Gtk.TreeStore` rebuilt
  wholesale by `construct_model`. A column-only path would mean new code in
  `EventRefModel`/`EmbeddedList` (a new method + call sites) versus the 1-line
  `rebuild_callback()` reuse here. Larger surface, no user-visible benefit — the
  full rebuild is what `event_change` already does on every event edit.
- **Make `EventEmbedList` itself listen for `person-update`** (register a person
  callback in `eventembedlist.py:_connect_db_signals`). This would also work, but
  it spreads the fix into the reusable displaytab and would fire for *every*
  person-update globally (the tab would have to filter to its participants),
  whereas the Family editor already knows the update concerns one of *its* people
  and owns the top-panel refresh. Keeping the refresh in `EditFamily`, next to the
  existing `load_data` refresh, is the minimal, localized change (2 hunks, 1 file,
  +16 lines) and matches the Children-tab precedent above.

## Out of scope (per brief)
- The **unsaved-data cross-dialog ordering** problem (issue 7924): dsblank's note
  worries about editing a person whose data "hasn't been saved yet". The success
  criterion here is explicitly about editing **and saving**; on `person-update`
  the person is already committed, so a rebuild reads correct data. Not touched.
- Gallery/Note tabs' separately-noted non-rebuild (the `## Todo` at
  `editfamily.py:541`). Not touched.
- How the event list computes participant names. Not touched.

## Files / POTFILES
Patch modifies one existing core file (`editfamily.py`) — no `.py` added or
removed in gramps, so `po/POTFILES.in` / `POTFILES.skip` need no change
(T2-potfiles N/A). The regression test lives in the **testbed** at
`engine/interface/test_bug_0008603_family_event_participant_refresh.py` — outside
gramps' POTFILES scope, and NOT part of `patch.diff` (per the interface-repro
convention, INTEGRATION.md §3).

## Test (the AT-SPI repro) and why it drives production
`engine/interface/test_bug_0008603_family_event_participant_refresh.py` launches a
real gramps on `TestTree`, opens a family whose father is a listed Main
Participant, renames the father to a unique sentinel surname via the family
window's father Edit button + the Edit Person dialog, presses OK, and asserts the
Events-tab table now contains the sentinel. It reads **only** the table carrying
the "Main Participants" column header (`eventembedlist.py:95`), so it isolates the
embedded event list from the top father/mother panel (which refreshes even
pre-fix). It exercises the real production path end-to-end — the same
`person-update` → `EditFamily` code the patch changes — not a copy.

- **Red pre-fix:** `topdata_updated` refreshes only the top panel; the event list
  model is never rebuilt, so the sentinel never appears in the table.
- **Green post-fix:** `person_updated` calls `event_list.rebuild_callback()`; the
  model is reconstructed and re-reads the committed name, so the sentinel appears.

Every step the accessibility tree cannot drive is `skipTest`-ed (recorded
UNVERIFIABLE), including a baseline check that the father's name token is present
in the table *before* the edit — so a family where the father is not a listed
participant can never produce an infra false-red.

## Verification status — red→green NOT executed in the builder sandbox
The correct runner for a `Surfaces: gui` bundle is
`./engine/scripts/ubuntu/run-verify-interface.sh` (C4-verify-interface), which
launches gramps twice under Docker + Xvfb + AT-SPI. **Docker execution is blocked
in this builder sandbox** (the invocation requires an approval this autonomous
Do beat cannot grant), so I could not personally run the red→green legs. What I
*did* confirm here:
- `git apply --check` — `patch.diff` applies cleanly to the clean
  `gramps-6.1` worktree.
- `ast.parse` — the test file is syntactically valid.
- All added `patch.diff` lines are ≤ 88 cols (black-clean; black itself is not
  installed in this sandbox, but the added code uses standard formatting).

The behavioral red→green is left to the **C4-verify-interface gate at Check**,
which re-runs exactly this repro against the unpatched (red) and patched (green)
worktree. This is a genuine test that drives production — not a fabricated/vacuous
stand-in — so it is honest for the gate to execute.

### Manual validation steps (for sign-off)
1. On `maintenance/gramps61`, load a tree with a family that has events with main
   participants (e.g. gramps' `example.gramps`).
2. Families → double-click a family whose father is a participant of a listed
   event; open the **Events** tab and note the father's name in "Main
   Participants".
3. Click the father's **Edit** (pencil) button in the family window, change his
   surname, press **OK**.
4. **Pre-fix:** the Events tab still shows the old surname. **Post-fix:** the
   Events tab shows the new surname.
