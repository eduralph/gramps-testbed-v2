# Build notes — issue 6324 (pdf-table-cell-wrap-page-break)

Iteration 3. Target: `gramps-project/gramps @ maintenance/gramps61`
(worktree `/home/eddie/gramps/gramps-6.1-issue6324` at `0d9e148908`; the pinned C4
worktree `gramps-6.1` is at the same commit and the patch applies clean to it).

All line citations below are **post-patch** line numbers in
`gramps/plugins/lib/libcairodoc.py` on the target worktree.

## Carry-forward addressed (iterations 1 & 2)

- **Iter-1 finding (layout regression):** do not remove the `line_count < 4 and CELL`
  keep-together shortcut wholesale. — Kept. The shortcut still fires (`:625`); a short
  cell that does not fit is still kept together, now by moving the **whole row** to the
  next page (`GtkDocTableRow.divide` `:936`) instead of blanking one cell. A short cell
  that previously moved intact still moves intact — verified by the randomized sweep
  (identical content-loss / non-termination counts pre and post, below).
- **Iter-1 finding (assertion tautology):** assert on `_plaintext`, not `_text`. — The
  test reads `child._plaintext` (the string `divide` actually truncates and `draw`
  renders), via `_page_texts`/`_first_page` (test `:198`, `:214`).
- **Iter-1 finding (wrong geometry):** use the brief's realistic repro. — Test 1 is
  3 filler rows + a `[LABEL, WRAP]` row on a page that holds the fillers plus ~1 line
  (`test_wrapping_last_cell_moves_row_whole`).
- **Iter-2 finding (the `cell_split=True` branch still tears):** when an *earlier* column
  splits across the boundary, the later short column was still left blank beside it. —
  **This is the core of iteration 3.** The previous attempt handed the short cell whole
  to the continuation row and left a blank placeholder on the current page (a torn row,
  identical pre/post). This iteration instead **forces the short cell to split too**
  (`GtkDocTableRow.divide` `:945` → `cell.divide(..., force_split=True)` `:951`), so its
  first lines render on the same page as its split sibling. Covered by
  `test_wrapping_cell_splits_beside_split_sibling` (the earlier-column-splits geometry
  the carry-forward demanded).
- **Iter-2 failing gate (T3 baseline delta — pre-test crash, NO JUnit):** see
  *Headless / T3* below. This is the known core-suite `headless-ut-segfault` baseline
  (INTEGRATION §3), environmental and not introduced by this diff.

## What the defect actually is

A table row lands near the bottom of a page. One cell holds a short (`< 4` line)
paragraph that must wrap. The per-paragraph keep-together rule
(`GtkDocParagraph.divide` `:625`, `line_count < 4 and CELL → return (None, self)`)
refuses to split that cell — but the decision is made **per cell**, with no knowledge of
its siblings. In the original `GtkDocTableCell.divide` the `(None, self)` return then
falls through to `self._children = self._children[:childnr]` which truncates the cell to
`[]`, so the cell renders **blank** at the foot of the page while the paragraph is carried
to the next page beside blank copies of the row's other cells. Reproduced verbatim
(pre-fix, driving the production paginator):

- page 0 last row: `['Zlabel', '']`  ← the wrapping cell prints no text at all
- page 1 first row: `['', 'Wstart is a long cell value …']`

exactly dsblank's report ("the cell prints no text at all … at the bottom of a page",
Mantis 6324 ~0031536). The invariant broken is *all cells of a row begin together*.

