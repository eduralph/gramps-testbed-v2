# Result — issue 7924 / child-editor-reference-lost-on-parent-save

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: When a primary editor (e.g. EditFamily) is confirmed (OK) while a child
- Success criterion: Driving the reporter's flow — Relationships view → "Add a new
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core fix →
- Scope (one logical fix) / out of scope: the shared primary-editor **save/commit path** must resolve open *dependent

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style (1 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix issue 7924 so saving a parent primary editor first resolves any dirty child primary editor and commits the completed reference graph rather than dropping the child reference.

Target caveat: `$PDCA_TARGET` is readable and `git apply --check patch.diff` succeeds, but the checkout is `master` at `aef9f35ec6` while the brief targets `maintenance/gramps61`; citations for unchanged source are grounded on `$PDCA_TARGET`, and citations for added code are grounded on `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the bug, intended linked DB end-state, shared save-boundary scope, and abort-on-cancel behavior at `brief.md:18`, `brief.md:24`, `brief.md:36`, and `brief.md:43`. |
| C2 — C2 Reproduction (red pre-fix) | PASS | The red condition is re-derived from source: `EditFamily.add_mother_clicked` spawns `EditPerson` with `new_mother_added` at `/home/eddie/gramps/gramps/gramps/gui/editors/editfamily.py:946`, but `__do_save` reads `get_mother_handle()` before closing children at `/home/eddie/gramps/gramps/gramps/gui/editors/editfamily.py:1295` and `/home/eddie/gramps/gramps/gramps/gui/editors/editfamily.py:1340`. |
| C3 — C3 Change | PASS | The patch routes OK through a shared `EditPrimary` pre-save hook and adds descendant-window traversal, matching the requested shared-layer change rather than a Family-only guard (`patch.diff:17`, `patch.diff:46`, `patch.diff:126`). |
| C4 — C4 Verification (red->green) | FAIL | `git apply --check patch.diff` passes, but the bundle has no runnable red->green core/interface test in `patch.diff`, and the configured C4 gate records verification as unverifiable because no core test ships (`check-gates.json:33`). |
| C5 — C5 Causal adequacy | FAIL | The patch sets `outcome["proceed"] = True` before `self.save()` returns (`patch.diff:102`), but child saves can show an error and return without closing or firing the callback, e.g. empty or duplicate Person at `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:918`, `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:929`, and `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:962`; parent save can still proceed with the reference unresolved. |
| T1 — T1 Structure | N/A | No addon path or addon manifest is touched; the patch changes only core files under `gramps/gui/...` (`patch.diff:1`, `patch.diff:118`). |
| T2 — T2 Shape | PASS | The patch modifies existing GPL-covered Python files only, adds no new core `.py` file requiring POTFILES registration, and the configured T2 gates pass (`check-gates.json:60`, `check-gates.json:69`). |
| T3 — T3 Runtime | PASS | The recorded runtime gate matches the baseline with 7 known reds and notes only baseline tree drift, not a patch-specific runtime regression (`check-gates.json:78`). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` is in the bundle, so contribution-wrapper review does not apply (`check-gates.json:87`). |
| T5 — T5 Judgment | FAIL | The shared-hook direction is sound, but the failed-child-save path above preserves the original class of incomplete parent commits; this should not pass Check without a success signal from the child save. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: after C5 is fixed and red->green verification exists, a human must drive the GUI flow from `brief.md:24` and decide whether the observed Save/Cancel/discard behavior is acceptable for real users and nested editor chains. |

## 6 Human Decisions

1. V — Validation fitness-to-purpose: clear only after a patched build is manually driven through the reporter flow: Relationships view -> Add a new family with person as parent -> add a new mother -> enter a name -> click Family OK -> choose Save in the child prompt -> confirm the family has `mother_handle` linked to the saved person and the person has the family back-reference. Also check Cancel keeps the parent open and uncommitted, and Close without saving intentionally discards the child contribution.

## Blocking Finding

The patch does not distinguish "child save succeeded" from "child save was attempted but validation failed." In `_resolve_before_parent_commit`, `_save()` sets `outcome["proceed"] = True` before calling `self.save()` (`patch.diff:102`), but existing primary editor saves can abort after validation errors while leaving the editor open and without invoking the completion callback, as `EditPerson.save()` does for empty or duplicate records (`/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:918`, `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:929`, `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:962`). In that case the parent proceeds to commit even though the child reference never landed, which is the defect class the patch is meant to eliminate.

### Advisory — adversary

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: after C5 is fixed and red->green verification exists, a human must drive the GUI flow from `brief.md:24` and decide whether the observed Save/Cancel/discard behavior is acceptable for real users and nested editor chains.
- [ ] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): Two holes in _resolve_before_parent_commit must be fixed: 1. succeed-before-callback: do not set outcome["proceed"] = True before calling self.save(). Instead, determine success by checking child.opened after the save attempt — a successful save closes the editor (child.opened == False); a validation-abort leaves it open. Only proceed if the editor actually closed. 2. dont-ask bypass: when config.get("interface.dont-ask") is set, do not return True immediately and skip the child save. Instead, call self.save() directly (silent, no prompt) and still check child.opened — honour the pref as "save without asking", not "skip saving entirely".
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
