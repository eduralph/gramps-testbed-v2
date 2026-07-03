# Build notes — issue 7924 (child-editor-unsaved-data-lost-on-parent-save)

## Target
gramps-project/gramps @ `maintenance/gramps61`. Worktree isolation is off for this
testbed (`pdca.toml:46`), so I edited the target checkout `/home/eddie/gramps/gramps-6.1`
(detached HEAD = `upstream/maintenance/gramps61`, verified clean), captured `patch.diff`
with `git diff`, then reverted the checkout to pristine (`git checkout --`). All
`path:line` citations below are against `upstream/maintenance/gramps61`.

This is **iteration 2**. Iteration 1's *approach* (veto the cascade at the child's
save-guard) was accepted as correct in direction but **rejected on a sequencing bug**
found in manual GUI verification (see carry-forward). This iteration keeps the veto idea
but restructures `ManagedWindow.close` so the child veto is resolved **before any of the
parent's own state is mutated**.

## The carry-forward defect (what iteration 1 got wrong)

Iteration 1 made `close_track` veto-aware but left `ManagedWindow.close`
(`gramps/gui/managedwindow.py:591-608`) in its original order:

```
self.opened = False
self._save_position(save_config=False)
self._save_size()
self.uistate.gwm.close_track(self.track)   # child SaveDialog fires DEEP in here
```

`close_track` → `recursive_action` walks the **children first** and only then the parent
(`managedwindow.py:200-208`). So the child's blocking `SaveDialog` (`dialog.py:87`
`self.top.run()`) runs a nested GTK main loop **after** the parent already set
`self.opened = False` and ran `_save_position`/`_save_size`. The human observed, on the
patched 6.1 build:

1. the "Save Changes?" dialog painted as an empty outline (rendered while the parent
   window group was mid-teardown);
2. clicking Cancel crashed — `AttributeError: 'NoneType' object has no attribute
   'serializer'` at `editsecondary.py:139` (`self.db` already `None`);
3. a `Missing item from window manager [0, 1]` warning — the window tree left inconsistent.

Root cause of the *rejection*: the parent began its own teardown before the child veto
was resolved. The fix must resolve the child guard while the parent is **fully intact**.

## Root cause of the bug itself (unchanged, re-traced on target)

The window group is torn down through the manager cascade, and the cascade's per-child
teardown *ignores* the child editor's save-guard veto:

- `ManagedWindow.close()` → `self.uistate.gwm.close_track(self.track)`
  (`managedwindow.py:603`).
- `close_track` → `recursive_action(item, close_item)` → `remove_item`
  (`managedwindow.py:180-190`).
- `close_item` (`managedwindow.py:210-219`):
  ```
  if item.opened:
      item.close()          # child editor's guard runs here…
  ...
  if item.get_window():
      item.get_window().destroy()   # …but the window is destroyed regardless
  ```

For a child that is an `EditPrimary` editor (`EditPerson` opened from
`EditFamily.add_mother_clicked` with the family's `self.track`, `editfamily.py:950-951`
— so the person is a child leaf of the family branch), `item.close()` **is**
`EditPrimary.close()` (`editprimary.py:244-261`):

```
if not config.get("interface.dont-ask") and self.data_has_changed():
    SaveDialog(..., self._do_close, self.save, parent=self.window)
    return True          # dialog shown
else:
    self._do_close()
```

`SaveDialog` (`dialog.py:62-96`) is blocking. Its three buttons map to responses via
`dialog.glade:1046-1050`: **Close without saving** = `NO`(-9) → `task1` = `_do_close`;
**Cancel** = `CANCEL`(-6) → **neither** task; **Save** = `YES`(-8) → `task2` = `save`. So
on **Cancel** the editor is *not* closed — `item.opened` stays `True`. The direct-close
path honours that (the editor stays open). **The bypass:** the cascade's `close_item`
never checks the veto and calls `get_window().destroy()` anyway — discarding the child's
unsaved edits without acknowledgement. That is exactly the invariant the brief names.

