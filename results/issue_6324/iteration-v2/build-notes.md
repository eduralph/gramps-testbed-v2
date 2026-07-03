# Build notes — issue 6324 (pdf-table-cell-wrap-page-break)

Iteration 2. The v1 approach (delete the `line_count < 4 and CELL` keep-together
shortcut wholesale) was rejected at sign-off for three reasons (carry-forward):
1. layout regression — short cell paragraphs now split/orphan on previously-correct
   documents; 2. test assertion tautology — it asserted on `_text` (not truncated by
   `divide`) instead of the rendered `_plaintext`; 3. wrong test geometry — a
   "never-fits" page that no real report produces.

This iteration replaces the fix entirely with a smaller, targeted one and rebuilds the
test around the *actual, realistic* defect. All three findings are addressed.

## What the defect actually is (reproduced empirically)

I imported the production `gramps.plugins.lib.libcairodoc` and drove the real
`CairoDoc.paginate` → `GtkDocTable/Row/Cell/Paragraph.divide` chain against an in-memory
cairo/Pango surface (headless). Findings:

- **Realistic geometry never *drops* content.** A 4000-trial randomized sweep
  (1–4 columns, 3–12 rows, 1–2 paragraphs/cell, page heights 100–500 pt, page widths
  300–600 pt) showed **0 content loss and 0 non-termination** on the *unpatched* code.
  So the literal single-cell repro in the carry-forward (adversary finding #2) is
  correct pre-fix: a lone wrapping cell is moved intact to the next page, cleanly.
- **The real, user-visible defect is a *torn row*.** With a realistic two-column row
  (`Label | wrapping-value`) landing near the bottom of a page (filler rows above, page
  holds the fillers + ~1 line), the wrapping cell takes the `line_count < 4 and CELL`
  keep-together shortcut and is moved to the next page **by itself**, emptying it on the
  current row. Result, reproduced verbatim:
  - page 0 last row: `['Label', '']`  ← the wrapping cell **prints no text at all**
  - page 1 first row: `['', 'This is a long cell text …']`
  This is exactly dsblank's report ("the cell prints no text at all … at the bottom of
  a page", Mantis 6324 note ~0031536). Content is technically preserved (it is on the
  next page next to blank sibling cells), so a *presence* assertion cannot see it — but
  the row is torn and the cell is blank where the user looks.

The `line_count < 4` shortcut's intent was "keep a short cell together (don't split it) —
move it to the next page". The bug is that it moves **one cell**, tearing its row.

## The fix (smallest change that restores the invariant)

`gramps/plugins/lib/libcairodoc.py`. Keep-together is honoured **at the row level**: a
short cell that cannot place its content at the current height moves the **whole row**
to the next page intact, instead of blanking itself and tearing the row.

1. `GtkDocTableCell.divide` (`libcairodoc.py:1040` post-patch, `if e1 is None and
   childnr == 0`): when the cell's
   **first** child places nothing, return `(None, self)`
   with the cell **left intact** (no mutation, no `new_cell` shell) — signalling "nothing
   placed, move me whole".
2. `GtkDocTableRow.divide` (`libcairodoc.py:931` post-patch, `if c1 is None`; kept-cell
   rebuild at `:958`): when a cell reports
   `c1 is None`, and no earlier cell in the row was genuinely split (`cell_split`),
   return `(None, self)` — move the whole row to the next page. (If an earlier cell *was*
   split the row already spans the boundary, so that whole cell goes to the continuation
   row with an empty placeholder left behind — no content lost, no duplication. The row's
   kept cells are rebuilt in `kept_cells` so nothing is double-referenced.)
3. `GtkDocTable.divide` (`libcairodoc.py:856` post-patch, `if r1 is None`): handle it by
   moving that row and every row after it into the continuation table and deleting them
   from the current table (so the moved row is not drawn on both pages); if nothing of
   the table fits, return `(None, new_table)`.

### Why this addresses finding #1 (no layout regression)

The v1 fix *split* short cells (orphaning lines) on documents that previously moved them
intact. This fix never splits a short cell — it keeps it together, now **without tearing
its row**. A single-cell row behaves exactly as before (moves whole to the next page).
Randomized measurement before/after (same 4000 configs):

| | content loss | non-termination | torn rows |
|---|---|---|---|
| pre-fix  | 0 | 0 | 10210 |
| post-fix | 0 | 0 |  6963 |

The 3247 eliminated torn rows are precisely the "short cell blank at the page bottom"
case. The 6963 remaining are *legitimate* splits of genuinely tall cells (a cell taller
than the page must span pages, leaving shorter siblings blank on the continuation — that
is correct and unavoidable, and unchanged by this fix). No new content loss, no new
non-termination.

### Termination

`move-whole-row` fires only when a cell placed *nothing*. On a fresh full page a cell
can place nothing only if its content is taller than an entire page — but the trigger is
a short (`< 4` line) paragraph or a first line that doesn't fit; both fit on a full page
(unless the page is shorter than ~3 lines, which no real report produces). So the moved
row always makes progress on the next page. Confirmed: 0 non-termination across 4000
configs at page heights down to 100 pt.

## Alternatives considered and rejected (with cost)

