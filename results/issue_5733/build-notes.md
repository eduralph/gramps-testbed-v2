# Build notes — issue 5733 (odf-drawchart-text-not-scaled), iteration 2

Target: `gramps-project/gramps @ maintenance/gramps61`.
Citations are `path:line` on that branch (worktree `/home/eddie/gramps/gramps-6.1`,
detached at the gramps61 tip `0d9e148908`).

## What iteration 1 got right (kept)

The root cause and the shape of the fix are unchanged from iteration 1 and were
not the reason for rejection — sign-off accepted the *approach* but flagged two
concrete defects it introduced plus one weak test assertion. Recap of the cause:

- A graphical tree report runs `doc.init()` **then** `begin_report()`
  (`gramps/cli/plug/__init__.py`), and `begin_report` scales the style sheet's
  **fonts** via the report's `scale_styles`
  (`gramps/plugins/drawreport/descendtree.py:1504-1529`:
  `font.set_size(font.get_size() * amount)` … `self.doc.set_style_sheet(...)`).
- `ODFDoc.init()` has **already** serialised, up front, a named `F<name>` text
  style whose `fo:font-size` is taken from the *unscaled* font
  (`gramps/plugins/docgen/odfdoc.py:651-686` on the unpatched branch).
- The draw methods emit box text as `<text:span text:style-name="F<name>">`
  (`odfdoc.py:1885, 1933, 1969` unpatched), so ODT text keeps the original size
  and overflows the shrunk boxes — while cairo/PDF reads the font at draw time
  (`gramps/plugins/lib/libcairodoc.py`) and scales correctly.

The fix decides the drawn text style **at draw time** (like cairo) instead of
baking it at `init()` time: `_scaled_text_style(para_name)` recomputes the
text-properties from the *current* (post-scale) font; if unchanged it reuses the
named `F<name>` (unscaled output stays byte-identical), otherwise it registers an
automatic override carrying the scaled size, flushed via `cntnt2` in
`add_scaled_text_styles()` — the same late-flush mechanism the styled-note styles
already use (`odfdoc.py:774-790, 825-842`). One shared `_draw_text_properties`
helper formats the font for both `init()` and the draw path, so there is no drift
(this is what keeps unscaled output byte-identical and lets the reuse check work).

## The two defects the iteration-1 carry-forward required fixing

Both were real regressions introduced by the iteration-1 patch (confirmed by the
adversary), and both are now fixed **and** covered by a dedicated test.

### 1. `KeyError('')` in `draw_box` for a draw style with no paragraph style

`GraphicsStyle.para_name` defaults to `""` (`graphicstyle.py`), and
`StyleSheet.get_paragraph_style` indexes the dict directly
(`gramps/gen/plug/docgen/stylesheet.py:369` → `self.para_styles[name]`), raising
`KeyError('')`. The unpatched `draw_box` never resolved the paragraph style at
all (it only used `para_name` as a string), so the empty name was tolerated;
iteration-1's `_scaled_text_style` resolved it eagerly and crashed. No shipped
report hits this (all non-empty-text `draw_box` calls set a paragraph style), but
the public `DrawDoc` API is addon-reachable.

Fix (`odfdoc.py` `_scaled_text_style`, the new `if para_name not in
self._draw_text_props:` guard): when `init()` wrote no `F<name>` style for this
paragraph style, return `"F%s" % para_name` verbatim — the exact pre-#5733
behaviour — without touching the style sheet. Because `init()` records every
paragraph style name it writes (`self._draw_text_props` / `_draw_text_style_names`),
"absent from `_draw_text_props`" is precisely "no such paragraph style", so the
guard is exact, not heuristic. Covered by
`test_draw_box_without_paragraph_style_does_not_crash` (asserts no crash and the
span still references `"F"`, i.e. behaviour is byte-preserved).

### 2. `FScaledN` override-name collision with a user style named `Scaled1`

`init()` writes an `F<name>` style for **every** paragraph style, so a user style
sheet with a paragraph style literally named `Scaled1` produces an init style
`FScaled1`. Iteration-1 minted overrides as `"FScaled%d"` unconditionally, so the
first override was also `FScaled1` → two `<style:style style:name="FScaled1">`
definitions with different sizes → invalid ODF.

A fixed prefix alone cannot be safe (any prefix `P` collides with a user paragraph
style named `P + n`), so the fix generates names against the actual reserved set:
`init()` accumulates every `F<name>` it writes in `self._draw_text_style_names`,
and `_new_scaled_style_name()` skips any `FScaledN` already in that set (and adds
each name it hands out, so overrides never collide with each other either).
Covered by `test_scaled_override_name_does_not_collide` (asserts the override is
not `FScaled1` and that **no** style name is defined twice in the emitted XML).

### 3. Tautological "cairo parity" assertion in the test

