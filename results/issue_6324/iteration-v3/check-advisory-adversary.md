# check-advisory-adversary.md — issue 6324 / pdf-table-cell-wrap-page-break (iteration 3)

Skeptic's pass. All probes run against `$PDCA_TARGET` source (patch applied in a scratch
clone; target left untouched). Note: `libcairodoc.py` is byte-identical between the
checkout's `master` HEAD and `origin/maintenance/gramps61`, and the patch applies cleanly
to both, so the branch-name discrepancy of the checkout is immaterial.

## Evidence attacks (red→green, production path)

- Independently re-ran the asserted proof: both tests **fail** on unpatched
  `gramps/plugins/lib/libcairodoc.py` (torn-row assertions fire with the exact pre-fix
  symptom, wrapping cell one page after its rowmate) and **pass** with the patch. The test
  drives the real `CairoDoc.paginate` / `divide` chain, and its row construction
  (`GtkDocTableRow([50, 50])`) matches production `start_row`
  (gramps/plugins/lib/libcairodoc.py:1505-1506). The iteration-1 tautology (`_text` vs
  `_plaintext`) is fixed — `_page_texts` reads `_plaintext`. **Attempted to refute the
  red→green evidence as tautological/mocked; could not.**
- Vacuity (portability) gap in test 2: `test_wrapping_cell_splits_beside_split_sibling`
  (gramps/plugins/test/cairodoc_table_pagination_test.py:442-493, `page_height =
  filler_h + 2 * line_h` at :462) guards WRAP's line count (2-3) but never asserts that
  the WRAP cell actually *failed to fit* beside the split sibling (e.g. that WRAP's tail
  lands on a later page than "Wstart"). Under different font metrics a 2-line WRAP could
  fit the 2-line gap and the test would pass pre- and post-fix without exercising the
  `force_split` branch. In the gate environment it demonstrably exercises it (red
  confirmed), so this is a future-silent-rot concern, not a current false pass.

## Fix attacks (concrete adversarial geometries, patched code)

- No content drop / no duplication in any terminating run I could construct: mid-table
  whole-row move (rows before + after intact), reversed column order [WRAP, TALL],
  multi-paragraph cell beside a splitting sibling, forced-split-fails placeholder branch
  (oversized 40pt cell beside a splitting cell — all characters render, split "BIGWOR"/"D"
  across the boundary, and that geometry **hung forever pre-fix**, so the patch is a strict
  improvement there). **Attempted to find a dropped or doubled word; could not.**
- NEEDS-HUMAN — Residual non-termination (pre-existing class, new code path): when a
  kept-together (<4-line) cell cannot fit even a full empty page (e.g. two-column row
  `[WRAP(2-3 lines), TALL]` with page_height ≈ 1 filler row + 2 lines), the new
  `GtkDocTable.divide` early return re-queues `(None, new_table)` every pass and
  `paginate_document`'s unbounded `while not self.paginate(): pass`
  (gramps/plugins/lib/libcairodoc.py:1777-1780) never returns, emitting empty pages
  forever. I verified the **same geometry also hangs pre-fix** (via the blank-cell-carry
  loop through :620's keep-together return), so this is not a new failure class — but the
  patch routes into it through a brand-new cycle, and post-fix the degraded output renders
  strictly less before hanging (pre-fix the tall sibling's text still appeared; post-fix
  nothing after the fillers). The added test tacitly acknowledges the hazard by capping its
  own paginator at 60 iterations (cairodoc_table_pagination_test.py:326-347) while
  production has no such cap. Human should decide whether "equivalent pre-existing hang" is
  acceptable residue or whether the row-move branch needs a no-progress guard (force split
  when height == full page height).
- Behavioral asymmetry, not a defect: whether a row moves whole or splits now depends on
  column order (`cell_split` is only set by columns processed *earlier* —
  patch hunk at libcairodoc.py:903-938 region): `[TALL, WRAP]` splits with a forced WRAP
  split, `[WRAP, TALL]` moves the row whole and defers TALL's start to the next page. Both
  outcomes satisfy the brief's invariant ("whole row moves, or every cell renders its first
  lines"); content verified complete in both orders. Noted for the record; not a refutation.
- Layout-regression re-check (iteration-1 finding #1): the keep-together shortcut
  (libcairodoc.py:620) is preserved for the unforced path, and rows not hitting the
  `c1 is None` case take exactly the old code path (`kept_cells` equals the original cell
  list object-for-object). Only previously-buggy (torn/blank) geometries change layout.
  **Attempted to reproduce the iteration-1 orphaned-line regression; could not** — the
  3-line-cell/2-line-room geometry now moves the row whole with all text intact.

## Verdict attacks

- `check-gates.json` C4/C5 claims verified independently above; no rationalization found
  there. One soft spot: T3 (`T3-unit`, advisory) passed against a baseline recorded on a
  different tree ("⚠ baseline tree drift: recorded detached@674e3b",
  check-gates.json rows[8]) — a newly-introduced red that happens to coincide with one of
  the "7 known test reds" would be masked. Given C4/C5 and my probes, I found no evidence
  of an actual masked failure; flagging the gate-integrity caveat only.

## Bottom line

Attempted to refute (a) the red→green evidence as tautological or non-production, (b) the
fix via content drop, duplication, column-order, multi-paragraph, oversized-font and
mid-table geometries, and (c) the iteration-1/iteration-2 regressions recurring — **could
not**. The one substantive residue is the pre-existing pagination hang class the patch
inherits (NEEDS-HUMAN above).
