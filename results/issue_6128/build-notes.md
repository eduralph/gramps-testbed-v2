# Build notes — issue 6128 / book-report-same-name-styles-collide

Target: `gramps-project/gramps @ maintenance/gramps61`. All line cites below are
post-patch positions in the patched files (what gets committed); pre-patch cites
are against `upstream/maintenance/gramps61`.

## Root cause (two sentences)

A Book Report renders every item into ONE shared document carrying ONE shared
stylesheet; `append_styles` (`_book.py:726-764` pre-fix) collated each item's
styles into that flat sheet keyed by the *bare* style name, so a second item of
the same type (two Descendant Reports both defining "DR-Title") overwrote the
first item's same-named style. Both items' reports then referenced "DR-Title"
and the shared sheet resolved it to the last-written value — both titles render
at 48pt instead of 14pt/48pt.

## Why a single shared stylesheet must stay (the historical trap)

The notes thread (notes.json) records that 6128 was "fixed" in 2013 (r20572) by
giving each item its *own* stylesheet and swapping `doc.set_style_sheet(...)`
before each item rendered — and then **reverted** (r21575/76/77,
commit a5b4759f) because "this fix broke ODF output which requires the
definition of a single large stylesheet." ODF emits the whole stylesheet once at
`doc.open()`, so a post-open per-item swap has no effect. So the correct fix
must keep ONE shared stylesheet set once before `open()`, yet make same-named
styles from different items distinct. That rules out the reverted approach and
points at **namespacing within the single shared sheet**.

## Mechanism chosen — per-item namespace + a document proxy

- `append_styles(selected_style, item, prefix="")` (`_book.py:779`) now stores
  every style under `prefix + name` via the shared `_add_namespaced_styles`
  helper (`_book.py:747`); it returns the item's own (un-prefixed) stylesheet.
  `prefix=""` preserves the historical behaviour for any other caller.
- `book_item_style_prefix(item_number)` → `"BI%03d-"` (`_book.py:802`): a unique
  per-item namespace using the same character set (upper-case/digits/hyphen) as
  report style names, so it survives every backend's style-name handling.
- `BookItemStyleProxy` (`_book.py:815`) wraps the shared document for one item
  and prefixes the style-name argument of every style-name-bearing
  `TextDoc`/`DrawDoc` method before delegating, so the report's baked-in bare
  references (`self.doc.start_paragraph("DR-Title")`) resolve to that item's
  namespaced style. `get_style_sheet` returns the item's own un-prefixed sheet;
  everything else delegates unchanged via `__getattr__`.
- `add_book_item_styles(selected_style, item, doc, item_number)` (`_book.py:904`)
  orchestrates collate + proxy install via `item.option_class.set_document`.
  It MUST run before the report is built, because `ReportBase.__init__` grabs its
  document at construction (`gramps/gen/plug/report/_reportbase.py:51`).
- Call sites switched from `set_document(doc)` + post-hoc `append_styles` to a
  single `add_book_item_styles(...)` before `get_write_item()`, with `enumerate`
  for the item number: CLI `cl_book` (`gramps/cli/plug/__init__.py`, was
  `_book` import line 82 / loop 880-898) and GUI `BookDialog.make_document`
  (`gramps/gui/plug/report/_bookdialog.py`, was import 76 / loop 1033-1041).
- Exports updated in `gramps/gen/plug/report/__init__.py` (add
  `add_book_item_styles`, `BookItemStyleProxy`; keep `append_styles`).

## Addressing the Iteration-1 carry-forward (the rejection)

The v1 sign-off rejected the proxy as **incomplete**: `write_styled_note` was
not overridden, so every REPORT_MODE_BKI textual report that writes notes
(Detailed Descendant/Ancestral, Family Group, Complete Individual) passed a bare
style name to the shared document and fell back to defaults. I audited the full
abstract document interface on the target branch and overrode the **complete**
set of style-name-bearing methods:

- `gramps/gen/plug/docgen/textdoc.py`: `start_paragraph` (133), `start_table`
  (150), `start_cell` (177), `write_styled_note` (216) ← the gap, now at
  `_book.py:868`, `add_media` (270).
- `gramps/gen/plug/docgen/drawdoc.py`: `draw_path` (103), `draw_box` (109),
  `draw_text` (115), `center_text` (121), `rotate_text` (127), `draw_line` (133).
