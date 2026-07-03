# Adversarial review — issue 7924 (child-editor-reference-lost-on-parent-save)

Lens: refute the red→green evidence and the reviewer's verdict; find the input that
breaks the fix. Grounded on the target source at `/home/eddie/gramps/gramps`
(clean @ `aef9f35ec6`; patch **not** applied, so the added methods are cited from
`patch.diff` and every production call-site they depend on is cited from the target tree).

## Findings

- **NEEDS-HUMAN — The fix re-opens the exact #7924 defect on the child's save-validation path.**
  `patch.diff` `_resolve_before_parent_commit._save` sets `outcome["proceed"] = True`
  **before** calling `self.save()` (patch.diff lines 102–104 → post-patch
  `gramps/gui/editors/editprimary.py`). But the child's `save()` has early returns that
  neither commit nor run the completion callback: `EditPerson.save`
  (`gramps/gui/editors/editperson.py:919-929` empty-object, `:949-962` duplicate Gramps ID)
  re-enables its OK button and `return`s **without** reaching `self.callback(self.obj)`
  (`editperson.py:984-986`) — so `new_mother_added` never fires and
  `family.obj` keeps `mother_handle == None`. Concrete flow: add-new-mother, give the person
  a Gramps ID that already exists (or leave it empty), click the **Family** OK, click **Save**
  in the child's "Save Changes?" prompt. The child's ErrorDialog fires, the person editor
  stays open and uncommitted, yet `_resolve_before_parent_commit` returns `True`, the loop
  proceeds, and `_ok_function` commits the Family with `mother_handle == None` — then the
  Family's `_do_close`→`close_track` force-tears-down the still-open orphaned person editor.
  This is precisely the outcome the brief declares "must be impossible" (brief.md:30-31).
  The same hole exists for a nested child that is itself a Family
  (`EditFamily.__do_save` early returns at `editfamily.py:1242-1265`).

- **NEEDS-HUMAN — `interface.dont-ask` silently restores the buggy behaviour for a large user population.**
  `_resolve_before_parent_commit` returns `True` at its first line when
  `config.get("interface.dont-ask")` is set (patch.diff line 94), **without** driving the
  child's save or callback. `SaveDialog` writes that global pref whenever a user ticks the
  "don't ask" box on *any* editor's close prompt (`gramps/gui/dialog.py:93`). So any user who
  has ever enabled it gets today's silent, unwarned data loss: Family committed with
  `mother_handle == None`, child discarded. The patch's docstring frames this as an accepted
  "opt-out (the pre-existing behaviour)", but the Design invariant is stated unconditionally
  — "**no** primary editor may persist an object that references a handle an open child editor
  was still preparing" (brief.md:136-139) — and the success criterion's "one outcome that
  must be impossible" (brief.md:30-31) is, in fact, still reachable. Human must adjudicate
  whether this carve-out is acceptable.

- **NEEDS-HUMAN — The asserted red→green proof is unverifiable from this bundle, and C5's "pass" cannot be corroborated.**
  `patch.diff` ships **no** test (no `*_test.py`, no `engine/interface/*` file); the repro is
  described as a testbed-mounted AT-SPI/dogtail interface test outside the bundle
  (brief.md:64-70). `check-gates.json` C4 is therefore `unverifiable`
  ("patch ships no core test … C4 red/green cannot run locally") yet `overall: pass`. C5
  reports `pass` with `path_line: "added test(s) import the production package 'gramps'"` —
  but there is **no added test in `patch.diff`** for that claim to describe, so it is
  unverifiable here and must not be read as evidence the production save path is exercised.
  Compounding the risk: the brief itself sanctions `skipTest` "where the full GUI drive cannot
  run headless" (brief.md:178-180); on a headless CI runner the sole repro would **skip**,
  making a green a non-signal rather than a genuine pass. No red→green was actually run.

- **The deepest-first snapshot ordering holds — attempted to refute, could not.** I traced
  `get_descendant_windows`/`_collect_windows` (patch.diff, `gramps/gui/managedwindow.py`
  additions) against the real tree structure (`add_item`/`get_item_from_track`,
  `managedwindow.py:143-148, 247-281`): editors are branches (`submenu_label` set), the head
  editor is `item[0]`, spawned children are `item[1:]`, and the recursion emits grandchildren
  before their parent-child head — correctly deepest-first for a Family→Person→Place chain.
  The materialised `windows` snapshot also survives the tree mutation (`close_track`→
  `remove_item`→`move_item_down`, `managedwindow.py:180-245`) that a child's save triggers,
  because it holds object references, not tracks. `self.uistate.gwm`
  (`gramps/gui/displaystate.py:477`) and `child.opened` (`managedwindow.py:588`) both exist as
  assumed. No refutation here.

- **Reentrancy of the parent OK button — attempted, likely blocked.** During
  `_resolve_before_parent_commit`, `SaveDialog.__init__` calls `self.top.run()`
  (`gramps/gui/dialog.py:87`), a recursive modal loop, so a second click on the still-sensitive
  Family OK is not delivered while the child prompt is up. I could not construct a concrete
  reentrant failure; noting the sensitive-button window only as residual surface, not a defect.

## Bottom line

Two concrete, in-scope inputs reintroduce the very defect the patch claims to eliminate
(child save-validation early-return; `interface.dont-ask` enabled), and the red→green
evidence is not runnable from the bundle. The deepest-first traversal and window-manager
wiring, by contrast, withstood attack. The first two findings are the ones a human must weigh
at sign-off.
