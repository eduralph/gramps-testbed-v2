# Brief — issue 8603 / family-event-list-stale-participant

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** family-event-list-stale-participant
- **Defect:** In the Family editor, the embedded Events tab's "Main participants" column
  keeps showing a participant's OLD name after that person is edited and saved from
  within the same dialog. Reproduced by Daniele (4.1.3): edit the father from the family
  window, change his name and press OK — the family Events list still shows the old name.
  dsblank confirmed and captured it from the reporter's screenshot.
- **Success criterion:** After the fix, editing and saving a family member (participant)
  from the Family editor refreshes the embedded Events tab so the "Main participants"
  column shows the participant's current name. Demonstrable by the committed AT-SPI repro:
  after renaming the father, the family Events list shows the new name (red pre-fix — old
  name persists; green post-fix).
- **Invariant to restore:** Derived data displayed in an open editor (participant names
  in the family Events list) must reflect the current state of the referenced objects
  after an edit that has been committed — a `person-update` for a referenced person must
  refresh the views that render that person's data. (Gramps editor-consistency rule; no
  external canon — the editor already listens for `person-update` but only refreshes the
  top father/mother panel, not the embedded event list.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium
- **Scope:** On `person-update` for a family member, the Family editor refreshes only its
  top father/mother display (`load_data`) and leaves the embedded Events tab stale, so
  the "Main participants" column shows outdated names. Make the participant-name refresh
  reach the embedded event list. / out of scope: the unsaved-data cross-dialog ordering
  problem (issue 7924), the Gallery/Note tabs' separately-noted non-rebuild, and any
  rework of how the event list computes participant names.
- **Repro instruction:** On `maintenance/gramps61`, load a tree with a family that has
  events with main participants; open the family (Families → double-click), view the
  Events tab, then edit the father from the family window, rename him, press OK. The
  Events tab still lists his old name under Main participants.
- **Test file:** `engine/interface/test_bug_0008603_family_event_participant_refresh.py`
  (committed AT-SPI/dogtail repro in the testbed; NOT in `patch.diff`). Red on the
  unpatched worktree, green on the patched one.
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause: `gramps/gui/editors/editfamily.py:508` maps `person-update` →
  `topdata_updated`, which at `editfamily.py:579-585` calls only `load_data`
  (`editfamily.py:782-796`), refreshing the top panel but not `self.event_list`
  (`editfamily.py:816`)).
- **New/removed files:** none in gramps — `patch.diff` modifies existing files only; the
  AT-SPI repro ships in the testbed `engine/interface/`, outside gramps' POTFILES scope.
- **Prior-art check (triage cycles):** searched `gramps/gui/editors/editfamily.py` on
  `upstream/maintenance/gramps61` — References-tab / order / black / license changes but
  no event-list participant refresh; no open/closed PR found for this defect. Not already
  upstream.
- **Mantis:** 8603
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.
