# Build notes — issue 7924 (child-editor-reference-lost-on-parent-save)

Target: gramps-project/gramps @ maintenance/gramps61 (worktree `../gramps-6.1`,
clean upstream/maintenance/gramps61 @ 0d9e148908). This is the **re-plan** (Option B —
preserve the reference), superseding the two prior cascade-veto iterations.

## What the fix does (the seam)

The reference is dropped **at commit time, before any window teardown**
(`editfamily.py:1299` reads `get_mother_handle()` → still `None` → family committed
without the mother inside the `Add Family` txn at `editfamily.py:1289-1312`, *then*
`_do_close()` at `editfamily.py:1344`). So the fix has to run **before** the parent
reads its references — not in the teardown cascade the prior iterations targeted.

Two production changes, both in the **shared** primary-editor machinery:

1. `gramps/gui/managedwindow.py` — `GrampsWindowManager.get_descendant_windows(track)`
   + `_collect_windows` (new methods, after `get_item_from_window`, patch.diff hunk 2).
   The window manager owns the `track` tree; this returns every descendant **leaf**
   window spawned below the window at `track`, **deepest-child-first**. Pure tree walk,
   no `_()` strings.

2. `gramps/gui/editors/editprimary.py` — `define_ok_button` (`editprimary.py:178` on the
   target) no longer wires the editor's `save` straight to the OK button; it stores it as
   `self._ok_function` and connects `self._save_with_dependent_children`. That handler
   calls the new `_resolve_dependent_children()` **before** running the real save; each
   dirty descendant `EditPrimary` (deepest-first) is driven through
   `_resolve_before_parent_commit()`, which shows the *same* `SaveDialog` guard the
   direct-close path already uses (`editprimary.py:247-257`) but reports the user's choice.

Because `define_ok_button` is the single call site **every** primary editor uses (22 call
sites across the editors; all `EditPrimary` subclasses pass their `save`), the resolve step
is genuinely shared — not a per-editor bolt-on — which is what the Plan's "Invariant to
restore" (principles §5, Tier C / Class B: *"a handle resolves or is cleaned up"*) requires.

### Traced patched flow (the Success criterion, Family + mother)

1. Family OK → `_save_with_dependent_children`.
2. `_resolve_dependent_children`: `get_descendant_windows(family.track)` → `[EditPerson]`
   (the "add mother" editor); it is `EditPrimary`, `opened`, `data_has_changed()`.
3. `EditPerson._resolve_before_parent_commit` → `SaveDialog` → **Save** → `EditPerson.save`
   (`editperson.py:914`) adds the person, `_do_close()`, then `callback(person)` =
   `EditFamily.new_mother_added` (`editfamily.py:973-977`) → `family.set_mother_handle(person.handle)`.
4. Back in the wrapper → `_ok_function()` = `EditFamily.save` → `__do_save` now reads the
   **real** `get_mother_handle()` (`editfamily.py:1299`) → commits the family fully linked,
   and adds the family handle onto the mother person (`editfamily.py:1299-1303`).

Result: person **saved AND linked**; the person carries the family back-reference. On the
abort path (Cancel = "keep editing") the wrapper returns before `__do_save` runs, so the
family is never committed and the OK button (which `__do_save` is what disables) is still
sensitive — exactly the Success criterion's two acceptable end-states, and today's
"Family committed with `mother_handle == None`, person lost" is made impossible.

### Why the wrapper needs no OK-button re-sensitize on abort

The existing error-return paths (`editfamily.py:1246`, …) re-sensitize because
`__do_save` disables the button at entry (`editfamily.py:1227`). My abort happens **before**
`__do_save` runs, so the button was never disabled — nothing to restore.

### Nesting (bamaustin's Place → enclosing-Place → … chain)

