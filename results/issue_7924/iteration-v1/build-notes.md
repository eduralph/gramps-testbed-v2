# Build notes — issue 7924 (child-editor-unsaved-data-lost-on-parent-save)

## Target
gramps-project/gramps @ `maintenance/gramps61`. All citations are against
`upstream/maintenance/gramps61` (worktree isolation is off for this testbed;
Do emits a `patch.diff`, it never mutates the target in place — `pdca.toml:46`).

## Root cause (traced on the target branch)

The window group is torn down through the manager cascade, NOT window-by-window
with each editor's own guard:

- `ManagedWindow.close()` → `self.uistate.gwm.close_track(self.track)`
  (`gramps/gui/managedwindow.py:603`).
- `GrampsWindowManager.close_track()` → `recursive_action(item, self.close_item)`
  → `remove_item(track)` (`managedwindow.py:180-190`).
- `recursive_action()` walks the branch and calls `close_item` on each leaf
  (`managedwindow.py:192-208`).
- `GrampsWindowManager.close_item()` (`managedwindow.py:210-219`):
  ```
  if item.opened:
      item.close()          # child editor's guard runs here…
  ...
  if item.get_window():
      item.get_window().destroy()   # …but the window is torn down regardless
      item.window = None
  ```

For a child that is an `EditPrimary` editor (`EditPerson` opened from
`EditFamily.add_mother_clicked`, `editfamily.py:937-952`, with the family's
`self.track` — so the person is a *child leaf* of the family branch in the
window tree), `item.close()` IS `EditPrimary.close()`
(`gramps/gui/editors/editprimary.py:244-261`):
```
if not config.get("interface.dont-ask") and self.data_has_changed():
    SaveDialog(..., self._do_close, self.save, parent=self.window)
    return True          # VETO — leave the editor open
else:
    self._do_close()
    return False
```
`SaveDialog` (`gramps/gui/dialog.py:62-96`) is *blocking* (`self.top.run()`), and
its **Cancel** button (glade `dialog.glade:918`, response `Gtk.ResponseType.CANCEL`)
runs **neither** `task1` (`_do_close`) **nor** `task2` (`save`) — see
`dialog.py:88-91`. So on Cancel the editor is *not* closed: `item.opened` stays
`True` and `close()` returns `True`.

**The bypass:** `close_item` ignores that veto and unconditionally calls
`item.get_window().destroy()`. So the direct-close path lets *Cancel* keep the
editor open (`editprimary.py:258` `return True`), while the parent's cascade
destroys the child window anyway — discarding the child's unsaved edits without
acknowledgement. That is exactly the invariant the brief names: *"the cascade
path (managedwindow.py:591-607) must not discard a dirty child without the same
prompt … it must not be bypassable via the parent's cascade."*

`EditFamily.__do_save` (`editfamily.py:1226-1344`) commits the family and its
parent handles, then calls `self._do_close()` (`editfamily.py:1344`) → the
cascade above. It has no open-child guard; the durable fix belongs in the shared
cascade so *every* parent (not just `EditFamily`) is covered.

## Fix — smallest change that restores the invariant (reuses the existing guard)

`gramps/gui/managedwindow.py`, four coupled edits (all necessary; see below):