`EditFamily.__do_save` (`editfamily.py:1226-1347`) commits the family, then calls
`self._do_close()` (`editfamily.py:1344`) → the cascade above. It has no open-child guard;
the durable fix belongs in the shared cascade so **every** parent is covered.

## Fix — smallest change that restores the invariant, with correct sequencing

`gramps/gui/managedwindow.py`, four coupled edits (reuses the existing
`EditPrimary.data_has_changed()`/`SaveDialog` guard — no new dirty-tracking layer, per
the brief's Difficulty note):

1. **New `GrampsWindowManager.close_child_windows(track)`** (added after `close_item`,
   `managedwindow.py:230` region). Closes **only the children** of the item at `track`
   (`item[1:]`), leaving `item[0]` (the parent itself) untouched, each via `close_item`
   (so each child routes through its own save-guard). Returns `True` if any child vetoes.
   This is the key to the sequencing fix: it lets `ManagedWindow.close` resolve child
   vetoes **before** mutating parent state, and it never touches the parent, so it cannot
   re-enter the parent's own `close()`.

2. **`close_item`** (`managedwindow.py:210`): after `item.close()`, re-check
   `item.opened`. If still open, the editor's own guard vetoed (Cancel) → return `True`,
   and do **not** tear the window down. Keying on `item.opened` (not `close()`'s return
   value) is deliberate: `EditPrimary.close` returns `True` even on Save/Close-without-
   saving (it always `return True` after showing the dialog), but there `_do_close`
   already ran and set `opened = False`. Only a genuine Cancel leaves `opened == True`.

3. **`recursive_action`** (`managedwindow.py:192`): propagate the veto — stop the walk and
   `return True` if a child `func` vetoes; otherwise `return func(...)`. (Previously it
   discarded return values.)

4. **`ManagedWindow.close`** (`managedwindow.py:591`): call
   `self.uistate.gwm.close_child_windows(self.track)` as the **first** action after the
   already-closed guard, **before** `self.opened = False` / `_save_position` /
   `_save_size` / `close_track` / `clean_up`. If it vetoes, `return True` immediately —
   the parent is fully intact, nothing mutated, both windows stay open. If it does not
   veto, the original sequence runs unchanged: `opened=False`, save geometry (window still
   alive), `close_track` (now only closes the parent + already-closed children, all
   no-ops), `remove_item`, `clean_up`.

### Why this fixes the carry-forward sequencing bug
The child's `SaveDialog` now runs inside `close_child_windows`, i.e. **before** the parent
sets `opened=False` or saves geometry or cleans up. The parent window group is fully
intact when the dialog paints → no empty-outline render. On Cancel we `return True` with
zero parent-state mutation → no half-torn-down window, no `NoneType … serializer` crash,
no `Missing item from window manager` inconsistency. The reorder is the whole point of
iteration 2.

### Why `close_child_windows` and not just reordering `close_track`
`close_track` closes the parent's children **and** the parent itself (`item[0]`) in one
recursive pass. The parent (`item[0]`) is closed by `close_item` calling
`item.close()` — which is *this same* `ManagedWindow.close`. The pre-existing
`self.opened = False` set *before* `close_track` is what stops that from recursing
infinitely (when the cascade reaches `item[0]`, `close_item`'s `if item.opened` is
`False`, so it skips `item.close()` and just destroys the window). So I cannot simply move
`close_track` ahead of `opened=False` — that would re-enter `close()` on the parent and
either recurse or destroy the parent before `_save_size` reads `self.window.get_size()`
(`managedwindow.py:633`), crashing on `None`.

Splitting the **children-only** close (`close_child_windows`, veto-resolving, parent
untouched) out of the **parent** close (`close_track`, unchanged) is the minimal structure
that lets the veto resolve first while preserving the recursion guard. After
`close_child_windows` runs, each non-vetoing child has already removed itself from the
tree via its own `close()` → `close_track` → `remove_item`, so the subsequent
`close_track(self.track)` finds no live children and just tears down the parent — identical
net behaviour to today for the no-veto case.

### Why all four edits, not fewer
The veto must be *detected* (2), *propagated up the recursion* (3), *collected across the
children without touching the parent* (1), and *acted on before the parent mutates its own
state* (4). Drop any one and you regress: e.g. detecting the veto but still letting
`ManagedWindow.close` proceed leaves a dangling child window under a torn-down parent — the
very state iteration 1 produced. Per `docs/principles.md §1.2/§2` the target is the
smallest change that **restores the invariant**, not the smallest diff.

### Regression safety of the return-value change
`recursive_action` has three call sites (`git grep` → `managedwindow.py:185, 201, 237`):
the cascade (`close_track`, return ignored — fine, children are already resolved by
`close_child_windows` before `close_track` runs, so no child ever vetoes here), the
internal recursion (201, now veto-aware), and `remove_item`'s `move_item_down`
(237). `move_item_down` returns `None` (`managedwindow.py:241-245`), so the new
`if self.recursive_action(...): return True` never early-exits there — `remove_item`
behaviour is unchanged.

Other `close()` overrides reachable via the cascade return falsy: `EditReference.close`
(`editreference.py`), `EditSecondary.close` (`editsecondary.py:142-146`) — both fall
through to `None`. Only `EditPrimary.close` returns truthy, and the fix keys off
`item.opened`, not the return value, so a non-editor window is torn down exactly as before.
`ManagedWindow.close` still returns falsy on a normal close (delete-event default destroy
proceeds) and returns `True` only on a genuine veto (keep the window) — the correct
delete-event contract.

### Multi-child edge case (no silent loss)
If a parent has several open child editors, `close_child_windows` closes them in tree
order and stops at the first veto. Any child destroyed before that veto either had no
unsaved data or the user explicitly chose Save/Close-without-saving on *its* prompt — so
no unsaved data is discarded without acknowledgement. The invariant ("no unsaved
primary-editor data discarded without a prompt, regardless of which window triggers the
close") holds. In the common single-child case (person is the family's only open child)
there are no earlier siblings at all.

## Alternatives considered and rejected

- **Iteration-1 approach unchanged (veto-aware `close_track` only, no reorder)**:
  rejected — it *is* the rejected attempt. Its `ManagedWindow.close` mutates parent state
  (`opened=False`, `_save_position`, `_save_size`) before the child `SaveDialog` resolves,
  producing the empty-outline dialog + `serializer` crash the human found. Concrete
  delta vs this iteration: iteration 1 changed 3 methods and left `close()`'s statement
  order intact; this iteration adds 1 method (`close_child_windows`, ~15 lines) and moves
  the child-close to be the first statement of `close()`. The extra method is the cost of
  correct ordering, not optional polish.
- **Guard in `EditFamily.__do_save` only** (open-child check before `_do_close`):
  rejected — fixes one trigger. Every primary editor that can spawn a child editor has the
  same cascade, so the guard belongs in the shared `GrampsWindowManager`. Cost of the
  per-editor alternative: the same open-child check duplicated into each `__do_save`
  (`EditFamily`, `EditPerson`, `EditEvent`, `EditPlace`, `EditSource`, `EditRepository`,
  … ≈6+ editors — one added block per editor, ~8 lines each ≈ 50 lines) and it would
  *still* miss the direct parent-close cascade (closing the parent by its window button,
  not OK). The single shared-cascade fix (~40 diff lines) is smaller in reach-per-line and
  complete. The brief's Invariant is explicitly category-wide.
- **Make primary editors modal**: explicitly out of scope (brief Scope) and a UX
  regression.
- **A new global dirty/modified framework**: out of scope; the existing
  `data_has_changed()`/`SaveDialog` guard already exists and is reused.

## Test — `engine/interface/test_bug_7924_child_editor_data_loss.py`

The committed AT-SPI/dogtail interface repro (testbed mount, **not** in `patch.diff`, per
the brief's "Test file" designation) is unchanged and remains the correct red→green for
this fix. It drives the brief's exact flow: Relationships view → Home → "Add a new family
with person as parent" → "Add a new person as the mother" → type a given name (child now
dirty) → click the **Family** editor's **OK** → on the "Save Changes?" prompt choose
**Cancel**.

Discriminating assertion: after Cancel, the **Person editor must still be open**.
- Unpatched: `close_item` destroys the child window regardless of the veto → the Person
  editor vanishes → assertion FAILS (the #7924 symptom). RED.
- Patched: `close_child_windows` resolves the veto with the parent intact and
  `ManagedWindow.close` returns early → the Person editor stays open → PASS. GREEN.

The **Cancel** choice is the essential discriminator: the "Save Changes?" prompt appears
in *both* versions (the cascade already calls `close()`), so merely asserting "a prompt
appeared" would pass vacuously on unpatched code. Only cancelling and checking the child
survived distinguishes the fix. With iteration 2 the prompt also renders correctly and
Cancel no longer crashes (the sequencing fix), so the assertion is now reachable rather
than aborting mid-flow. Navigation steps that can't be driven in the headless session
`skipTest` with an "infra" marker (never a false-positive bug); only the invariant is a
hard assertion.

## Verification status — automated interface red/green NOT run here; human GUI sign-off expected

This behaviour is irreducibly GUI/display-bound: a non-modal parent editor + a non-modal
child editor + a blocking modal `SaveDialog` running inside the window-manager cascade.
There is no honest **headless** unit that can exercise the *production* path end-to-end —
it needs real `EditFamily`/`EditPerson`/`SaveDialog` windows and the AT-SPI event loop. I
did **not** manufacture a headless stand-in / mock re-implementation of the cascade (that
would pass vacuously and leave the real path untested — forbidden). Restructuring the fix
into an import-light unit is not applicable: the defect *is* the interaction of the modal
dialog's nested main loop with the window teardown order, which only manifests under a
real display.

The project's GUI verifier is `engine/scripts/ubuntu/run-verify-interface.sh` (the
`C4-verify-interface` gate). The `gramps-testbed:ubuntu-6.1.0` image IS built in this
environment, but `docker run` requires interactive approval in this sandboxed Do session,
so I could not execute the two-launch red→green here. This is the sanctioned path per the
brief ("PDCA-UNVERIFIABLE for the automated red/green … the human verifies in the GUI at
sign-off") — the row routes to §6 NEEDS-HUMAN under the C6 accept-guard, **and** Check's
own `C4-verify-interface` gate re-runs the repro (image present) as part of sign-off.

The patch was checked mechanically here:
- `git apply --check` clean against `upstream/maintenance/gramps61`.
- The modified file parses (`python3 -c "import ast; ast.parse(...)"` → OK).
- No line in the edited regions exceeds 88 cols (black's default); the edits are comment
  lines + simple statements + one small method, matching the file's existing style. black
  is not installable in this sandbox (no network), so formatting was matched by hand and
  verified against the 88-col limit; black does not reflow comments, so the added comment
  blocks are stable under it.

### Manual validation steps (for sign-off)
1. Build/run gramps on `maintenance/gramps61` (or run the interface gate:
   `PDCA_BUNDLE=results/issue_7924 ./engine/scripts/ubuntu/run-verify-interface.sh`).
2. Relationships view → select a person (Home) → "Add a new family with person as parent".
3. In the Family editor → "Add a new person as the mother"; type a given name in the
   Person editor. Do **not** click the Person editor's OK.
4. Click the **Family** editor's **OK**.
5. On the "Save Changes?" prompt: the dialog must render fully (not an empty outline);
   click **Cancel**.
   - Expected (fixed): the Person editor stays open with the typed name intact; no crash,
     no `Missing item from window manager` warning on the console.
   - Bug (unpatched): the Person editor closes and the typed name is lost.
6. Re-run choosing **Save** and **Close without saving** on the prompt to confirm those
   paths still close the child correctly (no dangling window, no orphaned tree entry, and
   the family still saves).

## POTFILES
The patch modifies an existing file only (`gramps/gui/managedwindow.py`); it adds/removes
no `.py` in the gramps package. The interface repro lives under `engine/interface/`
(testbed mount, not the gramps package). So no `po/POTFILES.in` / `POTFILES.skip` change
is required (T2-potfiles N/A). Doc 16 §Adding/removing Python files: not triggered.