Descendants are resolved **deepest-first**, so each level's completion callback has landed
on its own parent before that parent's save reads its references. The `opened` guard is
defensive: resolving a deeper child (`close_track` on that child's own track) never closes
its ancestors or unrelated branches, but the snapshot list is guarded anyway.

## Scope note / documented follow-up

`_resolve_dependent_children` filters `isinstance(child, EditPrimary)`. The named
Success-criterion flow (Family → Person mother) is entirely `EditPrimary` and fully fixed.
`EditReference` intermediaries (the Event/Place **Reference** editors in bamaustin's full
chain) are a **different** base class with their own `define_ok_button`
(`editreference.py:192`) — the brief's Open Question explicitly leaves them as a follow-up
("cover EditReference … or note them as follow-ups"). A nested `EditPlace` *under* an
`EditEventRef` is still found as a descendant **leaf** and resolved; only the reference held
by the intervening `EditEventRef` node itself is out of this cycle's scope. Flagged for
sign-off.

## Alternatives considered (with cost)

- **Per-editor guard in `EditFamily.__do_save` only** (rejected). Would add a resolve call
  at the top of each spawning editor's `save`/`__do_save` — **≈14 `EditPrimary` subclasses**
  (editfamily, editperson, editplace, editsource, editrepository, editmedia, editevent,
  editcitation, editnote, …), each an independent edit and an independent place to drift —
  versus **one** edit in `EditPrimary.define_ok_button` here. It also still misses the
  category-wide invariant (fails the "shared, not per-editor" requirement).
- **Window-teardown cascade** (both prior iterations, `iteration-v1/`, `iteration-v2/`).
  Rejected on evidence: the reference is dropped **before** teardown, so a cascade veto
  cannot restore it — v2's own GUI sign-off found "Save had no effect: data still lost."
  This patch starts from clean upstream and does **not** revive that approach.
- **Make primary editors modal / new global dirty framework.** Out of scope per the brief;
  this reuses the existing `data_has_changed()` / `SaveDialog` / completion-callback
  machinery, adding no new dirty-tracking layer.

## `interface.dont-ask`

When the user has disabled the guard, `_resolve_before_parent_commit` returns True without
prompting, so the parent's existing cascade close discards the child exactly as before — no
new prompt, no behaviour change for that opt-out. (For a *dirty* child with the guard on,
the child's `SaveDialog` **already** appears today during the cascade close; this fix merely
relocates that same prompt to *before* the commit so the reference survives — it adds no new
prompt to the common flow.)

## Test

`engine/interface/test_bug_7924_child_editor_data_loss.py` (testbed mount, **not** in
patch.diff). Rewritten from the prior iterations' cascade-veto/Cancel assertion to the
**Option B** invariant: it drives the reporter's flow, chooses **Save** on the child's
"Save Changes?" prompt, and asserts the new mother (`Zzunsavedmother`) then appears as the
active person's partner in the Relationships view — a GUI-observable proxy for the committed
family's `mother_handle` resolving to the created person. It exercises the **production**
path (the live app drives `EditPrimary._resolve_dependent_children` in-process; no parallel
copy). Every navigation step that a headless AT-SPI session cannot drive `skipTest`s with an
"infra" marker; only the reference-survival check is a hard assertion.

Red/green discriminator: both patched and unpatched present a "Save Changes?" prompt (the
unpatched one fires from the *cascade close* after the family is already committed), so the
discriminator is **not** the dialog — it is whether the link survives. Unpatched: family
committed with `mother_handle == None`, person orphaned → the name never shows as the active
person's partner → the test **FAILS** (red). Patched: linked → **PASSES** (green).

### Verification status — honest

The C4-verify-interface gate (`run-verify-interface.sh`) runs the two-launch red→green in
Docker under xvfb + D-Bus + AT-SPI. In this Do session `docker run` requires interactive
approval and the lane worktree (`gramps-6.1-lane5`) is not present, so I could **not**
execute the red→green here. Per the brief this is the sanctioned `PDCA-UNVERIFIABLE` path:
Check's own `C4-verify-interface` gate re-runs the repro at sign-off, and the row routes to
§6 NEEDS-HUMAN under the C6 accept-guard. Mechanical checks done here:

- `git apply --check` of `patch.diff` is **clean** against clean
  `upstream/maintenance/gramps61` (0d9e148908).
- Both patched modules parse (`python3 -m ast`), and the test file parses.
- No added code line exceeds 88 cols (black's default); the `SaveDialog` call carries a
  magic trailing comma so black keeps it exploded as written.

### Manual validation steps (for sign-off)

Run the gate (`PDCA_BUNDLE=results/issue_7924 ./engine/scripts/ubuntu/run-verify-interface.sh`)
or, in a live gramps on maintenance/gramps61:

1. Relationships view → select a person (Home) → "Add a new family with person as parent".
2. In the Family editor → "Add a new person as the mother"; type a given name in the Person
   editor. Do **not** click the Person editor's OK.
3. Click the **Family** editor's **OK**.
4. On the "Save Changes?" prompt choose **Save**.
   - Expected (fixed): both editors close; the new person is saved **and** shown as the
     family's mother — the family's `mother_handle` resolves to the person, and the person
     carries the family back-reference (check the Families/People views).
   - Bug (unpatched): the family is committed without a mother; the person is orphaned (or,
     in the simpler flow, never saved) — the reference is lost.
5. Re-run choosing **Cancel** on the prompt → the Family editor stays open and nothing is
   committed. Re-run choosing **Close without saving** → the family saves without the mother
   (the user's explicit choice). Spot-check father / child adds and one nested
   Place-enclosure chain (design §Impact).

## POTFILES

The patch modifies existing files only. `gramps/gui/editors/editprimary.py` is already in
`po/POTFILES.in:474`; `gramps/gui/managedwindow.py` is already in `po/POTFILES.skip:348`
(my new methods add no `_()` strings; the two reused `SaveDialog` strings already exist in
`editprimary.py`'s `close`). No `.py` file is added or removed, and the interface repro lives
under `engine/interface/` (testbed mount, not the gramps package). T2-potfiles: N/A.