- `string_width`/`string_multiline_width` take a FontStyle *object*, not a name
  — correctly NOT prefixed (delegated).
- Confirmed reports do not call a doc-level `write_note` directly (only
  `write_styled_note` does, internally, in each backend — grep of
  `gramps/plugins/`), so prefixing at `write_styled_note` is sufficient.

## Two deeper gaps the audit found beyond the carry-forward

The carry-forward also said "audit draw-report equivalents." Doing so surfaced
two correctness holes a write_styled_note-only patch would still have:

1. **Run-time `set_style_sheet`.** AncestorTree/DescendTree/FanChart (all BKI
   draw reports) read-modify-write the doc stylesheet at render time
   (`gramps/plugins/drawreport/fanchart.py:349`,
   `ancestortree.py:811`, `descendtree.py:1529`). A bare `__getattr__`
   delegation would route their `set_style_sheet(...)` to the shared doc and
   **replace the whole shared sheet**, dropping every other item's namespaced
   styles. The proxy now overrides `set_style_sheet` (`_book.py:849`) to keep the
   item's own view and re-namespace only this item's styles back into the shared
   sheet; `get_style_sheet` (`_book.py:846`) returns the item's own sheet.
2. **Embedded paragraph reference inside a draw style.** A `GraphicsStyle`
   stores the *name* of the paragraph style it renders text with
   (`gramps/gen/plug/docgen/graphicstyle.py:158/174`), and draw backends resolve
   it against the same shared sheet (`svgdrawdoc.py:288-289`,
   `libcairodoc.py:1703`). Prefixing only the draw-style name would leave that
   embedded reference bare → collision again. `_add_namespaced_styles`
   (`_book.py:766-770`) clones each `GraphicsStyle` and re-points its `para_name`
   to `prefix + para_name`.

These are why the chosen fix is the *complete* proxy, not the minimal
write_styled_note add-on the carry-forward literally named.

## Alternatives considered and rejected (with cost)

- **Reverted-2013 per-item stylesheet swap** (each item its own sheet,
  `set_style_sheet` before each render). Smaller diff in `_book.py` (it deletes
  the collation loop, ~20 lines) but it is the exact change upstream reverted
  because it breaks ODF (single-stylesheet-at-open backends). Rejected on
  *correctness*, not size: it reintroduces a known regression.
- **Prefix the names but skip the proxy, rewriting references inside each doc
  backend instead.** That spreads the bare→prefixed translation across every
  `TextDoc`/`DrawDoc` subclass (asciidoc, htmldoc, rtfdoc, latexdoc, odfdoc,
  svgdrawdoc, libcairodoc, … — 7+ files, each of the 11 methods) versus one
  proxy class. Strictly more code, in more files, and out of the brief's scope
  (`document backends` are explicitly out of scope). Rejected.

## Verification (red → green)

The bundle test `gramps/gen/plug/report/test/book_styles_test.py` drives the
production path (`add_book_item_styles` → `append_styles` →
`BookItemStyleProxy`) against a `_RecordingDoc` that resolves a style by name
exactly as the real backends do, and asserts each item keeps its own value over:
the reported title (`start_paragraph`), `write_styled_note`, a draw style's
embedded paragraph ref (`draw_box`), a run-time `set_style_sheet` mutation, and a
3-item arbitrary-name generalization (self-test: not special-cased to
"DR-Title").

The C4 docker runner was not invokable in this Do session (the harness blocked
`run-verify.sh` / sandboxed python against the worktrees), so I verified the
contract directly:

- **RED** — against the installed pre-fix gramps (`append_styles` flat, no
  `add_book_item_styles`): all 5 tests FAIL, e.g.
  `[48, 48] != [14, 48]` and `[33, 33] != [9, 33]` — the collision reproduced.
- **GREEN** — binding the *exact* patched `_book.py` functions into the real
  `gramps.gen.plug.report._book` module (same real `StyleSheet`/`GraphicsStyle`
  classes) via `/tmp/green_runner.py`: all 5 tests pass.

Check's C4-verify gate re-runs the official docker red/green and must be the
authoritative green before sign-off.

## Commit-readiness

`black` 26.5.0 run over all five touched/added files; `_book.py` reformatted,
the other four already conform. `git apply --check` of `patch.diff` is clean
against the target tree. Both new files registered in `po/POTFILES.skip`
(tests, no translatable strings).