1. **v1: delete the `line_count < 4 and CELL` shortcut (−5 lines, 1 method).** Rejected
   at sign-off (finding #1): it makes short cells *split* (orphaned lines) on documents
   that previously moved them intact, and — critically — it does **not** fix the torn
   row, because with the shortcut gone the wrapping cell still splits per-cell (first
   line at the bottom next to `Label`, remainder next to a blank `Label` on page 2): the
   row is still torn, just with a first line showing. My probes confirm the per-cell
   split path also tears the row.
2. **Progress-based suppression the sign-off literally suggested** ("keep the shortcut
   when the cell fits on a fresh page; split only when it makes no progress"). Rejected:
   it requires threading the full page height through ~9 polymorphic `divide` signatures
   (Paragraph, Table, Row, Cell, Picture, Frame, Pagebreak, ToC, Index) — the "broad
   rewrite of the division engine" the brief puts out of scope — and it changes nothing
   for realistic geometry: a `< 4`-line cell paragraph *always* fits on a fresh page
   (my sweep never found one that didn't), so the shortcut would still fire and still
   tear the row. It only fixes the unreachable never-fits loop, i.e. it does not fix the
   reported bug.
3. **Move-whole-row via page-height threading (as #2) instead of the "placed nothing"
   signal.** Same ~9-signature churn for no additional behaviour: the "first child
   placed nothing" signal already identifies exactly the rows that must move, using
   information `divide` already has locally (+~35 lines across the 3 table methods, no
   signature change).

The brief names an **Invariant to restore**, so per principles §1.2/§2 the target is the
smallest change that restores it (keep the cell whole across the boundary without
tearing), not the smallest diff — this is +35 lines across 3 methods, the minimum needed
to move a row intact without duplicating it.

## Pre-existing, out-of-scope

The adversary's finding #4 (a paragraph on a page *shorter than one text line* loops in
the old step-2 `(None, self)`) is a pre-existing property that this fix neither
introduces nor removes; it is unreachable in real reports (my sweep terminates at 100 pt)
and the brief scopes the change to "the specific content-drop case … not any broad
rewrite of the division engine." Left as-is.

## Test — `gramps/plugins/test/cairodoc_table_pagination_test.py`

Drives the **production** path (principles §3.4), not a re-implementation of the math:

- builds a real `GtkDocTable/Row/Cell/Paragraph` — 3 short filler rows + one two-column
  `Label | wrapping-value` row;
- derives the page geometry **from production**: it measures the filler-row and
  wrapping-row heights with the real `GtkDocTableRow.divide` (given a huge height it
  returns the true row height) and sets `page_height = fillers + (filler_h + wrap_h)/2`
  so the `Label` cell fits at the bottom but the wrapping cell cannot — the brief's
  "wrapping cell on the last line of a normal page" case (**finding #3**);
- runs the production `CairoDoc.paginate` step in a bounded loop (the real
  `paginate_document` is an unbounded `while not paginate()`);
- asserts (a) pagination terminates and crosses a page boundary (`>= 2` pages, else the
  geometry is misconfigured and the test fails loudly rather than passing vacuously);
  (b) **no torn row** — no page holds a table row where one cell is blank while a sibling
  keeps its text — the core red→green signal; (c) every word of the wrapping cell's
  **`_plaintext`** survives (**finding #2** — `_cell_text` reads `child._plaintext`, the
  string `divide` actually truncates and `draw` actually renders, so a real drop would be
  caught).

Red→green (proven in-process against the isolated worktree, driving production):
- **without the fix**: FAIL — `torn == [(0, ['Label', '']), (1, ['', 'This is a long …'])]`;
- **with the fix**: OK — page 0 = filler rows only, page 1 = `['Label', 'This is a long …']`
  intact.

A sanity guard asserts the wrapping text is 2–3 lines at the cell width (so it takes the
keep-together branch); it fails loudly under font substitution rather than passing
vacuously.

### Headless

`libcairodoc` imports `gramps.gui.utils.SystemFonts` at load, but under GTK the bare
`gi` import needs no display, and Pango layout needs only fontconfig — so import + layout
succeed with `DISPLAY`/`WAYLAND_DISPLAY` unset (verified: the test runs under plain
`python3 -m unittest`, no xvfb/D-Bus/AT-SPI). Suitable for the headless C4 core runner.

## Verification performed

- In-process red→green driving the production `CairoDoc.paginate`/`divide` chain against
  the isolated worktree `/home/eddie/gramps/gramps-6.1-issue6324` (target commit
  0d9e148908, `maintenance/gramps61`): green with the fix, red (torn-row assertion) with
  `libcairodoc.py` reverted (test kept).
- 4000-config randomized regression before *and* after: 0 content loss, 0
  non-termination; torn rows 10210 → 6963 (only the short-cell-blank cases removed).
- `git apply --check` of `patch.diff` against a pristine `0d9e148908` checkout: clean for
  all three files.
- Black: all added lines ≤ 88 cols and standard-formatted (matches the file's existing
  style, e.g. the reused `list(map(...))`); the docker `black --check` gate could not be
  run here (docker requires approval unavailable in this sandbox) — a human/CI should run
  it at publish.

The docker-based C4 `run-verify.sh` needs container privileges not available in this
sandbox, so it could not be executed here; the in-process red→green above exercises the
identical production code path. A human should run C4 `run-verify.sh` and ideally eyeball
a Database Differences Report → PDF with a table row wrapping at a page bottom.

## Files / POTFILES

- `gramps/plugins/lib/libcairodoc.py` — the fix (3 divide methods).
- `gramps/plugins/test/cairodoc_table_pagination_test.py` — new test, no translatable
  strings → registered in `po/POTFILES.skip` (doc 16).

Note: the shared `gramps-6.1` worktree was found being reset mid-run by a concurrent
bundle (an `issue8622-builder-worktree-temp` stash appeared and the tree was wiped clean),
so all edits and citations here were made in a dedicated isolated worktree
`/home/eddie/gramps/gramps-6.1-issue6324` created at the target commit; `patch.diff` is
generated from it and applies cleanly to pristine `0d9e148908`.
