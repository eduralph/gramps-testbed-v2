## Root cause

A Book Report renders every item into one shared document with one shared stylesheet (a hard requirement of ODF backends, which emit the whole stylesheet once at `open()`). Two items of the same report type define styles under identical names (e.g. two Descendant Reports both define "DR-Title"), and `append_styles()` collated them into the flat shared sheet keyed by bare style name, so a second item's same-named style overwrote the first's. Both items then resolved that name to the last-written values, rendering both titles at the second item's size instead of preserving each item's distinct style values.

## Fix

The fix implements per-item style-name namespacing within the single shared stylesheet. Each item's styles are stored under a unique prefix (e.g., "BI000-DR-Title", "BI001-DR-Title") via `_add_namespaced_styles()`, which also re-points draw-style embedded paragraph references. A new `BookItemStyleProxy` class wraps the shared document for each item and prefixes every style-name-bearing method argument before delegating, so baked-in bare references resolve to that item's namespaced values. The proxy covers the complete abstract document interface: `start_paragraph`, `start_table`, `start_cell`, `write_styled_note`, `add_media` (TextDoc) and `draw_path`, `draw_box`, `draw_text`, `center_text`, `rotate_text`, `draw_line` (DrawDoc), plus stylesheet read/write methods (`get_style_sheet`, `set_style_sheet`) to handle reports that mutate styles at run time. The call sites in the CLI and GUI book report generation are switched from flat `set_document()` + post-hoc `append_styles()` to a single `add_book_item_styles()` call with enumerated item numbers.

## Verified against

- `gramps/gen/plug/report/_book.py:155-165` — `book_item_style_prefix()` generates a unique per-item namespace.
- `gramps/gen/plug/report/_book.py:95-129` — `_add_namespaced_styles()` copies styles under the prefix and re-points draw-style embedded paragraph references.
- `gramps/gen/plug/report/_book.py:175-261` — `BookItemStyleProxy` class overrides all style-name-bearing methods and stylesheet read/write.
- `gramps/gen/plug/report/_book.py:264-280` — `add_book_item_styles()` orchestrates collation and proxy install.
- `gramps/cli/plug/__init__.py:878-897` — CLI call site updated to enumerate items and call `add_book_item_styles()` before report construction.
- `gramps/gui/plug/report/_bookdialog.py:1033-1041` — GUI call site updated similarly.
- `gramps/gen/plug/report/__init__.py:52-60` — exports include `add_book_item_styles` and `BookItemStyleProxy`.

## Test

The regression test `gramps/gen/plug/report/test/book_styles_test.py` drives the production book style-collation path (`add_book_item_styles` → `append_styles` → `BookItemStyleProxy`) against a recording document that resolves styles by name exactly as the real backends do. It asserts each item keeps its own configured values over:

- Two same-type items with distinct title sizes (the reported Descendant-Report case, 14pt vs 48pt).
- `write_styled_note()` method (used by every REPORT_MODE_BKI textual report for notes), keeping per-item sizes distinct (9pt vs 33pt).
- Draw-style embedded paragraph references (testing `draw_box` with AC2-box/AC2-Normal), ensuring the paragraph reference resolution stays per-item (11pt vs 22pt).
- Run-time `set_style_sheet()` mutations (the AncestorTree/DescendTree/FanChart pattern), verifying one item's modification does not leak into another's.
- Generalization across three items and an arbitrary shared style name, confirming the fix applies generally, not just to the two-item Descendant-Report case.

The test is not special-cased to the reported scenario; it verifies the fix over any pair (or more) of items sharing a style name with different values.

Fixes #6128
