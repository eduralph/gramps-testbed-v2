# Result — issue 13268 / notes-editor-undo-scroll-jump

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the Notes editor, working in a note long enough to have a scroll bar, pressing **Undo** also scrolls the editor to the top/first line — forcing the user to scroll back down to where they were. (Mantis 13268; confirmed, always reproducible.)
- Success criterion: Performing **Undo** in the Notes editor leaves the visible scroll position (and the cursor) at the edit site — the viewport is **not** reset to the top of the note — while the text state is correctly reverted.
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core).
- Scope (one logical fix) / out of scope: Undo in the Notes editor resets the scroll to the top instead of preserving position — make undo preserve the viewport/cursor. / **out of scope:** the editor's other undo correctness (text content is reverted fine — only the scroll jumps); paste/redo behaviour beyond what shares the same handler; issue **13267** (the same GIF in note 2 shows both — confirm whether 13267 shares this undo handler before broadening; if it does, flag to the human rather than silently bundling).

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 4 file(s) conform to doc 16 §Coding style
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 13268 / notes-editor-undo-scroll-jump

Advisory, artifact-only review. Inputs: `brief.md`, `patch.diff`, `check-gates.json`
(build-notes.md withheld by design). Every Basis below is re-derived from the
artifacts, not copied from the gate output.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:10 states a concrete, falsifiable success criterion (undo leaves scroll+cursor at edit site, text reverted) and brief.md:11 a category-level invariant. Well-formed and testable. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Test isolates the cause: pre-fix the handlers call `set_text()` (full rebuild) which collapses the mid-buffer `TextMark` to offset 0, so `assertGreater(new_offset, 0)` fails (undoablestyledbuffer_test.py:114-123). Mechanically confirmed by the gating C4 gate `red-without-fix=PASS` (check-gates.json:37). |
| C3 — C3 Change | PASS | Minimal, on-cause: `apply_styled_tags()` reapplies tags to existing text without deleting the buffer (patch.diff:12-26); the five undo/redo handlers swap `set_text()`→`apply_styled_tags()` (undoablestyledbuffer.py:169,185,196,207,218). `set_text()` behaviour preserved as a refactor (patch.diff:8-10). Text is already correct at the call site (prior manual delete/insert), so applying tags in place is correct. |
| C4 — C4 Verification (red→green) | PASS | The one gating gate: `C4-verify: green-with-fix=PASS / red-without-fix=PASS`, result=pass (check-gates.json:33-39). T3 baseline unchanged (check-gates.json:73) confirms the new test runs and the suite did not regress, so the API surface the test drives (`undo_disabled`, `undo`, `insert`, `delete`) exists and executes. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | The test asserts a *buffer* `TextMark` survives undo (undoablestyledbuffer_test.py:110-123) as a stand-in for the un-assertable `GtkTextView` scroll position (brief acknowledges this, brief.md:16). Whether "mark not collapsed" faithfully captures "viewport preserved" — and whether the residual `place_cursor()` call (undoablestyledbuffer.py:170,208) could still scroll the view to the cursor — is a GUI-internals judgment that cannot be settled from artifacts. Contested root cause: brief.md:15 hypothesised "save/restore the scroll mark"; the shipped fix instead avoids the rebuild entirely. Reasonable, but the substitution needs human confirmation. |
| T1 — T1 Structure | PASS | New core test follows doc 16 core-test layout: `gramps/gui/widgets/test/` dir + `__init__.py` + `*_test.py` (patch.diff:30-37), registered in `po/POTFILES.skip` per brief.md:18 (patch.diff:228-229). The T1 gate FAIL ("no .gpr.py", check-gates.json:55) is an addon-structure check misapplied to a core change — N/A here; non-gating. |
| T2 — T2 Shape | PASS | Full GPL header on the new file (patch.diff:39-56); gate T2 reports 4 files conform to doc 16 §Coding style (check-gates.json:64). No `print()` debris in the diff. |
| T3 — T3 Runtime | PASS | Unit suite matches recorded baseline (7 known reds) and interface smoke matches (1 known red) — check-gates.json:73,82. Advisory only: `⚠ baseline tree drift: recorded detached@674e3b` (check-gates.json:73) — worth a glance but non-gating and the comparison still matched. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle, so the commit/PR-wrapper check has nothing to evaluate (check-gates.json:91). Consistent with the brief's STOP discipline (draft-only until sign-off, brief.md:23-27). |
| T5 — T5 Judgment | NEEDS-HUMAN | The fix broadens beyond the undo path to the redo/style handlers (`_undo_style`, `_handle_redo`, `_undo_delete` redo branch — undoablestyledbuffer.py:196,207,218). Brief scope flags redo as out of scope "beyond what shares the same handler" and requires confirming whether issue **13267** shares this handler *before* broadening (brief.md:14,19). They do share the `set_text` pattern, so the broadening is defensible — but the 13267 cross-check lived in the withheld build-notes and a human must clear it. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. The user-visible defect (scroll jump on Undo in a realized, scrolled Notes editor) is GUI-facing and was never asserted headlessly — only the buffer-mark proxy was. Confirming the actual viewport is preserved requires the manual repro from brief.md:15 (long note, scroll to bottom, Undo → viewport stays). |

