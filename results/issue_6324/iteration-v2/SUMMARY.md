# Result — issue 6324 / pdf-table-cell-wrap-page-break

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the print/PDF (cairo) document backend, a table cell sitting on the last
- Success criterion: After the fix, a table cell whose wrapped content straddles a
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: The cairo backend's page-division logic for a table cell / its paragraph

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (2 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix cairo print/PDF table pagination so a short wrapping table cell at a page boundary is not rendered blank or dropped, and add a regression test.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines a narrow cairo backend defect and success criterion: wrapped table-cell text at a page boundary must survive without dropped lines; scope excludes other backends and broad rewrites (brief.md:5, brief.md:11, brief.md:24). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added test is designed to fail on the pre-fix base by driving a page that holds filler rows plus only part of the wrapping row and asserting no torn row plus full `_plaintext` survival (patch.diff:316, patch.diff:329, patch.diff:347, patch.diff:357); check gate reports red-without-fix PASS (check-gates.json:33). |
| C3 — C3 Change | PASS | The patch changes only cairo table/table-row/table-cell division handling plus the required test/POTFILES entry, directly at the briefed root-cause surface (patch.diff:5, patch.diff:24, patch.diff:70, patch.diff:86, patch.diff:371). |
| C4 — C4 Verification (red→green) | PASS | Gate reports green-with-fix PASS and red-without-fix PASS (check-gates.json:33); I also applied the patch in `/tmp/pdca-gramps-check.br1lQq` and ran `env GRAMPS_RESOURCES=build/share PYTHONPATH=. python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test`, which returned `Ran 1 test ... OK`. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: accept the chosen behavioral repair as causally adequate: the base short-cell keep-together branch returns `(None, self), 0` (gramps/plugins/lib/libcairodoc.py:620) and the patch propagates that as “move the whole row/table onward” (patch.diff:39, patch.diff:47, patch.diff:81), but the human must decide whether moving the row intact is acceptable for the product expectation versus requiring an actual split at the boundary. |
| T1 — T1 Structure | N/A | No addon-source layout is touched; the bundle is a core cairo/test change, matching the gate’s addon-structure N/A (check-gates.json:51). |
| T2 — T2 Shape | PASS | Added test has the project GPL header and no translatable strings, and the new core test file is registered in `po/POTFILES.skip` as required (patch.diff:92, patch.diff:139, patch.diff:371). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: accept or rerun broader runtime coverage: the focused patched regression passes locally, but the configured whole-suite runtime gate failed before producing JUnit XML, reported as a pre-test crash rather than a test failure (check-gates.json:78). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this review bundle, so contribution-wrapper review is not applicable here (check-gates.json:87). |
| T5 — T5 Judgment | PASS | The patch is scoped to the cairo pagination call chain, avoids the rejected v1 blanket removal, asserts rendered `_plaintext`, and uses geometry matching the brief’s filler-row-plus-wrapping-row scenario (brief.md:60, patch.diff:126, patch.diff:245, patch.diff:329). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: product fitness remains human sign-off: the automated regression proves preservation/no torn row in a synthetic cairo pagination case, but a human must decide whether that sufficiently represents the user-visible Database Differences Report/PDF behavior described in the brief (brief.md:6, brief.md:31). |

§6 Human Clearances

1. C5 causal adequacy: decide whether moving the affected short wrapping row intact to the next page satisfies the intended cairo pagination behavior, or whether the product requires first-line-on-current-page splitting.
2. T3 runtime: decide whether the focused regression plus C4 gate are enough despite the configured whole-suite runner’s pre-test crash/no-JUnit result, or require a clean broader suite rerun.
3. V validation: decide whether the synthetic production-path pagination test is fit for purpose for the original PDF/report symptom, or require a manual Database Differences Report PDF check.

### Advisory — adversary

# Adversarial review — issue 6324 / pdf-table-cell-wrap-page-break

Lens: refute the red→green evidence and the reviewer's "green post-fix" verdict. All
citations are grounded on the **unpatched** target at
`/home/eddie/gramps/gramps/gramps/plugins/lib/libcairodoc.py`; patched behaviour was
verified by applying `patch.diff` to a scratch checkout, running the reproductions below,
then restoring the tree.

## What survives the attack

- The red→green is **genuine for the tested geometry**. Pre-fix, the test's `[LABEL, WRAP]`
  row tears (LABEL keeps text, WRAP cell renders blank) — `_torn_rows` flags it → RED.
  Post-fix the whole row moves to the next page → GREEN. Confirmed by running the added
  test against both trees. The C5 production-path claim also holds: the test drives the
  real `CairoDoc.paginate` / `GtkDocTable`/`Row`/`Cell`/`Paragraph.divide` chain, not a
  copy. Attempted to refute the red-for-the-wrong-reason and mock-away angles; could not.

## Findings the reviewer's "green" does not cover

- **NEEDS-HUMAN — The test exercises only ONE of the patch's two boundary branches; the
  other still tears a row (the exact bug-6324 symptom).** `gramps/plugins/lib/libcairodoc.py:903`
  (`GtkDocTableRow.divide`; post-patch the new `cell_split=True` arm is the block that
  appends a blank `GtkDocTableCell` placeholder to `kept_cells` while handing the intact
  cell to `new_row`). That arm is reached whenever an **earlier** column in the row splits
  across the page break (`cell_split` becomes True at the `else` at :921-923) and a **later**
  short (<4-line) cell then can't fit and returns `(None, self)`. The added test never gets
  there: its wrapping cell is column 1 and column 0 is a single-line `LABEL`, so `cell_split`
  is always False when the None-cell is hit and the *whole-row-move* arm runs instead.
  Reproduced with a realistic geometry — a filler row plus a `[multi-line col0, 2-line col1]`
  row on a ~5-line page — which yields a **torn boundary row** (`col0` prints its first lines,
  `col1` prints blank beside it) on the split page, *identical pre- and post-fix*. The patch
  neither splits nor moves that short cell intact; it leaves it blank at the page foot next
  to a sibling that keeps its text. That directly violates the brief's invariant ("never be
  left blank while a sibling cell in the same row keeps its text", brief §Invariant) and its
  success criterion ("renders its full text across the two pages"). The reviewer's C4 green
  proves a strictly narrower property than the brief asks for.

- **NEEDS-HUMAN — Runaway pagination + total content loss on a page shorter than a
  keep-together cell; the patch adds new `(None, …)` propagation without closing this hole.**
  `gramps/plugins/lib/libcairodoc.py:620` (`line_count < 4 and self._parent._type == "CELL"`
  → `return (None, self), 0`) combined with the patch's new whole-row-move
  (`GtkDocTableRow.divide`, the `if not cell_split: return (None, self), 0` arm) and the new
  `GtkDocTable.divide` r1-None arm at `:846`/:856. A 2-line cell beside a splitting
  multi-line cell on a page ~1.5 lines tall causes the short cell to hit keep-together on
  every page and be re-deferred forever: my bounded driver produced **81 pages** (hit the
  80-iteration cap) with the short cell's text **never rendered** (fully dropped). This
  reproduces identically pre-fix, so it is pre-existing — but note (a)
  `CairoDoc.paginate_document` at `gramps/plugins/lib/libcairodoc.py:1779` is
  `while not self.paginate(...): pass`, an **unbounded** loop → a real hang, which the added
  test masks behind its own `max_iterations=60` cap (test `_paginate`), and (b) the patch is
  scoped to "restore full rendering of such a cell" yet leaves this content-drop path
  untouched. A human should confirm the patch's several new non-terminating-looking
  `(None, …)` returns (`GtkDocTableCell.divide` `e1 is None and childnr == 0`;
  `GtkDocTableRow` whole-move; `GtkDocTable` r1-None → `(None, new_table)`) cannot themselves
  loop on other inputs.

- **Unwarranted verdict claim.** `check-gates.json` C4 asserts
  "green-with-fix=PASS / red-without-fix=PASS" and `overall: pass`. That is true only for the
  single geometry the test builds (`_table`: 3 filler rows + `[LABEL, WRAP]`, wrapping cell in
  the last column). It does **not** license the brief-level success criterion, which is
  general over column positions. The reviewer appears to have generalised a
  last-column-only green to "the cell renders in full across pages"; the earlier-column-splits
  case (Finding 1) refutes that generalisation with a concrete failing layout.

## Scope note

Findings 1 and 2 reproduce identically on the pre-fix tree, so neither is a *regression the
patch introduces* — they are cases the patch **claims to fix but does not**, squarely inside
the brief's scope ("a table cell whose wrapped content straddles a page boundary"). I did not
find an input where the patch makes a previously-correct document worse: the single-column
short-cell-at-boundary case actually improves (pre-fix leaves a blank row; post-fix the row
moves whole). T3-unit already shows `fail` (pre-test crash, non-gating) — that is
environmental, not attributable to this diff.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C5 — C5 Causal adequacy — DECISION OWED: accept the chosen behavioral repair as causally adequate: the base short-cell keep-together branch returns `(None, self), 0` (gramps/plugins/lib/libcairodoc.py:620) and the patch propagates that as “move the whole row/table onward” (patch.diff:39, patch.diff:47, patch.diff:81), but the human must decide whether moving the row intact is acceptable for the product expectation versus requiring an actual split at the boundary.
- [ ] T3 — T3 Runtime — DECISION OWED: accept or rerun broader runtime coverage: the focused patched regression passes locally, but the configured whole-suite runtime gate failed before producing JUnit XML, reported as a pre-test crash rather than a test failure (check-gates.json:78).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: product fitness remains human sign-off: the automated regression proves preservation/no torn row in a synthetic cairo pagination case, but a human must decide whether that sufficiently represents the user-visible Database Differences Report/PDF behavior described in the brief (brief.md:6, brief.md:31).

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
- Iteration delta (if iterating): The patch fixes only the last-column-wrapping-cell geometry (cell_split=False arm). When an earlier column in the same row splits across the page break, the cell_split=True arm runs instead and the short later-column cell is still rendered blank beside its text-keeping sibling — identical pre- and post-fix. The adversary reproduced this with a concrete multi-column layout. The brief's invariant ("never left blank while a sibling cell keeps its text") is general over column positions; the fix must handle the cell_split=True branch too, and the test must cover the earlier-column-splits geometry.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
