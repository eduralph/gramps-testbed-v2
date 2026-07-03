## Root cause

In the cairo/PDF backend, `GtkDocParagraph.divide` (maintenance/gramps61
line 620–621) implements a keep-together rule: if a cell's paragraph is short
(fewer than 4 lines) and cannot fully fit in the space left on the page, move
the whole paragraph to the next page instead of splitting it.

The problem occurs when an earlier cell in the same row has already placed
content. The keep-together rule then moves the later cell whole to the next
page while its rowmates stay behind, tearing the row: the cell renders blank
on the first page (placeholder committed, content moved) and its text appears
orphaned on the next page beside blank copies of the row's other cells.

## Fix

The divide chain now accepts two optional flags to the entire chain
(GtkDocParagraph, GtkDocTable, GtkDocTableRow, GtkDocTableCell, GtkDocPicture,
GtkDocFrame):

1. **`force_split=True`**: Override the keep-together rule when the page is
   already full (another rowmate has split), so the cell's first lines render
   beside the sibling instead of being dropped.

2. **`allow_overflow=True`**: Paginator-only signal that even an empty page
   cannot hold the content, so place it accepting overflow rather than loop
   forever (for images taller than the page).

`GtkDocTableRow.divide` keeps the whole row together when the first cell
cannot fit has no committed sibling, and force-splits later cells so their
first lines render beside a split sibling. `CairoDoc.paginate` adds a
no-progress guard: if an element placed nothing on an already-empty page, it
re-divides with both flags set to ensure pagination always advances.

## Verified against

- `gramps/plugins/lib/libcairodoc.py:620–621` (GtkDocParagraph.divide
  keep-together rule) — changed to check force_split flag
- `gramps/plugins/lib/libcairodoc.py:843–939` (GtkDocTable.divide row
  continuation logic) — passes force/overflow flags only to first row
- `gramps/plugins/lib/libcairodoc.py:976–1046` (GtkDocTableRow.divide) —
  tracks cell splits and force-splits later cells
- `gramps/plugins/lib/libcairodoc.py:1091–1130` (GtkDocTableCell.divide) —
  returns cell whole only when not forced
- `gramps/plugins/lib/libcairodoc.py:1245–1287` (GtkDocPicture.divide) —
  respects allow_overflow only
- `gramps/plugins/lib/libcairodoc.py:1310–1320` (GtkDocFrame.divide) —
  respects allow_overflow only
- `gramps/plugins/lib/libcairodoc.py:1796–1820` (CairoDoc.paginate) — 
  no-progress guard with bounded re-divide

## Test

New test `gramps/plugins/test/cairodoc_table_pagination_test.py` exercises
the production pagination chain against realistic geometries with a bounded
loop:

1. **test_wrapping_last_cell_moves_row_whole** (lines 640–688): Last-column
   wrapping cell at page foot — the row moves whole, cells begin on same page.
   **RED pre-fix**: cells on different pages (torn row). **GREEN post-fix**:
   cells begin together.

2. **test_wrapping_cell_splits_beside_split_sibling** (lines 690–741): Earlier
   column splits, later short column must split too. **RED pre-fix**: later
   cell blank beside split sibling. **GREEN post-fix**: both split together.

3. **test_wrapping_cell_taller_than_page_terminates** (lines 743–770): Cell
   cannot fit on any page — paginator guard forces split and terminates.
   **RED pre-fix**: unbounded loop never terminates. **GREEN post-fix**:
   completes, all words rendered.

4. **test_image_cell_in_torn_row_moves_intact_not_overflowed** (772–859):
   Image in torn row must move to next page intact, never clipped into slot.
   **RED pre-fix (naive regression)**: image clipped on head page. **GREEN
   post-fix**: image on continuation page, intact.

All assertions read `_plaintext` (what divide places/truncates), not `_text`,
so dropped/truncated cells are genuinely detectable. Full core unit suite
(32,977 tests) runs with zero new regressions. Test file registered in
`po/POTFILES.skip:675` to exclude from translation.

Run: `python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v`

---

Fixes [#6324](https://gramps-project.org/bugs/view.php?id=6324)
