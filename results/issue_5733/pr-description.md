## Summary

**User impact:** Graphical tree reports (descendant/ancestor chart) generated to ODT with a "scale tree to fit" size option now render box text at the correct scaled font size, matching PDF output. Previously, text boxes would shrink but the text inside would stay at the original size, causing overflow.

**The fix:** The ODF drawing backend now resolves text-style font sizes at draw time (after any report scaling) instead of locking them in at initialization.

## What to look at

The fix touches the ODF backend's text-style handling in two places:

1. **Core logic** (`gramps/plugins/docgen/odfdoc.py`):
   - `_scaled_text_style()` — decides which style name a drawn text span should reference by comparing the current font to what was written at init time
   - `_draw_text_properties()` — formats font properties (shared by init and draw paths to ensure consistency)
   - `_new_scaled_style_name()` — allocates collision-safe override-style names
   - `add_scaled_text_styles()` — flushes registered overrides into the ODF document
   - Callers in `draw_text()`, `draw_box()`, `center_text()` — now invoke `_scaled_text_style()` at draw time

2. **Regression test** (`gramps/plugins/test/odfdoc_drawscale_test.py`):
   - Drives the production ODF draw path under an applied scale factor (matching how graphical reports scale)
   - Asserts the emitted font size reflects the scale

To reproduce the original defect: generate a graphical Descendant Chart (≥3 generations) to ODT, portrait, with "scale tree to fit" enabled. Open in LibreOffice and observe text overflow; the same report to PDF scales correctly.

## Root cause

When a graphical tree report runs:

1. `doc.init()` writes fixed named text styles ("F<name>") from the unscaled style sheet
2. `begin_report()` then scales the style sheet's fonts (via `scale_styles()`)
3. Draw methods (`draw_box`, `center_text`) emit the box text with references to the stale named styles

The PDF/cairo backend reads the font at draw time, so it sees the scaled values. The ODF backend, writing the style once at init, saw only the unscaled sizes — text stayed at 16pt while boxes shrank to 8pt.

## The fix

Text-style resolution moved from init time to draw time:

1. **At init time** (`_draw_text_properties()` + `_draw_text_props` dict): Record what font properties each "F<name>" style was written with.
2. **At draw time** (`_scaled_text_style()`): Fetch the current paragraph font and compare it to what "F<name>" holds. If unchanged, reuse "F<name>" (so unscaled output stays byte-identical). If changed (report scaled it), register an automatic override style with the current size and reference that instead.
3. **At finish time** (`add_scaled_text_styles()` + `cntnt2`): Serialize the override styles into the ODF document's `<office:automatic-styles>` block.

The same `_draw_text_properties()` helper formats the font for both paths, ensuring no drift. Override names are collision-proof: `_new_scaled_style_name()` skips any `FScaled<n>` that would collide with a user paragraph style.

## Verified against

**Claim:** Drawn box text in a scaled ODT report emits a font size reflecting the report's scale factor, achieving parity with the PDF/cairo backend.

**Evidence:**

- **Core test** (`gramps/plugins/test/odfdoc_drawscale_test.py:375-399`, `test_scaled_box_text_font_is_scaled`):
  - Scales a 16pt font by 0.5× (matching `DescendTree.scale_styles`)
  - Calls `draw_box()` with the scaled style sheet
  - Parses the emitted ODF content and extracts the actual `fo:font-size` value
  - Asserts `emitted == 16pt × 0.5 = 8pt` (green with fix; red without)
  
- **Scaled center-text path** (`gramps/plugins/test/odfdoc_drawscale_test.py:401-413`, `test_center_text_font_is_scaled`):
  - Title text (`center_text()`) also scales to 8pt

- **Regression guards** to prevent defects from a prior fix attempt:
  - `test_draw_box_without_paragraph_style_does_not_crash()` (`gramps/plugins/test/odfdoc_drawscale_test.py:428-441`): Empty paragraph-style names fall back to pre-#5733 behavior without a `KeyError`
  - `test_scaled_override_name_does_not_collide()` (`gramps/plugins/test/odfdoc_drawscale_test.py:443-466`): Override names do not collide with user styles (e.g., a user style literally named "Scaled1")
  
- **Unscaled output unchanged** (`gramps/plugins/test/odfdoc_drawscale_test.py:415-426`, `test_unscaled_output_unchanged`): Without a scale, drawn spans reference the named "F<name>" style unchanged, preserving byte-parity for unscaled reports.

## Test

`gramps/plugins/test/odfdoc_drawscale_test.py` (new) — drives the production ODF draw path under an applied scale factor (matching how graphical reports scale) and asserts the emitted `fo:font-size` reflects the scale (16pt × 0.5 = 8pt for both box and centre text), plus regression guards for the no-paragraph-style fallback, override-name collisions, and byte-parity of unscaled output. Red with the production change reverted, green with the fix.

---

Fixes [#5733](https://gramps-project.org/bugs/view.php?id=5733)
