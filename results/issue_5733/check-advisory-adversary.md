# Adversarial review — issue 5733 / odf-drawchart-text-not-scaled

Advisory only; I never gate. I re-ran the red→green at `$PDCA_TARGET`
(`/home/eddie/gramps/gramps`), attacked the fix with concrete inputs, and probed the
reviewer's verdict. Findings below; grounded on the target source with the patch applied.

## Refutation attempts that FAILED (fix held up)

- **Red→green is real and on the production path.** Applied `patch.diff`, ran
  `gramps.plugins.test.odfdoc_drawscale_test`: with the fix all 5 pass; reverting only
  `odfdoc.py` flips `test_scaled_box_text_font_is_scaled`, `test_center_text_font_is_scaled`
  and `test_scaled_override_name_does_not_collide` to FAIL. The test drives real
  `ODFDoc.draw_box` / `center_text` (`odfdoc.py:1988,2034`), not a re-implementation.
- **The scaling premise is faithful to production.** `_apply_report_scale` mirrors the real
  `DescendTree.scale_styles` (`descendtree.py:1474-1529`: get sheet → `font.set_size(*amount)`
  → set sheet), and the timing it relies on is genuine: `cli/plug/__init__.py:781-782` and
  `_reportdialog.py:757-758` call `doc.init()` *before* `begin_report()`, and
  `descendtree.py:1417` calls `scale_styles` inside `begin_report` — so `init()`'s
  `F<name>` styles are indeed written unscaled, then the sheet is scaled, then draws happen.
- **Override placement is valid ODF.** `add_scaled_text_styles` writes to `cntnt2`
  (`odfdoc.py:1942`), which opens `<office:automatic-styles>` (`odfdoc.py:516-520`) and is
  flushed before `cntnt` (`odfdoc.py:773-775`); the overrides land inside automatic-styles,
  same proven mechanism as `add_styled_notes_styles`.
- **Edge cases the prior iteration broke are now covered.** Empty paragraph-style name
  falls back to `"F"` without a KeyError (`odfdoc.py:1904-1906`, tested); the `FScaled%d`
  allocator skips names reserved by `init()` and prior overrides (`odfdoc.py:1918-1929`,
  no-dup test passes).

I could not refute the fix for the descendant-chart path the brief targets.

## Findings a human should weigh

- NEEDS-HUMAN — **Invariant only partially restored: `rotate_text` still emits the unscaled
  named style.** `odfdoc.py:1790` still does `'<text:span text:style-name="F%s">' % pname`
  — the patch fixed `draw_text`/`draw_box`/`center_text` but left the sibling `rotate_text`
  untouched. The fan-chart report re-sizes the paragraph font *after* `init()`
  (`fanchart.py:610`, `fanchart.py:641`: `font.set_size(...)`) and draws through
  `self.doc.rotate_text` (`fanchart.py:694,703,756,765`), so ODF fan-chart text still
  exhibits exactly bug #5733. This is out of the brief's stated scope (descendant chart /
  ancestor-verify) and `rotate_text` is pre-existing code the diff didn't touch, so it is
  **not** a defect *introduced* by the patch — but it makes any verdict phrased as "the ODF
  draw backend now honours the report's scale factor" (brief Invariant, §"output format must
  not change the rendered text size") **overbroad**. A human should confirm that leaving the
  rotated-text path unscaled is an acceptable, deliberate scope boundary.

- **The "cairo/PDF parity" the test advertises is asserted, not executed.**
  `odfdoc_drawscale_test.py` computes `expected = BASE_SIZE * SCALE` and labels it "what
  cairo/PDF renders", but never instantiates the cairo backend. I checked the production
  cairo path and it *does* match (`libcairodoc.py:1747-1751` reads the post-scale paragraph
  style at draw time; `libcairodoc.py:174` sets the Pango size from `font.get_size()`), so
  the constant equals the real PDF size today — the assertion is meaningful and non-tautological
  (pre-fix ODF emits 16pt vs expected 8pt). The caveat is only that the test would not catch a
  future *cairo-side* divergence (e.g. a minimum-font clamp or different rounding), since parity
  is verified by construction/my analysis rather than by exercising both backends. Low severity;
  the brief itself only asked for cairo parity "where feasible".

- **Sub-point rounding divergence is real but negligible.** ODF emits `fo:font-size="%.2fpt"`
  (`odfdoc.py:1877-1878` via `_draw_text_properties`) while cairo rounds to Pango units
  (`libcairodoc.py:174`). For non-round scale factors (e.g. 0.37) the ODT and PDF sizes can
  differ in the third decimal. Not a functional defect; noted for completeness.
