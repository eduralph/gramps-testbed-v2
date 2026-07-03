# Brief — issue 7924 / child-editor-unsaved-data-lost-on-parent-save

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** child-editor-unsaved-data-lost-on-parent-save
- **Defect:** Primary editors are non-modal, so a parent editor (e.g. EditFamily) and a child
  editor it opened (e.g. EditPerson) can be open at once. Clicking the **parent's** OK saves the
  parent and cascade-closes the child through `ManagedWindow.close()` → `gwm.close_track()`, which
  tears down the tracked child window **without** invoking the child editor's
  `data_has_changed()` / SaveDialog guard — so the child editor's unsaved data is silently
  discarded with no warning.
- **Success criterion:** With a parent editor and a child editor both open and the child holding
  unsaved changes, confirming the parent (OK) must NOT silently discard the child's data: the
  cascade close honours the child's dirty state — the user gets the same "Save Changes?"
  prompt (or the close is blocked) that a direct child-close already triggers — so no unsaved
  edit is lost without acknowledgement. Demonstrated by the committed interface repro driving the
  Relationships-view add-family → add-person flow.
- **Invariant to restore:** Closing a window that owns child *primary-editor* windows with unsaved
  edits must apply the same save-guard the direct close path already enforces — it must not be
  bypassable via the parent's cascade. The direct path guards at
  `gramps/gui/editors/editprimary.py:244-262` (`close()` → SaveDialog when `data_has_changed()`);
  the cascade path (`gramps/gui/managedwindow.py:591-607`) must not discard a dirty child without
  the same prompt. State over the category: *no unsaved primary-editor data is discarded without a
  user prompt, regardless of which window triggers the close.*
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui — only observable through the running editors' close/OK flow; selects the
  C4-verify-interface gate. Manual verification at sign-off is expected (`PDCA-UNVERIFIABLE` for the
  automated red/green if the AT-SPI repro cannot fully assert the prompt).
- **Difficulty:** medium — touches the shared `ManagedWindow` close cascade; the fix must REUSE the
  existing `EditPrimary.data_has_changed()` / SaveDialog machinery, not add a parallel dirty-tracking
  layer.
- **Scope:** the `ManagedWindow.close()` cascade (`gramps/gui/managedwindow.py:591-607`, via
  `uistate.gwm.close_track(self.track)`) must, before tearing down a child window that is a primary
  editor reporting `data_has_changed()`, route through that editor's save-guard (prompt Save/Cancel,
  or save) instead of closing it silently. `EditFamily.__do_save` (`editfamily.py:1226`) has no
  open-child guard and is the trigger. / out of scope: making primary editors modal; a new global
  dirty/modified framework; non-editor `ManagedWindow` subclasses (which have no unsaved-data notion).
- **Repro instruction:** Relationships view → "Add a new family with person as parent" → in the
  Family editor click "Add a new person as mother" → type a name (and any data) in the Person editor
  → then click the **Family** editor's OK (not the Person editor's). Observe: the Person editor closes
  and the entered data is lost, with no warning.
- **Test file:** engine/interface/test_bug_7924_child_editor_data_loss.py — a committed AT-SPI/dogtail
  interface repro in the testbed mount (NOT in patch.diff), subclassing the interface harness: opens
  the Family editor, opens the child Person editor, enters data, clicks the Family editor's OK, and
  asserts the child's unsaved data is not silently lost (a Save/abandon prompt appears, or the data
  survives). Verify-first has no red↔green without the fix; the repro runs on the current target and
  the human verifies in the GUI at sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds the interface repro under `engine/interface/` (testbed mount, not the
  gramps package) → no POTFILES change. If a core `.py` test is added, register it per doc 16.
- **Prior-art check (triage cycles):** searched on maintenance/gramps61 — `ManagedWindow.close()`
  (`managedwindow.py:591`) cascades via `close_track` with no per-child dirty guard;
  `EditPrimary.close()`/`data_has_changed()` (`editprimary.py:244,267`) guard only the direct close;
  `EditFamily.__do_save` (`editfamily.py:1226`) has no open-child guard. Editors are non-modal
  (`editprimary.py` `ManagedWindow.__init__` without `modal=True`). No fix in git history.
- **Mantis:** 7924
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a draft PR MAY
happen during the cycle (useful for CI). The PR MUST NOT be marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Manual GUI verification on patched gramps-6.1 revealed the fix has a sequencing bug: ManagedWindow.close() sets self.opened=False and calls _save_position()/_save_size() before calling close_track(), so by the time the child's SaveDialog fires during the cascade the parent GTK container is already partially destroyed. Symptoms observed: (1) the "Save Changes?" dialog rendered only as an outline with no usable content; (2) clicking Cancel crashed with AttributeError: 'NoneType' object has no attribute 'serializer' in editsecondary.py:139 (self.db already None); (3) "Missing item from window manager [0, 1]" warning confirmed the window tree was left in an inconsistent state. The approach (veto the cascade at the child save-guard) is correct but the parent must not begin its own teardown before the child veto is resolved — the sequence in ManagedWindow.close() needs to be reordered so the child-veto check runs before any self state is mutated.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: Second failed Do iteration. v1: SaveDialog rendered as empty outline, crashed on Cancel (self.db already None). v2: SaveDialog renders but Save button has no effect — data still lost with a misleading prompt. The plan approach (route cascade through EditPrimary save-guard before parent state mutation) is correct but two builder attempts have failed on the sequencing. Update brief.md to specify a stronger model for the next Do attempt; carry forward both iteration findings so the builder understands the sequencing constraint fully before attempting again.
- Failing gate: C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) (advisory) — run-verify-interface.sh: /home/eddie/gramps/gramps-6.1-lane2 has uncommitted or untracked changes — refusing to patch it
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
