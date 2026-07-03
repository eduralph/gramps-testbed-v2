# Build notes — issue 5733 (odf-drawchart-text-not-scaled)

Target: `gramps-project/gramps @ maintenance/gramps61`.
Citations are `path:line` on that branch (files fetched from
`raw.githubusercontent.com/.../maintenance/gramps61`).

## Root cause (traced end-to-end)

A graphical tree report is run as (`gramps/cli/plug/__init__.py:781-784`):

```
my_report.doc.init()      # ODF: write the named draw styles
my_report.begin_report()  # tree report: scale_styles() → mutate the style sheet
my_report.write_report()  # draw the boxes
```

- `ODFDoc.init()` writes, up front, the automatic paragraph/text styles for
  every style in the sheet — including the per-style text style
  `F<name>` whose `fo:font-size` is taken from `font.get_size()` at that
  moment (`gramps/plugins/docgen/odfdoc.py:651-686`, the block writing
  `<style:style style:name="F%s" …>`).
- The graphical report (e.g. Descendant chart) then, in `begin_report()`,
  applies "scale tree to fit" by scaling the style sheet's **fonts** in
  `scale_styles()` (`gramps/plugins/drawreport/descendtree.py:1504-1529`:
  `font.set_size(font.get_size() * amount)` … `self.doc.set_style_sheet(...)`).
  That happens **after** `init()` already serialised the `F<name>` styles.
- At draw time, `draw_box`/`draw_text`/`center_text` emit the box text as a
  `<text:span text:style-name="F<name>">` (`odfdoc.py:1884-1885, 1932-1933,
  1968-1969`). That named style still carries the **unscaled** size, so ODT
  box text renders full-size and overflows the shrunk boxes.
- The cairo (PDF) backend has no such pre-written styles: it reads the
  paragraph style's font at draw time (`gramps/plugins/lib/libcairodoc.py:1369-1370`
  via `fontstyle_to_fontdescription`, `:173-174`), so it sees the *scaled*
  font and PDF text scales correctly. Hence the format-dependent behaviour the
  reporter saw.

`get_style_sheet()` returns a deep copy (`gramps/gen/plug/docgen/stylesheet.py:298-312,
363-369`), which is why the report persists the scaled sheet with
`set_style_sheet` (`descendtree.py:1529`); at draw time
`ODFDoc.draw_*` re-reads `get_style_sheet()` and therefore *does* see the
scaled font size — it just wasn't using it for the emitted text.

## The fix (restores the invariant, minimal, in-scope)

Invariant to restore: the backend must render text at the *effective* font
size the report computed, including the report's scale factor.

At draw time the scaled size is already available (`pstyle.get_font().get_size()`
— the same value cairo renders and the same value `draw_text`/`center_text`
already use for the frame height, `odfdoc.py:1880, 1960`). The only gap is that
the text **span** referenced a style baked at `init()` time. So:

1. Factor the `F<name>` text-properties body into a shared helper
   `_draw_text_properties(style)` used by **both** `init()` (writing the named
   style once) and the draw path — one implementation, no drift.
2. `init()` records each style's `F<name>` properties in `self._draw_text_props`.
3. New `_scaled_text_style(para_name)`: recompute the properties from the
   **current** (post-scale) font; if unchanged, return the existing `F<name>`
   (so unscaled output is byte-identical); if changed, register and return an
   automatic text style `FScaled<n>` carrying the current size.
4. `add_scaled_text_styles()` flushes those into `<office:automatic-styles>`
   via `cntnt2` at `finish_cntnt_creation()` — the **same** late-flush
   mechanism the styled-note styles already use (`odfdoc.py:825-842`,
   `finish_cntnt_creation` at `:774-790`). No buffer re-sequencing.
5. The three draw methods reference `_scaled_text_style(para_name)` for the
   span (`draw_text`, `draw_box`, `center_text`).

This mirrors the cairo behaviour (decide the size at draw time) rather than
guessing it up front — it removes the cause *within the ODF backend* (a stale,
pre-serialised size) rather than papering over it.

