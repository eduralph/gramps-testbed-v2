# build-notes.md — issue 7924 / child-editor-reference-lost-on-parent-save

Builder rationale (for the human; withheld from the reviewer). Target:
`gramps-project/gramps` @ `maintenance/gramps61` (checkout `gramps-6.1`, tip of
`upstream/maintenance/gramps61`).

## What the fix does

Relocates reference-completion to **before** the parent commits, in the *shared*
primary-editor machinery, exactly as the design proposal directs — not a per-editor
bolt-on and not the rejected window-teardown cascade.

- **New pure module `gramps/gui/savecascade.py`** — the "which open child windows must a
  parent editor resolve before it commits, and in what order" decision, free of any GTK
  import. `descendant_leaves(item)` walks the `GrampsWindowManager` window tree
  (branch = list, head = `item[0]`, leaf = non-list) returning the spawned leaves
  **deepest-child-first**; `children_to_resolve(item, predicate)` filters them. This is the
  "testable seam": the live save path drives the very same functions on the real tree.

- **`EditPrimary` (`gramps/gui/editors/editprimary.py`)** — every save door now routes
  through `_save_with_dependent_children`, which resolves open dependent child editors
  first and aborts the parent save if any child is left unresolved:
  - `define_ok_button` connects the OK button to the guard (was: straight to `self.save`).
  - **`close()` routes its `SaveDialog` "Save" callback through the guard too** — this
    closes the adversary's confirmed hole: closing the parent with the window-X or Cancel
    and choosing *Save* previously bypassed the resolve step and committed the parent with
    the child's reference dropped (the #7924 defect via a second door).
  - `_is_unresolved_dependent_child(window)` selects an open child **that carries a
    completion callback** (`callback is not None`) — the over-trigger fix: a child opened
    to edit an *existing* object (`EditFamily.edit_person`, no callback) writes nothing back
    onto the parent, so it is left alone and the common case is unchanged. (Adversary's
    concrete regression: editing an existing father then confirming an unrelated family
    edit no longer force-resolves that edit.)
  - `_resolve_before_parent_commit()` drives the child's own "Save Changes?" guard (reusing
    the existing `SaveDialog`), then reads **`self.opened` AFTER the attempt** to decide
    success — a saved/discarded child closes, a Cancel/validation-abort stays open. Under
    `interface.dont-ask` it saves silently ("save without asking"), never skips the save
    (skipping would revive the defect for dont-ask users).

## Why this shape

- The parent's `save()` is reached by BOTH the OK button and the `close()`→SaveDialog path,
  so intercepting a single door is insufficient — the guard is wired to both.
- `callback is not None` is the precise signal that distinguishes "add a new mother"
  (`EditPerson(..., self.new_mother_added)`) from "edit existing person"
  (`EditPerson(..., person)` — no callback), so only children whose save lands a reference
  on the parent are resolved.
- Deepest-first ordering matches `GrampsWindowManager.recursive_action`, so in a nested
  chain each level's callback has landed before its parent reads its references.

## Tests & verification

- **`gramps/gui/test/savecascade_test.py`** (unit, headless): 13 tests over
  `descendant_leaves` / `children_to_resolve` on fabricated window trees — leaf/branch
  handling, deepest-first ordering, and the selection predicate including the new
  **callback-less child is skipped** case (over-trigger guard). Drives the SAME production
  functions the live path calls (imported, not re-implemented).
  - **Verified GREEN in the Docker engine image** (`gramps-testbed:ubuntu-6.1.0`): 13/13.
- **`engine/interface/test_bug_7924_child_editor_data_loss.py`** (AT-SPI/dogtail, testbed
  mount): the DB-end-state repro — Relationships → add family → add mother → type a name →
  click the Family OK → *Save* → assert the new person shows as the active person's partner
  (i.e. `mother_handle` survived). The reference-survival oracle.
- **Full core unit suite**: 32977 tests, the same 7 pre-existing baseline failures as the
  clean checkout (zip imports + WebCal/NarrativeWeb — unrelated to this diff). **Zero new
  regressions.**

## Verification status / NEEDS-HUMAN

- The pure decision unit (ordering/selection incl. the over-trigger guard) is proven
  headless. The GUI *wiring* (`_save_with_dependent_children`, the close-door guard, the
  `opened`-post-check, the dont-ask branch) is exercised by the dogtail interface repro,
  which is irreducibly GUI-driven; per the brief it may land PDCA-UNVERIFIABLE and the human
  confirms the reference survives in the GUI at sign-off. Spot-check at sign-off: Family
  mother/father, and closing the parent with the window-X → *Save* (the door this iteration
  fixed).
- **EditReference-spawned children remain out of the predicate** (it requires
  `isinstance(window, EditPrimary)`). The nested Place→enclosing-Place enclosure editor is
  an `EditPlaceRef` (`EditReference`), so a dirty enclosure editor is not auto-resolved.
  The Success criterion (Family + mother) and every primary→primary spawn ARE covered;
  extending to `EditReference` is a scoped follow-up the human should confirm or defer
  (brief §Open questions). A genuine judgment call, not a defect in the shipped scope.

## Citations (maintenance/gramps61)

- `gramps/gui/editors/editprimary.py` — `define_ok_button`, `_save_with_dependent_children`,
  `_resolve_dependent_children`, `_is_unresolved_dependent_child`,
  `_resolve_before_parent_commit`, and the `close()` SaveDialog callback.
- `gramps/gui/editors/editfamily.py:950-952` (`add_mother_clicked` → callback) vs `:1095`
  (`edit_person` → no callback); `:973-983` completion callbacks.
- `gramps/gui/managedwindow.py:143-148` (`get_item_from_track`), `:192-208`
  (`recursive_action` tree shape).
- `po/POTFILES.skip` — register the new `savecascade.py` and its test (doc 16).