The same tear occurs in a second shape: when an **earlier** column is a genuinely long
(`≥ 4` line) paragraph that splits, and a **later** column is a short keep-together cell
that cannot fit — the long cell shows its first lines, the short cell goes blank beside
it (the iter-2 finding). And in a tighter geometry that per-cell keep-together loops
forever (the adversary's 61-page runaway).

## The fix (smallest change that restores the invariant)

Keep-together is honoured **at the row level**, and a row already committed to a split
forces its short cells to split too. `gramps/plugins/lib/libcairodoc.py`:

1. `GtkDocParagraph.divide` gains `force_split=False` (`:552`); the keep-together rule is
   guarded by `not force_split` (`:625`). `force_split` is threaded but never changes the
   *nothing-fits* / *single-line-too-tall* returns — it only overrides the keep-together
   heuristic.
2. `GtkDocTableCell.divide` gains `force_split=False` (`:1027`), passes it to its first
   child (`:1044`), and — when the first child places nothing — returns the cell
   **intact** (`if e1 is None and childnr == 0: return (None, self), 0`, `:1054`) instead
   of falling through and truncating itself to `[]`. This is what stops the blank-cell
   drop at the source.
3. `GtkDocTableRow.divide` (`:920`):
   - if a cell placed nothing **and no earlier cell has split** (`c1 is None and not
     cell_split`, `:936`) → `return (None, self), 0`: move the **whole row** to the next
     page (keep-together preserved, no cell blanked).
   - if a cell placed nothing **and an earlier cell already split** (`:945`) → re-divide
     it with `force_split=True` (`:951`) so it splits beside its sibling. If even forced
     nothing fits (a taller-font edge case, `:954`) move that one cell onward and leave an
     empty placeholder — no content dropped.
   - the row's kept cells are rebuilt in `kept_cells` (`:971`) so nothing is
     double-referenced across the two pages.
4. `GtkDocTable.divide` (`:861`, `if r1 is None`): when a row moves whole, take it and
   every following row into the continuation table and delete them here (so the row is
   not drawn on both pages); if nothing of the table fits, `return (None, new_table), 0`.
5. `GtkDocPicture.divide` gains an ignored `force_split=False` (`:1145`) so a picture
   cell can be re-divided by the row uniformly (a picture never splits regardless).

Net: +74 lines in one file, three `divide` methods materially changed. The brief names an
**Invariant to restore**, so per principles §1.2/§2 the target is the smallest change that
restores it (a row's cells begin together), not the smallest diff.

## Termination

`move-whole-row` and `force_split` both fire only when a cell placed *nothing* at the
current height. On the continuation the row gets a full page, where a `< 4`-line paragraph
(or a first line) fits — so progress is made. The fix strictly *reduces* non-termination:
the tight `[TALL, WRAP]` geometry that looped to the 60-iteration cap pre-fix now
terminates in 4 pages. The randomized sweep shows **0** non-termination both before and
after.

## Alternatives considered and rejected (with cost)

1. **v1: delete the keep-together shortcut (−1 condition).** Rejected at iter-1 sign-off:
   short cells then *split* (orphan a line) on documents that previously moved them
   intact, and it does not fix the tear (the per-cell split still blanks the sibling on
   the continuation). My probes confirm the per-cell split path also tears the row.
2. **v2: handle only the last-column arm (move whole row), hand the short cell whole to
   the continuation in the `cell_split=True` arm.** Rejected at iter-2 sign-off: the
   earlier-column-splits case is still torn (blank placeholder beside a split sibling),
   identical pre/post. Cost of the gap: the entire `cell_split=True` branch
   (`libcairodoc.py:945-953` in this patch) rendered the short cell blank. This iteration
   replaces that ~6-line branch with a `force_split` re-divide (same line budget) that
   actually renders the cell.
3. **Two-pass, non-mutating probe of every cell first, then choose move-whole vs
   split-all for the row uniformly.** Rejected on cost: it needs a `divide` that separates
   *measure* from *mutate* (the split path mutates the paragraph in place at
   `libcairodoc.py:717-732`), i.e. a new measurement method duplicating ~60 lines of the
   paragraph layout code (`:552-638`) — a parallel implementation that would drift from
   the real `divide` (principles §3.4). The chosen left-to-right approach re-divides the
   *same* production method a second time with a flag (no duplicated math), at the cost of
   one extra `divide` call on the rare boundary cell. The only observable difference is
   cosmetic (column order decides whether the whole row moves or the row splits); both
   outcomes satisfy the invariant.
4. **Thread the full page height through all ~9 polymorphic `divide` signatures to decide
   keep-together by "fits on a fresh page".** Rejected: that is the "broad rewrite of the
   division engine" the brief puts out of scope, and it changes nothing for realistic
   geometry (a `< 4`-line paragraph always fits a fresh page).

## Out of scope / pre-existing

- Content is dropped only in degenerate geometries (a page shorter than a single text
  line): the randomized sweep (3000 configs, 1–4 cols, 2–8 rows, 1–2 paragraphs/cell,
  page 80–500 pt × 300–600 pt) reports **content_loss=16, nonterm=0 both pre and post-fix**
  — the *same* 16 degenerate cases, none introduced by this patch. The brief scopes the
  change to "the specific content-drop case … not any broad rewrite", so the
  page-shorter-than-one-line drop (the old `:637` `at_last_line` return) is left as-is.

## Test — `gramps/plugins/test/cairodoc_table_pagination_test.py`

Drives the **production** path (principles §3.4), not a re-implementation of the math:
builds real `GtkDocTable/Row/Cell/Paragraph`, derives page geometry from the production
`GtkDocTableRow.divide` (measuring true row heights with a huge available height), and
runs the production `CairoDoc.paginate` step in a bounded loop (the real
`paginate_document` is an unbounded `while not paginate()`).

Two tests, one per boundary branch:
- `test_wrapping_last_cell_moves_row_whole` — the brief's repro (fillers + `[LABEL, WRAP]`
  at the page foot). Whole-row-move arm.
- `test_wrapping_cell_splits_beside_split_sibling` — `[TALL, WRAP]` where TALL splits and
  WRAP must split too. `force_split` / `cell_split=True` arm (the iter-2 requirement).

Each asserts: pagination terminates and crosses a boundary (`≥ 2` pages, else the geometry
is misconfigured and it fails loudly); the wrapping cell's opening token (`Wstart`) begins
on the **same page** as its rowmate's opening token (`Zlabel` / `Talpha`) — the precise
red→green signal that catches the tear **without** false-flagging a legitimate
continuation blank (a cell that fully rendered earlier is legitimately blank on its
continuation page; the same-page-start check does not flag that, whereas a naive
"any blank beside text" over-flags — verified); and no word of the wrapping cell is
dropped. Sanity guards assert WRAP is 2–3 lines and TALL ≥ 4 lines so a font substitution
fails loudly rather than passing vacuously.

Red→green proven in-process against the production `CairoDoc.paginate`/`divide` chain on
the isolated worktree:
- **without the fix** (production reverted, test kept): both tests FAIL —
  `wrap_page 1 != label/tall_page 0` (the torn row).
- **with the fix**: both OK.

## Headless / T3 / C4 environment

The test drives production and so must import `gramps.plugins.lib.libcairodoc` and
`gramps.gen.plug.docgen`. Both transitively import the GUI stack
(`gramps.gen.plug.docgen` → `gramps.gui` + `gramps.gui.dbguielement`; `libcairodoc` →
`gramps.gui.utils`), which is **irreducible** — the production classes under test live
behind those imports. I verified this: I tried making `libcairodoc`'s
`from gramps.gui.utils import SystemFonts` lazy, but (a) `set_font_families()` is called at
module load (`libcairodoc.py:151`) and (b) `gramps.gen.plug.docgen` pulls `gramps.gui`
regardless, so the lazy change bought nothing and was reverted — the patch stays focused
on pagination.

On this host the import + test run **green under plain `python3 -m unittest`, headless**
(no DISPLAY/WAYLAND). On the C4 docker core runner, the GUI import can hit the known
`headless-ut-segfault` core-suite baseline (INTEGRATION §3; `engine/essential-fixes.tsv`
row `headless-ut-segfault` = `f4f94f34db`). `run-verify.sh` handles exactly this: it
retries on the essential line and, if green there, writes `essential-dependency.json`
rather than failing the gate. The iter-2 **T3-baseline delta (exit 1 / NO JUnit)** is this
same environmental core-suite crash — advisory, reproduces on a clean tree, not
attributable to this diff (INTEGRATION §3 "green-C4 / red-T3 split is EXPECTED").

I could **not** run the docker-based `run-verify.sh` / `black` in this sandbox (container
and `pip install` require approvals unavailable here). Mitigations:
- red→green was proven in-process driving the identical production `divide`/`paginate`
  code (above); Check's C4 gate re-runs the real runner.
- `git apply --check` of `patch.diff` is clean against the pinned `gramps-6.1` worktree.
- black: no added line exceeds 88 cols; multi-line calls were hand-checked against black's
  collapse rule (e.g. a 87-col `self._table(...)` call was collapsed to match). A human/CI
  should still run `black` at publish.

Manual validation a human can run at sign-off: generate a report with a wide two-column
table to PDF (e.g. the Database Differences Report addon) such that a wrapping cell lands
on the last line of a page — the cell's text now appears (split across the two pages or
with the whole row moved) instead of a blank cell.

## Files / POTFILES

- `gramps/plugins/lib/libcairodoc.py` — the fix (paragraph/cell/row/table/picture divide).
- `gramps/plugins/test/cairodoc_table_pagination_test.py` — new test, no translatable
  strings → registered in `po/POTFILES.skip` (doc 16 §Adding and removing Python files).