### Alternatives considered, with cost

- **Move `begin_report` work into `init()`** (so the sheet is scaled before the
  styles are written): explicitly **out of scope** — the brief notes this was
  committed and reverted twice upstream as "worse than the original"
  (a design-discussion item, per paulfranklin). Not pursued.
- **Move the whole paragraph/text/draw style-writing block out of `init()` into
  `close()`/`finish_cntnt_creation()`** so it serialises the scaled sheet:
  that block is `odfdoc.py:513-750` (~237 lines) and is written into `cntnt`
  interleaved with the `<office:automatic-styles>` open (in `cntnt2`) / close
  (in `cntnt`) and, later, the body content that `draw_*` appends. Relocating
  it means splitting the automatic-styles emission into its own buffer and
  re-sequencing the whole `cntnt1`/`cntnt2`/`cntnt` assembly
  (`finish_cntnt_creation`, `odfdoc.py:774-790`) that the styled-note, photo,
  table and cell paths all depend on — far more surface, and it changes the
  serialised output for *every* ODT report, not just scaled graphical ones. My
  change instead is: −35/+12 lines in the `init()` F-block, +3 one-line span
  swaps, +1 call in `finish_cntnt_creation`, and 3 new small methods
  (~65 lines) — and leaves unscaled output byte-for-byte identical (guarded by
  `test_unscaled_output_unchanged`).

## Test

`gramps/plugins/test/odfdoc_drawscale_test.py` (core `*_test.py` suffix;
registered in `po/POTFILES.skip` — a test, no translatable strings).

It drives the **production** ODF draw path:

- builds a minimal style sheet (one paragraph style + one draw box style — the
  exact shape a tree report uses),
- `ODFDoc.open()/init()`,
- applies the scale the way a graphical report does — `get_style_sheet()` →
  `font.set_size(size*amount)` → `set_style_sheet()` (the report→doc contract,
  `descendtree.scale_styles` `:1510-1529`); this is *input*, not a
  reimplementation of the backend's size emission,
- calls the real `draw_box` / `center_text` (which route through
  `_scaled_text_style` + `add_scaled_text_styles`),
- parses the emitted content.xml and asserts the drawn span's `fo:font-size`
  equals the scaled size — and equals the size the cairo backend would render
  (both read the same scaled sheet at draw time).

`test_unscaled_output_unchanged` guards that, absent a scale, the span still
references the original `F<name>` at the base size (no regression to the common
case). The test is import-light (only `gramps.gen` / `gramps.plugins.docgen.odfdoc`;
`odfdoc` and `libodfbackend` pull in no `gi`/`gramps.gui`), so it runs under the
headless C4 runner.

Expected C4: **red** pre-fix (span → `F<name>` at unscaled 16.0pt, expected
8.0pt), **green** post-fix (span → `FScaled1` at 8.0pt).

## Verification status

- `patch.diff` applies cleanly to a pristine `maintenance/gramps61` tree
  (`git apply --check` → "APPLIES CLEAN").
- `python3 -m py_compile` passes for both changed/added Python files.
- Formatting written to black defaults (88-col); `black` is not installed in
  this session and pip install is offline, so I hand-checked line lengths and
  black-stable wrapping rather than running it — worth a `black` pass at publish.
- **The engine C4 runner (`engine/scripts/ubuntu/run-verify.sh`) could not be
  executed in this session:** it launches Docker and every invocation was
  blocked by the sandbox (approval denied). I did not hand-roll a `docker run`
  (no timeout) nor fabricate a pass. The red→green check therefore still needs
  to run — Check's C4-verify gate runs exactly this and will confirm it.

  Manual reproduction of the original bug (for sign-off), on `maintenance/gramps61`:
  generate a graphical **Descendant Chart** (≥3 generations) to ODT,
  letter/portrait, Size option "Scale tree to fit the size of the page"; open in
  LibreOffice — pre-fix the boxes shrink but the text overflows them; with the
  patch the text scales down with the boxes (matching the PDF output).