## §6 — Items the human must clear

1. **C5 — Causal adequacy / contested root cause.** Confirm the buffer-mark
   proxy faithfully represents `GtkTextView` viewport preservation, and that the
   surviving `place_cursor()` calls (undoablestyledbuffer.py:170,208) do not
   themselves re-scroll the view to the cursor. The shipped fix ("don't rebuild
   the buffer") differs from the brief's hypothesised fix ("save/restore the
   scroll mark", brief.md:15) — accept the substitution or reject it.

2. **T5 — Judgment / scope.** The patch extends the same `apply_styled_tags`
   change to the redo and style-undo handlers. Per brief.md:14,19, confirm
   issue **13267** shares this handler (the evidence was in the withheld
   build-notes) — accept the bundled broadening or require it be split out.

3. **V — Validation / fitness-to-purpose.** Run the manual repro (brief.md:15):
   open a note long enough to scroll, scroll to the bottom, press Undo, and
   verify the viewport and cursor stay at the edit site while the text reverts.
   This is the load-bearing check the headless test cannot perform.

## Notes (non-gating, for the human's awareness)

- T1 gate disagreement: the gate emitted FAIL on an addon `.gpr.py` rule that
  does not apply to a core contribution. I read this as a misfire, not a real
  structural defect — flagged here so the FAIL isn't taken at face value.
- T3 baseline tree drift (`recorded detached@674e3b`) is advisory; the baseline
  comparison still matched, so no regression is implied, but a stale baseline
  tree is worth re-recording.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — The test asserts a *buffer* `TextMark` survives undo (undoablestyledbuffer_test.py:110-123) as a stand-in for the un-assertable `GtkTextView` scroll position (brief acknowledges this, brief.md:16). Whether "mark not collapsed" faithfully captures "viewport preserved" — and whether the residual `place_cursor()` call (undoablestyledbuffer.py:170,208) could still scroll the view to the cursor — is a GUI-internals judgment that cannot be settled from artifacts. Contested root cause: brief.md:15 hypothesised "save/restore the scroll mark"; the shipped fix instead avoids the rebuild entirely. Reasonable, but the substitution needs human confirmation.
- [x] T5 — T5 Judgment — The fix broadens beyond the undo path to the redo/style handlers (`_undo_style`, `_handle_redo`, `_undo_delete` redo branch — undoablestyledbuffer.py:196,207,218). Brief scope flags redo as out of scope "beyond what shares the same handler" and requires confirming whether issue **13267** shares this handler *before* broadening (brief.md:14,19). They do share the `set_text` pattern, so the broadening is defensible — but the 13267 cross-check lived in the withheld build-notes and a human must clear it.
- [x] V — Validation — fitness-to-purpose — Always-human. The user-visible defect (scroll jump on Undo in a realized, scrolled Notes editor) is GUI-facing and was never asserted headlessly — only the buffer-mark proxy was. Confirming the actual viewport is preserved requires the manual repro from brief.md:15 (long note, scroll to bottom, Undo → viewport stays).

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-20

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
