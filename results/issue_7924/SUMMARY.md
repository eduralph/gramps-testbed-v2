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
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: core worktree /home/eddie/gramps/gramps-6.1-lane1 missing — run 'make worktrees LANES=N'.
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix Mantis 7924 so a parent primary editor resolves dirty child primary editors before committing, preserving child references instead of silently dropping them.

Target caveat: `$PDCA_TARGET` is `/home/eddie/gramps/gramps`, readable and patch-applicable, but it is on `master` at `aef9f35ec6` while the brief targets `maintenance/gramps61`; new-code citations therefore use `patch.diff` where the target has not been patched.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the required complete graph outcome and abort alternative for the Family→Person flow, not just a warning (`brief.md:18`, `brief.md:24`, `brief.md:29`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The red condition is re-derived from target source: mother child editor is opened with callback (`gramps/gui/editors/editfamily.py:946`), callback is the only mother-handle write (`gramps/gui/editors/editfamily.py:969`), but save reads/commits mother before close (`gramps/gui/editors/editfamily.py:1294`, `gramps/gui/editors/editfamily.py:1308`, `gramps/gui/editors/editfamily.py:1340`). |
| C3 — C3 Change | FAIL | The patch routes only `define_ok_button` clicks through the resolver (`patch.diff:15`, `patch.diff:26`), but parent window close still offers SaveDialog with `self.save` directly (`gramps/gui/editors/editprimary.py:247`, `gramps/gui/editors/editprimary.py:255`), missing the brief's OK/save shared path. |
| C4 — C4 Verification (red→green) | FAIL | Official red→green verification did not run: `run-verify.sh` failed because `/home/eddie/gramps/gramps-6.1-lane1` is missing (`check-gates.json:33`, `check-gates.json:37`); I applied the patch to a temp copy and only the focused unit test passed: `Ran 12 tests ... OK`. |
| C5 — C5 Causal adequacy | FAIL | The save-boundary cause is only partially addressed: OK clicks resolve children first (`patch.diff:48`, `patch.diff:71`), but the existing close→Save path can still commit the parent before child resolution (`gramps/gui/editors/editprimary.py:244`, `gramps/gui/editors/editprimary.py:255`). |
| T1 — T1 Structure | N/A | Addon layout rules do not apply because the patch is core-only with no `addons-source` path (`check-gates.json:51`, `check-gates.json:55`). |
| T2 — T2 Shape | PASS | New core files have GPL headers and are registered in POTFILES.skip (`patch.diff:137`, `patch.diff:153`, `patch.diff:372`, `patch.diff:388`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: decide whether the runtime gate's pre-test crash is acceptable infra debt or must be rerun before merge; baseline runner exited 1 with no JUnit XML (`check-gates.json:77`, `check-gates.json:82`), while my feasible focused unit run passed 12 tests. |
| T4 — T4 Contribution | N/A | No commit message or PR-description artifact is present, so contribution-wrapper checks are not applicable to this artifact-only review (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | FAIL | Reviewer judgment is not merge-ready because the implementation misses an in-scope save entry point and therefore does not cover the full shared save lifecycle (`brief.md:36`, `brief.md:45`, `gramps/gui/editors/editprimary.py:255`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human must validate the GUI fitness-to-purpose on the reporter flow and decide whether OK-only behavior is sufficient despite the brief requiring shared OK/save coverage (`brief.md:24`, `brief.md:32`, `brief.md:156`). |

## §6 Human Clearance Items

1. T3 runtime gate: rerun or explicitly waive the whole-suite baseline after fixing the missing lane/worktree issue reported by `check-gates.json`; the focused patched-temp run only proves `gramps.gui.test.savecascade_test` passes.
2. V fitness-to-purpose: manually drive the reporter flow in the GUI and also test parent window close → Save while the child editor is dirty; the current patch appears to cover OK clicks but not that close/save path.

### Advisory — adversary

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
> Cleared by Eduard Ralph on 2026-07-03 after the re-implementation in this
> iteration (see build-notes.md). Machine-verification was run in the same
> `gramps-testbed:ubuntu-6.1.0` image the harness gate uses; the GUI
> fitness-to-purpose item is accepted on the human's authority (not independently
> visually verified). The over-trigger and close/Save-door holes are fixed in the
> patch and covered by tests.
- [x] T3 — T3 Runtime — CLEARED: the full core unit suite was run (32977 tests) — the only 7 failures are pre-existing baseline failures identical on a clean checkout (zip imports + WebCal/NarrativeWeb, unrelated to this diff); zero new regressions. The harness lane worktree was missing (infra), so the whole-suite gate is verified manually rather than via `check-gates.json`.
- [x] V — Validation — fitness-to-purpose — ACCEPTED (human authority): the fix now covers BOTH save doors (OK button AND close/window-X/Cancel→Save), closing the shared-coverage gap the brief required. Live-GUI visual confirmation is deferred; the human accepts the reference-survival behaviour on the strength of the corrected patch + `savecascade_test` (13/13 green) and the committed dogtail repro.
- [x] C4 fix verified — CLEARED (manual): `savecascade_test` 13/13 green in Docker; the DB-end-state dogtail repro is the reference-survival oracle. Official run-verify blocked only by the missing `gramps-6.1-lane1` worktree (infra), not by the fix.

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating): Multiple correctness holes across three iterations: (1) close/Save path not covered — concrete reproduced failing case with the same outcome the brief calls "must be impossible"; (2) dont-ask semantics inverted (one preference, discard vs silent-save); (3) over-trigger on editors with already-set handles; (4) zero automated red→green evidence (C4 gate never ran, test in diff cannot go red pre-fix); (5) main reviewer C3+T5 FAIL. Not a viable fix in its current direction.
- By / date: Eduard Ralph / 2026-07-03

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
