# check-advisory-adversary.md — issue 7924 (iteration 3 patch)

Skeptic's pass. Grounded on `$PDCA_TARGET` = `/home/eddie/gramps/gramps` @ `aef9f35ec6`.

## Refutations

- **Concrete failing case — the fix guards only ONE of the parent's save doors.** The patch
  intercepts the OK button (`define_ok_button` → `_save_with_dependent_children`), but the
  parent editor's *close* path saves too: `EditPrimary.close()` at
  `gramps/gui/editors/editprimary.py:244-257` hands **`self.save` directly** to its
  `SaveDialog`, and both the window-manager X (`gramps/gui/managedwindow.py:513`,
  `delete-event` → `self.close`) and the Cancel button
  (`gramps/gui/editors/editprimary.py:184`) route there. Failing case: run the reporter's
  exact flow, but instead of clicking the Family OK, close the Family editor with the
  title-bar X (or Cancel) and choose **Save** in the prompt → `EditFamily.save` →
  `__do_save` reads `get_mother_handle()` (`gramps/gui/editors/editfamily.py:1295`) with the
  dirty child EditPerson still open → family committed with `mother_handle == None` — the
  precise outcome the brief's Success criterion says "must be impossible". The brief itself
  rejected a per-entry-point guard because it "would still miss the parent's window-button
  close" (brief §Alternatives); this patch has exactly that hole.

- **The red→green evidence does not exist.** `check-gates.json` C4 (gating) is **fail** —
  `run-verify.sh` never ran ("core worktree /home/eddie/gramps/gramps-6.1-lane1 missing"),
  and T3 is fail with "runner exited 1 producing NO JUnit XML — a pre-test crash". So there
  is no demonstration that the interface repro is red pre-fix or green post-fix, and no
  whole-suite regression signal. The only test **in the diff**
  (`gramps/gui/test/savecascade_test.py`) is green-by-construction: it tests a module that
  did not exist pre-fix, on fabricated `FakeWindow` trees — it can never have been red
  against the defect. Any "fix verified" claim in the review is unwarranted on this bundle.

- **C5 "test exercises the production path" passed on a vacuous criterion.** The gate only
  checked that "added test(s) import the production package 'gramps'". In substance,
  `savecascade_test.py` re-implements the selection predicate as `_needs_resolving`
  (patch, savecascade_test.py — "Predicate mirroring the production one, over FakeWindow
  facts") instead of driving the production
  `EditPrimary._is_unresolved_dependent_child`, and nothing in the diff exercises
  `_save_with_dependent_children`, `_resolve_before_parent_commit`, the `opened`
  post-check, or the dont-ask branch — i.e. exactly the wiring that failed sign-off in
  iterations 1–3 has **zero** automated coverage; only the trivial tree-walk is tested.
  This is the brief §"Testable seam" mirrored-copy pattern applied to the predicate half of
  the decision.

- **NEEDS-HUMAN — the nested Place-enclosure chain named in the brief is NOT covered.**
  `_is_unresolved_dependent_child` requires `isinstance(window, EditPrimary)`, but the
  Place → enclosing-Place chain runs through `EditPlaceRef`, which is an `EditReference`
  (`gramps/gui/editors/editplaceref.py:63`), not an `EditPrimary` — so a dirty enclosure
  editor open under an EditPlace is skipped and the place still commits with the enclosure
  reference dropped. The brief left EditReference coverage as an open question "if the
  shared seam already catches them" — it does **not** catch them, and the brief's sign-off
  instruction to "spot-check … one nested Place-enclosure chain" (brief §Impact) should be
  expected to FAIL. A human must decide: follow-up issue, or this cycle.

- **NEEDS-HUMAN — `interface.dont-ask` semantics are inverted relative to the existing
  guard, and auto-commit without user intent results.** Existing behaviour: with dont-ask
  set, `EditPrimary.close()` (`gramps/gui/editors/editprimary.py:247`) skips the prompt and
  **discards**. The patch's `_resolve_before_parent_commit` makes dont-ask mean silent
  **save-and-link** of the child. The iteration-3 sign-off note mandated this, but it
  collides with the brief's out-of-scope clause ("auto-saving without user intent where the
  child prompt already offers Save / Cancel / Close-without-saving"): a dont-ask user who
  opened "add mother", typed exploratory junk, and clicks Family OK gets that junk person
  silently committed AND linked as mother. Note also the same checkbox drives both:
  `SaveDialog` writes `config.set("interface.dont-ask", …)` on every response
  (`gramps/gui/dialog.py:93`), so ticking "don't ask" during a child-resolve prompt makes
  future direct closes silently *discard* while future parent-OK resolves silently *save*
  — one preference, opposite outcomes. Spec conflict between brief and sign-off rationale;
  human must adjudicate.

- **Over-trigger: children with no pending reference are force-resolved.** The predicate
  flags **any** open dirty `EditPrimary` in the subtree, but e.g.
  `EditFamily.edit_person` (`gramps/gui/editors/editfamily.py:1087-1093`) opens an
  existing parent's EditPerson with **no completion callback** — its handle is already on
  the family; committing the family drops nothing. Failing case: open an existing father
  for editing from the Family editor, make a change, leave it open, click Family OK for an
  unrelated family edit → previously the family saved and the person editor stayed open;
  now the user is forced to save/discard that unrelated edit (with dont-ask: it is
  silently committed), and Cancel aborts the *family* save. The brief's Impact section
  promises "the change must not alter the common case" — this alters a common case that is
  not the defect.

## Attempted and could not refute

- Re-entrancy during the child prompt: `SaveDialog` uses `Gtk.Dialog.run()`
  (`gramps/gui/dialog.py:87`), which is modal for its duration, so the parent's
  still-sensitive OK cannot be re-clicked mid-resolve.
- The `not self.opened` success check: `ManagedWindow` flips `opened` at
  `gramps/gui/managedwindow.py:588/600`, and `EditPerson.save` reaches `_do_close()` then
  the completion callback (`gramps/gui/editors/editperson.py:983-985`) before returning, so
  save-success/validation-abort/Cancel are all correctly distinguished — the two
  iteration-3 sign-off holes (succeed-before-callback, dont-ask bypass) are genuinely fixed.
- Deepest-first ordering and branch-head handling in `savecascade.descendant_leaves`
  match the `GrampsWindowManager` tree shape (`gramps/gui/managedwindow.py:247-281`,
  branch-vs-leaf per `submenu_label`), including sub-branch heads; `config` is already
  imported in `editprimary.py:47`.
