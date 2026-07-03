# Preserve child-editor references when a parent editor is confirmed

## Root cause

Primary editors are non-modal, so a parent editor (e.g. `EditFamily`) and a child
primary editor it spawned (e.g. `EditPerson`, opened via "Add a new person as the
mother") can be open at once. The child's handle is written onto the parent **only** by
the child's completion callback (`EditFamily.new_mother_added`
— `gramps/gui/editors/editfamily.py:973`), which runs when the *child* saves.

Confirming the *parent* first runs `EditFamily.__do_save`
(`gramps/gui/editors/editfamily.py:1226`): it reads `get_mother_handle()`
(`:1299`) — still `None`, because the child never saved — and commits the family
**without** the mother, *before* `_do_close()` (`:1344`) tears the child down. The
reference is lost at commit time, not teardown: even choosing "Save" on a later prompt
writes the mother handle onto a family object that was already committed. Result: the
person is saved but orphaned, the family has no mother (Mantis 7924).

## Fix

Resolve open dependent child editors in the **shared** `EditPrimary` save path, *before*
the parent reads its references and commits:

- Route every parent save door through one guard, `_save_with_dependent_children`: both
  the OK button (`define_ok_button`) **and** the window-X / Cancel → "Save Changes?" path
  (`close()`). Covering only the OK button would leave the close/Save door committing an
  incomplete graph.
- `_resolve_dependent_children` collects the open child `EditPrimary` instances that carry
  a completion callback (`callback is not None`) — the sign that the child writes a handle
  back onto the parent. A child opened to edit an *existing* object
  (`EditFamily.edit_person` — no callback) writes nothing back and is left alone, so the
  common case is unchanged.
- Each such child is resolved via its own "Save Changes?" guard (the existing `SaveDialog`
  and completion-callback machinery — no new UI). Whether the parent may proceed is read
  from `child.opened` *after* the attempt: a saved/discarded child closes; a Cancel or a
  validation error leaves it open, and the parent save aborts (nothing committed).
- The "which children, in what order" decision is extracted to a new pure module,
  `gramps/gui/savecascade.py`, free of any GTK import so it is unit-testable headless. It
  walks the `GrampsWindowManager` window tree and returns children **deepest-first**, so a
  nested Place → enclosing-Place chain resolves innermost first and each callback has
  landed before its parent reads references. The live save path drives the identical
  functions on the real tree.

## Verified against

- `gramps/gui/editors/editfamily.py:950` — `add_mother_clicked` opens `EditPerson` **with**
  the `new_mother_added` callback (a child that writes a reference back), vs
  `gramps/gui/editors/editfamily.py:1095` — `edit_person` opens `EditPerson` with **no**
  callback (correctly *not* resolved: the over-trigger guard).
- `gramps/gui/editors/editfamily.py:1299,1344` — the family is committed reading
  `get_mother_handle()` *before* `_do_close()`, confirming the loss is at commit time.
- `gramps/gui/editors/editprimary.py` — `define_ok_button` and `close()` are the two save
  doors; both now route through `_save_with_dependent_children`. New methods:
  `_resolve_dependent_children`, `_is_unresolved_dependent_child`,
  `_resolve_before_parent_commit`.
- `gramps/gui/managedwindow.py:143` (`get_item_from_track`) and `:192` (`recursive_action`)
  — the window-tree shape `savecascade` walks (deepest-first, head excluded).
- `po/POTFILES.skip` — registers the new `savecascade.py` module and its test (no
  translatable strings).

## Test

`gramps/gui/test/savecascade_test.py` — 13 headless unit tests over the extracted decision
(`descendant_leaves`, `children_to_resolve`): leaf/branch handling, deepest-first ordering,
and the selection predicate including the callback-filtering guard (a dirty child without a
pending reference is not force-resolved). They drive the same functions the live save path
calls, not a copy. All pass with the fix; the full core unit suite passes with no new
failures.

The database end-state — after adding a family, adding a new mother, typing a name, and
clicking the Family OK, the committed family's `mother_handle` resolves to the created
person — is exercised by an AT-SPI/dogtail reproduction of the reporter's flow; without the
fix the family commits with `mother_handle == None` and the person is orphaned.

Fixes #7924
