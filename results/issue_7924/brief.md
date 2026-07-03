# Design proposal — issue 7924 / child-editor-reference-lost-on-parent-save

> The Plan artifact for the **exception**: a change significant enough to warrant a
> GEPS-style design proposal. Authored interactively at Plan with the human. Do reads
> ONLY this file and implements it; Check runs the regular gated check on the code.
>
> **This is a re-plan.** Two prior Do iterations (preserved under `iteration-v1/` and
> `iteration-v2/`) aimed at the wrong layer (the `ManagedWindow.close()` teardown
> cascade) and failed. This proposal re-aims the fix at the **save/commit boundary** and
> raises the ambition from "warn on loss" to "preserve the reference" (Option B, the
> human's call — the full fix bamaustin's 2021 comment describes). Do MUST NOT revive the
> cascade-veto approach; see Design §"Why not the window cascade (prior attempts)".

- **Slug:** child-editor-reference-lost-on-parent-save
- **Kind:** bugfix (design proposal) — restores correct persistence behaviour for nested
  non-modal editors; escalated to a proposal because it changes the shared editor
  save-lifecycle across every spawning editor, which needs design buy-in.
- **Goal:** When a primary editor (e.g. EditFamily) is confirmed (OK) while a child
  primary editor it spawned (e.g. EditPerson opened as "add a new mother") is still open
  with unsaved data, the parent must persist a **complete, correctly-referenced** object
  graph: the child is resolved so its reference callback lands on the parent object, and
  the parent commits **with** that reference — never a parent committed with the child's
  reference silently dropped, and never the child's data silently discarded.
- **Success criterion:** Driving the reporter's flow — Relationships view → "Add a new
  family with person as parent" → in the Family editor "Add a new person as mother" → type
  a name in the Person editor → click the **Family** editor's OK — the resulting database
  state has the new person **saved AND linked as the family's mother** (the committed
  Family's `mother_handle` resolves to the new person, and the person's
  `parent`/`family` back-reference is set). Equivalently, on the abort path the family is
  **not** committed at all. The one outcome that must be impossible is today's: a Family
  committed with `mother_handle == None` while the typed person is lost or orphaned.
  Demonstrated by the committed interface repro asserting the post-flow DB references, and
  confirmed by the human in the GUI at sign-off.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core fix →
  current production maintenance branch, forward-merged to master; INTEGRATION §2).
- **Scope:** the shared primary-editor **save/commit path** must resolve open *dependent
  child primary editors* before it persists the parent's object graph. Concretely: when a
  primary editor's OK/save is invoked and it owns, in its `self.track` subtree, one or more
  open child primary editors holding unsaved data, the save must first drive each such
  child's own save so the child's registered completion callback
  (`EditFamily.new_mother_added` / `new_father_added` and the analogous callbacks in other
  editors) runs and updates the parent's working object — **then** the parent computes its
  reference set and commits the completed graph. If a child cannot be resolved (user
  cancels its Save prompt), the parent's save is **aborted** (parent stays open, nothing
  committed), so no partial graph is ever persisted. The decision + resolution must live in
  the **shared** editor machinery (`EditPrimary` / `GrampsWindowManager`), applied to every
  spawning primary editor. / **out of scope:** making primary editors modal; a new global
  dirty/modified framework; restructuring `DbTxn` transaction boundaries; the non-editor
  `ManagedWindow` subclasses (no unsaved-data notion); auto-saving without user intent
  where the child prompt already offers Save / Cancel / Close-without-saving.
- **Difficulty:** high — cross-editor change to the shared save-lifecycle: the resolve
  step touches `EditPrimary`/`GrampsWindowManager` and must remain correct for every
  editor that spawns a child (Family father/mother/child, Event reference, Place enclosure,
  Source, Repository, …) and for **nested** chains (bamaustin's Place→enclosing-Place→…
  stack). A diff-reviewer must hold the whole editor save/commit/callback interaction in
  view. Routes the stronger Do backend and deeper review (the human asked for a stronger
  model); when unsure, rated up.
