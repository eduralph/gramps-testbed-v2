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