1. **`close_item`** (`managedwindow.py:210`): after `item.close()`, re-check
   `item.opened`. If the editor is still open, its own save-guard vetoed the
   close (Cancel) — return `True` and do **not** tear the window down.
   Using `item.opened` (not `close()`'s return value) is deliberate: `EditPrimary.close`
   returns `True` even when the user picked **Save**/**Close-without-saving**
   (it always `return True` after showing the dialog, `editprimary.py:258`), but
   in those cases `_do_close` already ran and set `opened = False`. Only a genuine
   veto (Cancel) leaves `opened == True`. This is the reliable veto signal.
2. **`recursive_action`** (`managedwindow.py:192`): propagate the veto — stop the
   walk and `return True` if a child `func` vetoes; otherwise `return func(...)`.
3. **`close_track`** (`managedwindow.py:180`): if `recursive_action` vetoed, return
   without `remove_item(track)`, so the tree stays intact and the child window
   is not orphaned.
4. **`ManagedWindow.close`** (`managedwindow.py:591`): if `close_track` vetoed,
   restore `self.opened = True` and return before `clean_up()`/destroy, so the
   parent isn't half-torn-down while its child stays open.

This **reuses** `EditPrimary.data_has_changed()` / `SaveDialog` (via the existing
`close()`) — no new dirty-tracking layer, as the brief's Difficulty note requires.

### Why all four edits, not fewer
The veto must be *detected* (1), *propagated up the recursion* (2), *stop the
tree removal* (3), and *stop the parent teardown* (4). Dropping any one leaves a
partially-destroyed state: e.g. detecting the veto in `close_item` but still
running `remove_item` pops the child from `window_tree` while its live window
stays visible — a dangling, unreachable editor. There is no smaller correct set;
per `docs/principles.md §1.2/§2` the target is the smallest change that restores
the invariant, not the smallest diff.

### Regression safety of the return-value change
`recursive_action` is called in only two places (verified:
`git grep recursive_action` → `managedwindow.py:185,201,237`): the cascade (now
veto-aware) and `remove_item` with `move_item_down` (`managedwindow.py:237`).
`move_item_down` returns `None` (falsy), so the new `if self.recursive_action(...):`
never early-exits there — no behaviour change for `remove_item`.

Other `close()` overrides that the cascade may call all return `None` (falsy):
`EditReference.close` (`editreference.py:235-239`), `EditSecondary.close`
(`editsecondary.py:142-146`) — verified. Only `EditPrimary.close` ever returns
truthy, and the fix keys off `item.opened`, not the return value, so a non-editor
window is torn down exactly as before. The `delete-event` handler contract is
preserved: `ManagedWindow.close` still returns falsy on a normal close (default
destroy proceeds) and now returns `True` only on a genuine veto (keep the window).

## Alternatives considered and rejected

- **Guard in `EditFamily.__do_save` only** (add an open-child check before
  `_do_close`): rejected — it fixes one trigger. Every primary editor that can
  spawn a child editor (EditPerson→child events/places, EditFamily, etc.) has the
  same cascade, so the guard belongs in the shared `GrampsWindowManager` cascade.
  The brief's Invariant is category-wide ("regardless of which window triggers
  the close"). A per-editor guard would need duplicating into each `__do_save`
  (EditFamily, EditPerson, EditEvent, EditPlace, … — ~6+ editors), and would still
  miss the *direct* parent-close cascade. The single cascade fix is both smaller
  in reach-per-line and complete.
- **Make primary editors modal**: explicitly out of scope (brief Scope) and a UX
  regression (users open child editors intentionally alongside the parent).
- **A new global dirty/modified framework**: out of scope; the existing
  `data_has_changed()`/`SaveDialog` guard already exists and is reused.

## Test — `engine/interface/test_bug_7924_child_editor_data_loss.py`

Committed AT-SPI/dogtail interface repro in the testbed mount (NOT in
`patch.diff`), subclassing `GrampsInterfaceTestCase`. It drives the brief's
repro flow: Relationships view → Home → "Add a new family with person as parent"
→ "Add a new person as the mother" → type a given name (child now dirty) →
click the *Family* editor's **OK** → on the "Save Changes?" prompt choose
**Cancel** ("keep editing").

Discriminating assertion: after Cancel, the **Person editor must still be open**.
- Unpatched: `close_item` destroys the child window regardless of the veto →
  the Person editor vanishes → assertion FAILS (the #7924 symptom). RED.
- Patched: the veto is honoured → the Person editor stays open → PASS. GREEN.

The **Cancel** choice is the essential discriminator: the "Save Changes?" prompt
itself appears in *both* versions (the cascade already calls `close()`), so
merely asserting "a prompt appeared" would pass vacuously on the unpatched code.
Only cancelling and checking the child survived distinguishes the fix — this is a
genuine red→green, not a vacuous pass. Navigation steps that can't be driven in
the headless session `skipTest` with an "infra" marker (never a false-positive
bug); only the invariant is a hard assertion.

## Verification status — automated red/green UNVERIFIABLE here; human GUI sign-off expected

This behaviour is irreducibly GUI/display-bound: a non-modal parent editor + a
child editor + a blocking modal `SaveDialog` inside the manager cascade. There is
no honest headless (import-light) unit that can drive the *production* cascade —
`gramps/gui/managedwindow.py` imports `gi.repository.Gtk` at load and the flow
needs real `EditFamily`/`EditPerson`/`SaveDialog` windows and AT-SPI. I did **not**
manufacture a headless stand-in / parallel re-implementation of the cascade (that
would pass vacuously and leave the real path untested — forbidden).

The project's GUI verifier is `engine/scripts/ubuntu/run-verify-interface.sh`
(the `C4-verify-interface` gate, advisory). In this environment the
`gramps-testbed:ubuntu-6.1` Docker image is not built (`docker images` shows
none) and the gate runs two full GUI launches (patched + unpatched), so I could
not execute the red→green here without a heavy image build + double GUI run —
well beyond a sanity pass, and not a hand-rolled `docker run` I'm permitted to
substitute. Per the brief ("PDCA-UNVERIFIABLE for the automated red/green if the
AT-SPI repro cannot fully assert the prompt … the human verifies in the GUI at
sign-off"), this is the sanctioned path: the row routes to §6 NEEDS-HUMAN under
the C6 accept-guard.

The patch itself was checked mechanically:
- `git apply --check` clean against `upstream/maintenance/gramps61`, and applying
  it reproduces the intended source exactly (`diff` = identical).
- Modified file parses (`python3 -c "import ast; ast.parse(...)"`).

### Manual validation steps (for sign-off)
1. Build/run gramps on `maintenance/gramps61` (or run the interface gate:
   `PDCA_BUNDLE=results/issue_7924 ./engine/scripts/ubuntu/run-verify-interface.sh`
   once `make worktrees` + the ubuntu image are built).
2. Relationships view → select a person (Home) → "Add a new family with person
   as parent".
3. In the Family editor → "Add a new person as the mother"; type a given name in
   the Person editor. Do **not** click the Person editor's OK.
4. Click the **Family** editor's **OK**.
5. On the "Save Changes?" prompt, click **Cancel**.
   - Expected (fixed): the Person editor stays open with the typed name intact.
   - Bug (unpatched): the Person editor closes and the typed name is lost.
6. Re-run choosing **Save** and **Close without saving** on the prompt to confirm
   those paths still close the child correctly (no dangling window, no orphaned
   tree entry).

## POTFILES
The patch modifies an existing file only (`gramps/gui/managedwindow.py`); it adds
/ removes no `.py`. The interface repro lives under `engine/interface/` (testbed
mount, not the gramps package). So no `po/POTFILES.in` / `POTFILES.skip` change
is required (T2-potfiles N/A).

## Formatting
gramps' commit hook runs `black`. `black` is not installed on this host, so I
matched the file's existing style by hand: the edits are comment lines plus
simple statements (`if …: return True`, `return func(...)`), all within the
88-column limit and consistent with the surrounding code. black does not reflow
comments, so the added comment blocks are stable under it.
