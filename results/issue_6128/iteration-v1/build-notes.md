# Build notes — issue 6128 / book-report-same-name-styles-collide

## Root cause (target: gramps-project/gramps @ maintenance/gramps61)

A Book Report renders every item into **one shared document** carrying **one
shared stylesheet**. `append_styles` (`gramps/gen/plug/report/_book.py:726-764`
on the unpatched branch) reads each item's selected stylesheet and adds its
paragraph/draw/table/cell styles into that single `selected_style` **keyed by
the bare style name** (`add_paragraph_style(this_style_name, …)` etc.).

Two items of the same report type define styles under identical names (two
Descendant Reports both define `DR-Title`). The second item's `add_*_style`
overwrites the first item's same-named entry in the flat shared sheet. At render
time the document resolves a style **lazily, by name**, against that shared sheet
(verified in `gramps/plugins/docgen/asciidoc.py:228-230`:
`self.get_style_sheet().get_paragraph_style(style_name)` — every backend does the
same). So both items' reports — whose style references are hard-coded as
`self.doc.start_paragraph("DR-Title")` — resolve `DR-Title` to the **last-written**
values. Item-1's 14pt title renders at item-2's 48pt.

The render loop is *sequential* (`cl_book` at `gramps/cli/plug/__init__.py:906`,
`_BookReportDialog.make_book` at `gramps/gui/plug/report/_bookdialog.py:1056`),
but the collision is in the *shared name space*, not in concurrency: page-oriented
backends (ODF/RTF/LaTeX) also pre-declare styles by name in the output, so merely
swapping the doc's active stylesheet per item at render time would still collide
in the output format. The fix must make the names **distinct**.

## Fix — namespace each item's styles + a per-item document proxy

Invariant to restore: each book item is rendered with the values it was
configured with. Smallest change that restores it (principles §1.2/§2), not the
smallest diff:

1. `append_styles(selected_style, item, prefix="")` now stores each style under
   `prefix + name` (`_book.py`). Default `prefix=""` keeps the old behaviour for
   any other caller; book callers pass a per-item prefix.
2. `book_item_style_prefix(item_number)` → `"BI%03d-"` — a per-item namespace in
   the same character set (upper-case, digit, hyphen) as existing report style
   names like `DR-Title`, so it survives every backend's style-name handling
   exactly as the already-distinct style names from *different* report types do
   (those have always co-existed in the book sheet without trouble).
3. `BookItemStyleProxy` — a thin wrapper around the shared document. It rewrites
   the style-name argument of every doc method that takes one
   (`start_paragraph/start_table/start_cell/add_media`, and the DrawDoc
   `draw_path/draw_box/draw_text/center_text/rotate_text/draw_line`) to the
   item's prefixed name, and delegates everything else to the shared doc via
   `__getattr__`. `get_style_sheet()` returns the item's **own, un-prefixed**
   stylesheet, so report code that reads its styles back by their original name
   (common in graphical reports) keeps working.
4. `add_book_item_styles(selected_style, item, doc, item_number)` ties it
   together: collate under the prefix, build the proxy, install it as the item's
   document (`item.option_class.set_document`). It must run **before** the report
   is constructed, because `Report.__init__` grabs its doc from
   `options_class.get_document()` (`gramps/gen/plug/report/_reportbase.py:51`).
5. Both production callers route through it: `cl_book`
   (`gramps/cli/plug/__init__.py:884-901`) and `make_document`
   (`gramps/gui/plug/report/_bookdialog.py:1033-1043`), each switched to
   `enumerate(...)` to supply `item_number`. (The old `if obj:` guard was dead —
   `obj` is always a truthy 2-tuple — so moving the collation ahead of report
   construction changes nothing observable.)

Both callers and the test share the one production implementation
(`add_book_item_styles`); the test exercises the real path, not a copy.

## Why the proxy, not a cheaper symptom guard

Rejected: **swap the doc's active stylesheet between items at render time**
(`doc.set_style_sheet(item_sheet)` before each `rpt.write_report()`). Diff would
be smaller (~6 lines in each caller, no proxy class), but it does **not** restore
the invariant for page-oriented backends: ODF (`odfdoc.py`), RTF, and LaTeX emit a
named style table in the document header from the stylesheet, so two items'
`DR-Title` still collide in the *output* even though each was "active" when
written. It would fix only the ascii/plain backends — a symptom guard, not the
cause. The proxy + namespacing removes the cause (no two items ever share a name
in the shared sheet) at the cost of one ~45-line wrapper class.

Rejected: **rename styles in place without a proxy.** The references are
hard-coded in ~every report's source (`start_paragraph("DR-Title")`); there is no
way to make them resolve to prefixed names without an interception seam. The proxy
is that seam and is the minimal one.

## Test — `gramps/gen/plug/report/test/book_styles_test.py`

Data-layer, import-light (no `gi.repository.Gtk` / `gramps.gui`; importing `_book`
pulls only `gi`/GLib, no display — safe for the headless C4 runner). It:

- writes **real** stylesheet savefiles via the production `StyleSheetList.save()`
  so the production `append_styles` reads them back through the real
  `StyleSheetList` parse path (not a stubbed stylesheet);
- builds two (and, in a second test, three) items whose same-named style carries
  different font sizes, drives `add_book_item_styles`, then renders each item
  through the document **it writes through** (`option_class.get_document()` — the
  proxy with the fix), resolving the style exactly as real backends do;
- asserts each item keeps its own size.

To make the C4 red leg (production reverted, test kept) fail on the **bug** rather
than a missing symbol, `add_book_item_styles` is imported lazily inside the
helper; absent, the helper reproduces the *pre-fix production behaviour* (flat
`append_styles` onto the raw shared doc — what `cl_book` did before this change),
so the red leg asserts the actual collision. This is the pre-fix path, not a
re-implementation of the fix; the green path routes through real production.

Local red→green (docker C4 runner needs an approval not available in this
session; the official C4-verify re-runs at Check):
- with fix: `test_two… → [14, 48]`, `test_generalizes… → [10, 20, 30]` — PASS.
- production reverted, test kept: `[48, 48]` and `[30, 30, 30]` — FAIL with
  "the second item's style overwrote the first's". Assertion-level red, exact
  defect reproduced.

The second test uses a different style name (`AB-Heading`) and three items, per
the brief SELF-TEST: the property holds for *any* pair sharing a name, not the
`DR-Title`/Descendant-Report repro.

## Files / housekeeping

- New core files registered in `po/POTFILES.skip` (tests, no translatable
  strings): `gramps/gen/plug/report/test/__init__.py` and `…/book_styles_test.py`.
- `gramps/gen/plug/report/__init__.py` exports `add_book_item_styles` and
  `BookItemStyleProxy`; the CLI/GUI imports were updated (`append_styles` is still
  exported and unused-by-callers but kept public/back-compatible).
- `black` (26.5.0, gramps' formatter) reports all six touched `.py` files
  unchanged — commit-ready for the target's pre-commit hook.