- **Do model:** opus-xhigh
  <!-- pins this bundle's Do backend to the opt-in [[leaves.builder_variant]]
  model = "opus-xhigh" (opus-4-8 at --effort xhigh, #167). Value MUST stay the bare
  selector on this line. Scoped to this brief: the default builder and every other
  bundle are unchanged. -->

- **Test file:** engine/interface/test_bug_7924_child_editor_data_loss.py — a committed
  AT-SPI/dogtail interface repro in the testbed mount (NOT in `patch.diff`), subclassing
  the interface harness. It drives the flow above and asserts the **DB end-state**
  (post-OK: the committed Family's `mother_handle` resolves to the created person, i.e. the
  reference survived) — not merely "a dialog appeared". See §Design "Testable seam" — the
  resolve-before-commit decision must be a single production unit the test also drives, so
  the assertion exercises the production path, not a parallel copy.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** if the resolve-before-commit decision is extracted to a new core
  `.py` helper/module, register it in `po/POTFILES.in|.skip` per doc 16 §Adding and
  removing Python files. The interface repro lives under `engine/interface/` (testbed
  mount) → no POTFILES change for it.
- **Prior-art check (by affected path, merged + closed/rejected):** searched
  maintenance/gramps61 **and** gramps master. `EditFamily.__do_save`
  (`editfamily.py:1226`) commits the family reading `get_mother_handle()`
  (`editfamily.py:1299`) **before** `self._do_close()` (`editfamily.py:1344`) — identical
  in master (`gramps` @ `aef9f35ec6`: same `commit_family` → `_do_close` order). The child's
  handle is only written by the save callback `new_mother_added` (`editfamily.py:973-977`).
  `EditPrimary.close()`/`data_has_changed()` (`editprimary.py:244-274`) guard only a
  *direct* close. `managedwindow.py` in master has **no** `close_child_windows`/veto
  machinery — the prior iterations' cascade approach was never adopted upstream. No fix in
  git history for 7924; no open upstream PR found. Related/duplicate Mantis reports the
  reporter thread names (plain text, not linked): 3718, 12008.
- **Mantis:** 7924
- **Disposition hint:** likely-fix

## Motivation

Since 2014 (report by TJMac) users lose work when two primary editors are open at once —
the classic case: adding a new family, adding a new person as a parent from inside it, then
clicking the **Family** editor's OK instead of the Person editor's. The person window
closes and the typed data appears lost.

bamaustin's 2021 investigation (Mantis 7924, tested on 5.1.3) is the authoritative
diagnosis and reframes the bug: *"Objects are saved but **References connecting the Objects
are lost**."* The person can end up in the database, but **unlinked** — the family is saved
without the person as its mother, enclosing places lose their parent references, events
lose their place. bamaustin flags this as high-impact, hard to search for (so it breeds
duplicate reports — 3718, 12008), and needing *significant testing*; he suggests
consolidating the duplicates onto one targeted fix. That is why this is a design proposal
rather than a minimal brief, and why the human chose the full **preserve-the-reference**
outcome (Option B) over a mere warning.

## Design

### Root cause (traced on maintenance/gramps61; identical in master)

The reference is dropped **at commit time, before any window teardown** — which is why the
two prior cascade-based attempts could not fix it:

1. `EditFamily.add_mother_clicked` (`editfamily.py:937-952`) opens
   `EditPerson(self.dbstate, self.uistate, self.track, person, self.new_mother_added)` —
   the child shares the family's `track` subtree and carries a completion callback.
2. The family's `mother_handle` is written **only** when the child saves: `EditPerson`'s
   save invokes `new_mother_added(person)` → `self.obj.set_mother_handle(person.handle)`
   (`editfamily.py:973-977`).
3. Click the **Family** OK → `EditFamily.save` → `__do_save` (`editfamily.py:1226`). It
   reads `self.obj.get_mother_handle()` (`editfamily.py:1299`) — still **None**, because
   the child never saved — and commits the family **without** the mother inside the
   `Add Family` transaction (`editfamily.py:1289-1312`), then calls `self._do_close()`
   (`editfamily.py:1344`) which cascades the child windows shut.

So the family is committed incomplete *before* `_do_close()` runs. Any fix located in the
teardown path (`ManagedWindow.close()` / the `close_track` cascade) is inherently too late:
even if it prompts and the user clicks Save, `new_mother_added` mutates a family object that
is already committed and being destroyed, and is never re-committed — exactly the observed
"Save button has no effect / references lost."

### The invariant to restore (sourced)

`docs/principles.md §5`, Tier C internal, Class B (reference integrity): **"A handle
resolves or is cleaned up."** Quantified over the defect category (principle 3.2): **no
primary editor may persist an object that references a handle an open child editor was
still preparing** — the parent must complete (or abandon) the child's pending contribution
before it commits, so the committed graph never contains a silently-dropped reference and
no in-progress child data is discarded without the user's choice. This is a structural /
object-lifetime fix (principle 1.2): the target is the smallest change that restores the
invariant across the shared save-lifecycle, **not** the smallest diff.

### The approach — resolve dependent children before the parent commits

Relocate reference-completion to **before** the parent's commit, in the shared machinery:

- On a primary editor's OK/save, before it reads its reference set and opens its `DbTxn`,
  ask the shared window manager whether this editor owns open **child primary editors**
  (its `self.track` subtree, leaves that are `EditPrimary` instances) that report
  `data_has_changed()`.
- For each such child, drive its existing save-guard (the same `EditPrimary.close()` →
  `SaveDialog` path at `editprimary.py:244-261`, reusing `data_has_changed()` / `save()` —
  **no** new dirty-tracking layer). The child's own `save()` runs its completion callback
  (`new_mother_added` etc.), which updates the parent's working object with the resolved
  handle.
- After all children resolve **saved**, the parent proceeds to its existing commit block —
  now `get_mother_handle()` returns the real handle and the family commits fully linked.
- If any child is **cancelled** ("keep editing"), abort the parent save entirely: parent
  stays open, no transaction, nothing committed. Re-enable the OK button
  (`editfamily.py:1227` sets it insensitive at save entry — restore it on abort, as the
  existing error-return paths already do, e.g. `editfamily.py:1246`).
- Order within a nested chain (bamaustin's Place→enclosing-Place→…): resolve **deepest
  child first** so each level's callback has landed before its parent reads its references.

The decision belongs in `EditPrimary` (the shared save entry) and/or
`GrampsWindowManager` (which owns the `track` tree), so it covers **every** spawning
primary editor, not just `EditFamily`. Do decides the exact seam; it must be shared, not a
per-editor bolt-on.

### Testable seam (principle 3.4 — production-path, not a copy)

Extract the "does this editor have unresolved dependent child editors, and resolve them"
decision into **one** production function that the live save path calls. The interface
repro asserts the **DB end-state** after the flow (the committed Family's `mother_handle`
resolves to the created person; the person carries the family back-reference). The
production save path and the test must exercise the **same** extracted unit — do not create
a parallel headless re-implementation of the resolve logic (it would pass vacuously while
the real path stays untested; forbidden). Where the full GUI drive cannot run headless,
`skipTest` with an "infra" marker (never a false green); the reference-survival assertion is
the hard one.

### Why not the window cascade (prior attempts — do not repeat)

`iteration-v1/` made `close_track`/`recursive_action`/`close_item` veto-aware and hooked
`ManagedWindow.close()` — human GUI verification found the parent began its own teardown
(`opened=False`, `_save_position`) before the child `SaveDialog` resolved: empty-outline
dialog, `AttributeError: 'NoneType' … serializer` on Cancel, `Missing item from window
manager`. `iteration-v2/` added `close_child_windows` to resolve the child *before* parent
teardown and fixed those crashes — but "Save had no effect: data still lost," because the
family was **already committed without the mother** upstream in `__do_save` before
`close()` was ever reached. The cascade layer cannot restore a reference that was dropped at
commit time. **The v2 patch is currently left applied (uncommitted) in the
`/home/eddie/gramps/gramps-6.1` checkout — it must be reverted; the fix starts from clean
`upstream/maintenance/gramps61` and supersedes that approach entirely.**

## Alternatives considered

- **Option A — refuse-to-commit guard (rejected by the human for this cycle).** Detect the
  open dependent child and *warn / abort* the parent OK without linking. Smaller and
  restores "nothing silently dropped" (matches TJMac's "or nothing happens"), but does not
  deliver the user's intended result (family + mother saved together) and leaves the
  duplicate reports' real complaint (broken references) unaddressed. The human chose the
  full fix.
- **Per-editor guard in `EditFamily.__do_save` only.** Rejected — fixes one trigger;
  every primary editor that spawns a child has the same commit-before-child-resolve
  pattern, and it would still miss the parent's window-button close. Fails the Plan-exit
  gate (a single-module guard cannot satisfy a category-wide invariant).
- **Window-teardown cascade (both prior iterations).** Rejected on evidence — the
  reference is lost before teardown; see §"Why not the window cascade".
- **Make primary editors modal.** Out of scope; a UX regression.
- **New global dirty/modified framework.** Out of scope; the existing
  `data_has_changed()` / `SaveDialog` / completion-callback machinery is reused.

## Impact & compatibility

- **Behaviour change:** confirming a parent editor with an open, dirty child editor now
  resolves the child (its Save Changes prompt) and links the reference, instead of silently
  committing an incomplete graph. Users who currently rely on the (buggy) silent close get
  a prompt instead — this is the intended correction.
- **Reach:** the shared save path is exercised by all primary editors; the change must not
  alter the common case (no open child → identical commit path as today). Regression
  surface is every editor save — the C4 interface repro plus the T3 GUI smoke and core unit
  baseline guard against breakage; sign-off should spot-check at least Family (mother /
  father / child) and one nested Place-enclosure chain.
- **i18n:** reuses existing SaveDialog strings; any new user-facing string (e.g. if a
  chained-resolve needs its own message) goes through `_()` and POTFILES.
- **No data migration**, no settings, no public-API removal. If a new core module is added,
  register it in POTFILES (doc 16).

## Open questions

- Exact seam: resolve inside `EditPrimary.save`/a new `EditPrimary` pre-commit hook, vs a
  `GrampsWindowManager` helper the save path calls. Do chooses, keeping it shared.
- Nested-chain ordering and partial-cancel semantics: if a deep child saves but a shallower
  one is then cancelled, the parent aborts — confirm the already-saved deeper child's state
  is acceptable (it was an explicit user Save). Flag for sign-off if the flow surfaces a
  surprising intermediate state.
- Whether to also cover the `EditReference` (Event/Place reference) spawns in this same
  cycle or note them as follow-ups if the shared seam already catches them.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a draft PR
MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be marked ready
before sign-off accepts.

## Iteration 3 — carry-forward (from the previous attempt)
- Sign-off rationale: Two holes in _resolve_before_parent_commit must be fixed: 1. succeed-before-callback: do not set outcome["proceed"] = True before calling self.save(). Instead, determine success by checking child.opened after the save attempt — a successful save closes the editor (child.opened == False); a validation-abort leaves it open. Only proceed if the editor actually closed. 2. dont-ask bypass: when config.get("interface.dont-ask") is set, do not return True immediately and skip the child save. Instead, call self.save() directly (silent, no prompt) and still check child.opened — honour the pref as "save without asking", not "skip saving entirely".
- Full previous attempt preserved in `iteration-v3/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
