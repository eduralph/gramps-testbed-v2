# Brief — issue 6324 / pdf-table-cell-wrap-page-break

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** pdf-table-cell-wrap-page-break
- **Defect:** In the print/PDF (cairo) document backend, a table cell sitting on the last
  line of a page whose text must wrap to the next line is not rendered — the cell prints
  no text at all (neither the first line nor the wrapped remainder). Reproduced by dsblank
  (4.0.x, Database Differences Report) and still confirmed by him in 2015; other output
  formats render the cell correctly.
- **Success criterion:** After the fix, a table cell whose wrapped content straddles a
  page boundary renders its full text across the two pages with no lines dropped.
  Demonstrable by a C4 docgen test that lays out a table row whose cell wraps at the
  bottom of a page and asserts the cell's text is present in the paginated output (red
  pre-fix — cell text missing; green post-fix).
- **Invariant to restore:** Paginating a document must preserve all content — a table
  cell whose text crosses a page boundary must appear in full across the pages, never be
  silently dropped. (Gramps docgen pagination rule; no external canon — the cell/paragraph
  division logic drops the cell instead of splitting or moving it intact when only part of
  a wrapping cell fits at the bottom of a page.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** high
- **Scope:** The cairo backend's page-division logic for a table cell / its paragraph
  loses the cell's content when a wrapping cell lands on the last line of a page (the
  cell is neither correctly split across the break nor moved intact to the next page).
  Restore full rendering of such a cell. / out of scope: other backends (they render
  correctly); table styling/borders beyond what a correct split requires; the ODT
  text-scaling defect (issue 5733, different file); any broad rewrite of the division
  engine — target the specific content-drop case.
- **Repro instruction:** On `maintenance/gramps61`, run a table-based report (e.g. the
  Database Differences Report addon, or any report with wide table cells) to PDF such that
  a cell needing to wrap falls on the last line of a page; the first/all lines of that
  cell are missing from the output.
- **Test file:** `gramps/plugins/test/cairodoc_table_pagination_test.py` (core `test/`
  package, `*_test.py` suffix). The test MUST drive the production division path (the
  `GtkDocTableCell` / `GtkDocParagraph` `divide` chain used to paginate) with a geometry
  that forces the last-line-wrap-at-page-boundary case, and assert the cell's text
  survives — not a reimplementation of the pagination math (principles §3.4). If a
  deterministic red→green at this layer proves infeasible, say so in build-notes so C4
  can route to human verification rather than manufacturing scaffolding.
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause region: `gramps/plugins/lib/libcairodoc.py:979-1021` `GtkDocTableCell.divide`
  and `gramps/plugins/lib/libcairodoc.py:552-640+` `GtkDocParagraph.divide` — the
  `line_count < 4 and parent._type == "CELL"` / `(None, self)` move-to-next-page branches).
- **New/removed files:** adds `gramps/plugins/test/cairodoc_table_pagination_test.py` (a
  test, no translatable strings) → register in `po/POTFILES.skip`. No other `.py`
  added/removed.
- **Prior-art check (triage cycles):** searched `gramps/plugins/lib/libcairodoc.py` on
  `upstream/maintenance/gramps61` — only https/black/mypy/license churn, no pagination
  content-drop fix; no open/closed PR found on this path. Not already upstream.
- **Mantis:** 6324
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Three adversary findings require a tighter fix before accept: 1. Layout regression: the patch removes the <4-line keep-together shortcut wholesale, splitting short cell paragraphs across pages on previously-correct documents (reproduced: 3-line cell with 2 lines of room now orphans one line on the next page). Scope the fix to suppress keep-together only when it makes no progress (i.e. the cell still can't fit after the move), not unconditionally. 2. Test assertion tautology: _collect_text checks _text but divide truncates _plaintext; the word-survival assertion passes even if all pages except page 1 are discarded. Fix the test to assert on _plaintext so content-drop can actually be detected. 3. Wrong test geometry: the test's never-fits page geometry does not reproduce the brief's reported scenario (wrapping cell on last line of a normal page). Add a test case matching the brief's repro (5 filler rows + wrapping row, page holds fillers + ~1 line) to confirm the actual user-visible defect is fixed.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: The patch fixes only the last-column-wrapping-cell geometry (cell_split=False arm). When an earlier column in the same row splits across the page break, the cell_split=True arm runs instead and the short later-column cell is still rendered blank beside its text-keeping sibling — identical pre- and post-fix. The adversary reproduced this with a concrete multi-column layout. The brief's invariant ("never left blank while a sibling cell keeps its text") is general over column positions; the fix must handle the cell_split=True branch too, and the test must cover the earlier-column-splits geometry.
- Failing gate: T3 runtime: gramps core unit suite (whole-suite baseline) (advisory) — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 3 — carry-forward (from the previous attempt)
- Sign-off rationale: The row-move branch must implement a no-progress guard: when a kept-together cell cannot fit even a full empty page, divide() must force-split (or error) instead of re-queuing (None, new_table) and spinning paginate_document's unbounded loop forever. The pre-existing hang is not acceptable residue — the new code path must not inherit it.
- Full previous attempt preserved in `iteration-v3/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