Iteration-1's test computed `cairo_effective` by re-reading the same style sheet
it had just mutated and asserted `cairo_effective == expected` — no cairo code
ran, so it could never fail independently (the adversary's point, `check-advisory
:44-51`). Removed. The genuine parity fact is that the cairo backend renders
`font.get_size()` at draw time, i.e. `BASE_SIZE * SCALE`; the test now asserts the
**emitted ODF** size equals `BASE_SIZE * SCALE` directly — that single assertion
*is* the parity check, and it is on the production ODF path. I did not import the
cairo backend to "really" run parity because `libcairodoc` pulls in `gi`
(cairo/pango) and would crash the headless C4 runner; the pure-arithmetic parity
target (`BASE_SIZE * SCALE`) is exact and needs no GUI.

## Test drives production, and is import-light

`gramps/plugins/test/odfdoc_drawscale_test.py`:

- builds a minimal style sheet (one paragraph style + one draw box style — the
  exact shape a tree report uses), `ODFDoc.open()/init()`;
- applies the scale the way a graphical report does — `get_style_sheet()` →
  `font.set_size(size*amount)` → `set_style_sheet()`, the report→doc contract
  (`descendtree.scale_styles`, `:1504-1529`) — this is *input*, not a
  reimplementation of the backend's size emission;
- calls the **real** `draw_box` / `center_text` (which route through the
  production `_scaled_text_style` + `add_scaled_text_styles`) and parses the
  emitted content.xml.

It imports only `gramps.gen` / `gramps.plugins.docgen.odfdoc` (no `gi`,
no `gramps.gui`), so it runs under the headless C4 runner.

## Alternatives considered, with cost

- **Move `begin_report` work into `init()`** so the sheet is scaled before styles
  are written: explicitly **out of scope** — the brief records this was committed
  and reverted twice upstream as "worse than the original" (a design-discussion
  item, per paulfranklin). Not pursued.
- **Relocate the whole paragraph/text/draw style-writing block out of `init()`**
  into `finish_cntnt_creation()` so it serialises the scaled sheet: that block is
  `odfdoc.py:513-747` (~230 lines) and is written into `cntnt` interleaved with
  the `<office:automatic-styles>` open (`cntnt2`) / close (`cntnt`) and the body
  content `draw_*` appends. Relocating means splitting automatic-styles emission
  into its own buffer and re-sequencing the whole `cntnt1`/`cntnt2`/`cntnt`
  assembly (`finish_cntnt_creation`, `:774-790`) that the styled-note, photo,
  table and cell paths depend on — and it changes the serialised bytes for
  *every* ODT report, not just scaled graphical ones. Concrete cost of my chosen
  fix instead: `odfdoc.py` −27/+13 in the `init()` F-block, +3 one-line span
  swaps, +2 `text_style = …` lines, +1 call in `finish_cntnt_creation`, and 4
  small new methods (~90 lines) — and unscaled output stays byte-for-byte
  identical (`test_unscaled_output_unchanged`).

## Verification (red → green)

The Docker-based engine runner (`run-verify.sh`) is **blocked by this session's
sandbox** (every Docker invocation is denied — same limitation the iteration-1
notes recorded). The deterministic C4 gate will run it on repaired infra. As a
sanity check I ran the exact red→green contract by hand against the gramps61
worktree, headless (`python3 -m unittest`, no display), which is what the C4
runner does for a core fix:

- **fix applied →** all 5 tests **pass**;
- **production reverted, test kept →** **3 failures** — the core defect
  (`test_scaled_box_text_font_is_scaled`: emitted `16.00pt` vs expected `8.00pt`),
  `test_center_text_font_is_scaled`, and the scaled branch of
  `test_scaled_override_name_does_not_collide`.

The two regression-guard tests (`…without_paragraph_style…`,
name-collision structural part) pass **both** pre- and post-fix by design — they
guard against defects *this patch* could introduce, not the original bug. After
the check the worktree was restored to pristine (`git status --short` clean).

## Commit-readiness / formatting

`black` is not installed in this session (no `pip`, offline), so I could not run
it. I hand-checked: no line I added exceeds 88 columns (verified with `awk
'length>88'` — the only >88 line in the file is a pre-existing URL comment at
`odfdoc.py:2110`), and the new code mirrors the existing black-formatted wrapping
(adjacent-string concatenation, trailing-comma calls). Both changed Python files
pass `python3 -m py_compile`. A `black` pass at publish is still advisable since
no PDCA gate models it.

## Files

- `gramps/plugins/docgen/odfdoc.py` — the fix (init F-block refactor + 4 methods +
  3 span swaps + finish_cntnt_creation call + `__init__` state).
- `gramps/plugins/test/odfdoc_drawscale_test.py` — new regression test.
- `po/POTFILES.skip` — register the new test (no translatable strings), inserted
  alphabetically between `imports_test.py` and `reports_test.py`.
