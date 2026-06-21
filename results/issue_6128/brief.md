# Brief — issue 6128 / book-report-same-name-styles-collide

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** book-report-same-name-styles-collide
- **Defect:** When a Book Report contains two reports of the same type whose styles differ
  (e.g. two Descendant Reports, one with a 14-point title style and one with a 48-point title
  style), both reports render with one item's style — the second item's style wins, so the
  first report's title is wrong. The two items' same-named styles collide in the book's shared
  stylesheet.
- **Success criterion:** A book with two same-type items that define styles under the same
  name but with different values renders **each item with its own style values** (item-1 title
  14pt, item-2 title 48pt — not both 48pt). Demonstrable by C4-verify on a test that builds such
  a two-item book and asserts the collated/applied styles preserve both items' distinct values.
- **Invariant to restore:** Each book item is rendered with the style values it was
  configured with; collating styles from multiple items into the book document MUST NOT let one
  item's style overwrite another item's same-named style. (Internal Gramps report rule — book
  items are independently-styled units; no external canon.) SELF-TEST: the property is over
  *any* pair of items sharing a style name, not the specific "Descendant Report" repro — a fix
  must keep per-item styles distinct in general, not special-case one report type.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** the per-item style collation in `gramps/gen/plug/report/_book.py`. Root cause:
  `append_styles` (`_book.py:726-764`) reads each item's selected stylesheet and adds its
  paragraph/draw/table/cell styles into a single shared `selected_style` keyed by style name —
  `add_paragraph_style(this_style_name, …)` etc. — so a second item contributing a style with
  the same name overwrites the first item's, and both items then resolve that name to the same
  (last-written) style. The fix must keep each item's styles distinct in the book document (so
  each item's report resolves its own values). Mechanism — how the styles are kept distinct and
  how each item's references resolve to its own — is Do's to choose. / out of scope: the Style
  Editor UI; non-book single reports; document backends.
- **Repro instruction:** On maintenance/gramps61: remove/rename `report_options.xml`; Reports →
  Books → Book Report; new book with two text Descendant Reports; via the Style Editor give the
  first a 14-point title style and the second a 48-point title style; generate (PDF) and observe
  both titles render at 48-point.
- **Test file:** gramps/gen/plug/report/test/book_styles_test.py (new core `test/` package —
  add `__init__.py`). A data-layer test driving the **production** book style-collation/rendering
  path (`append_styles` plus the document the book builds) with two items whose same-named styles
  carry different values, asserting each item keeps its own values. It MUST exercise the real
  book collation, not a parallel reimplementation of `append_styles`.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds `gramps/gen/plug/report/test/__init__.py` and
  `gramps/gen/plug/report/test/book_styles_test.py` (tests, no translatable strings) → register
  both in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/gen/plug/report/_book.py` — only black/license reformat commits; no style-collision fix.
  Merged history clean; closed-PR search by this path advised at review.
- **Mantis:** 6128
- **Disposition hint:** likely-fix

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: BookItemStyleProxy is incomplete: write_styled_note(styledtext, format, style_name) in TextDoc is not overridden, so any book-eligible report that calls it (Detailed Descendant, Family Group, Complete Individual, Detailed Ancestral — all REPORT_MODE_BKI) passes the un-prefixed style name to the shared document, which holds only prefixed names and falls back to defaults. Add write_styled_note to the proxy's overridden methods (prefix the style_name argument before delegating), and audit draw-report equivalents for any further style-name-bearing methods not yet covered.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
