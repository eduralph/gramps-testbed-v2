# build-notes.md — issue 6324 / pdf-table-cell-wrap-page-break

Builder rationale (for the human; withheld from the reviewer). Target:
`gramps-project/gramps` @ `maintenance/gramps61` (checkout `gramps-6.1`).

## Root cause

In the cairo/PDF backend, when a table row lands near the foot of a page and a cell's short
paragraph must wrap, the keep-together rule (`GtkDocParagraph.divide`:
`line_count < 4 and parent._type == "CELL"` → `(None, self)`) moves the cell whole, but the
row's already-committed sibling cells stay on the current page — so the cell renders **blank**
here while its text lands on the next page (dsblank, Mantis 6324: "the cell prints no text at
all"). The division chain drops the cell instead of keeping the whole row together / splitting
every cell at the same boundary.

## What the fix does — a **two-signal** divide protocol

The whole `divide` chain (`GtkDocParagraph`, `GtkDocTable`, `GtkDocTableRow`,
`GtkDocTableCell`, `GtkDocPicture`, `GtkDocFrame`) gains **two** optional flags, and the
paginator drives them:

- **`force_split`** — "the row/page is already as large as it will get; split what you can
  here." Overrides the keep-together rule so a short cell paragraph renders its first lines
  beside its rowmates instead of being dropped.
- **`allow_overflow`** — the stronger, paginator-only signal: "even a fresh empty page
  cannot hold this, so place it here accepting overflow (else pagination loops forever)."
  Only an **unsplittable** element (image / frame / a single line taller than a whole page)
  ever consults it.

`GtkDocTableRow.divide` keeps the whole row together when the first cell that cannot fit is
reached with no committed sibling (`return (None, self)`), and otherwise force-splits later
cells so their first lines render beside a split sibling. `GtkDocTable.divide` hands the
non-fitting row (and the rest) to a continuation table. `CairoDoc.paginate` adds a
**no-progress guard**: if an element placed nothing yet asked to move on **and the current
page is already empty**, it re-divides the continuation with `force_split=True,
allow_overflow=True`, so pagination always advances.

## The picture-arm regression (adversary's one confirmed finding) — fixed by the split

The naive single-flag version forced an **image** in a torn row (a sibling text cell split)
to place-with-overflow into the tiny slot left, clipping ~100pt past the page edge, even
though the image would fit intact on the next page. The two-signal design fixes this: a
torn row forces the split **without** `allow_overflow`, so `GtkDocPicture.divide` /
`GtkDocFrame.divide` **move the image to the next page intact** instead of clipping it. The
genuine "image taller than any page" case still terminates, because there the paginator's
no-progress guard supplies `allow_overflow=True` on an empty page.

Where the meanings meet in the cell: `GtkDocTableCell.divide` returns the cell **intact**
(`(None, self)`) only when NOT forced — so the row can move the whole row or force the
split. When forced, it falls through to the continuation path: a splittable child splits
(first lines placed here), an unsplittable one that still won't fit is carried to a
continuation cell — **blank on this page, intact on the next** — never dropped.

## Tests & verification

`gramps/plugins/test/cairodoc_table_pagination_test.py` drives the production
`CairoDoc.paginate` + `divide` chain against realistic geometries (Pango on an in-memory
cairo surface; headless) with a bounded paginator loop so a non-terminating case is
*reported*, not hung. 4 tests:

1. last-column wrapping cell → whole row moves (cells begin on the same page);
2. earlier column splits → the later short column splits beside it (not blank);
3. cell taller than any page → the no-progress guard terminates, every word rendered;
4. **image in a torn row → moves intact to the continuation page, never clipped** (the
   picture-arm regression guard — asserts the image is on exactly one page and it is the
   TALL continuation page, not the cramped head page).

Assertions read `_plaintext` (what `divide` actually places/truncates), not `_text`, so a
dropped/truncated cell is genuinely detectable; the tear oracle is `_first_page` equality.

- **Verified in the Docker engine image** (`gramps-testbed:ubuntu-6.1.0`):
  - **RED** (production reverted, test kept): tests 1–3 fail (torn row / non-termination) —
    the #6324 symptoms; the picture-arm test (4) passes on the unpatched tree, because the
    original code already moves an image to the next page — it is a guard against the
    regression the naive fix introduced.
  - **GREEN** (fix applied): all 4 pass.  Confirmed self-contained: applying
    `patch.diff` alone to a pristine `maintenance/gramps61` yields 4/4.
- **Full core unit suite**: 32977 tests, only the 7 pre-existing baseline failures (zip
  imports + WebCal/NarrativeWeb — HTML reports, not cairo; identical on the clean
  checkout). **Zero new regressions** from this 130-line change to the shared rendering lib.

## Notes / scope

- The four `divide` stubs that never return `(None, self)` (`GtkDocBaseElement` base,
  PAGEBREAK, TOC, INDEX) are intentionally left unchanged — the paginator's no-progress
  guard and the row/table force paths never reach them with the new args, so no TypeError
  is possible (checked).
- Pre-existing issues out of scope and unchanged pre/post: the doc-level paragraph
  continuation `AttributeError` on `self._parent._type`, and row heights stored in Pango
  units — neither is used or worsened by this diff.

## Citations (maintenance/gramps61)

- `gramps/plugins/lib/libcairodoc.py` — `GtkDocParagraph.divide` (keep-together + the
  `_place_whole`/overflow gates), `GtkDocTable.divide` (row continuation),
  `GtkDocTableRow.divide` (`cell_split` + force logic), `GtkDocTableCell.divide`
  (forced fall-through), `GtkDocPicture.divide` / `GtkDocFrame.divide` (overflow only under
  `allow_overflow`), `CairoDoc.paginate` (the `page_is_empty` no-progress guard).
- `po/POTFILES.skip` — register the new test.
