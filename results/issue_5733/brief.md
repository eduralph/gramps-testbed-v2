# Brief — issue 5733 / odf-drawchart-text-not-scaled

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** odf-drawchart-text-not-scaled
- **Defect:** A graphical descendant-chart report generated to ODT with a "scale tree to
  fit" size option shrinks the boxes but NOT the text inside them, so text overflows the
  scaled boxes. The same report to PDF scales text correctly. Reported by paulfranklin
  (3.4.x), reproduced through 4.1.3 (sam888). NOTE: a 2012 fix that moved the graphical
  reports' `begin_report` work into `init` was committed then **reverted twice** as
  "worse than the original" — that restructuring approach is out of scope here.
- **Success criterion:** After the fix, a graphical descendant chart written to ODT with a
  scale-to-fit option renders box text at the same scaled-down font size the cairo/PDF
  output uses (text fits its box). Demonstrable by a C4 test that drives the ODF draw
  backend for a scaled graphical report and asserts the emitted draw-text/paragraph font
  size reflects the applied scale factor (red pre-fix — unscaled style size; green
  post-fix).
- **Invariant to restore:** A document backend must render text at the effective font
  size the report computed for it, including any scale factor the report applied — output
  format must not change the rendered text size. (Gramps docgen fidelity rule; no external
  canon — the ODF draw backend renders box text from fixed named paragraph styles and so
  ignores the per-report scale factor that the cairo backend honours at draw time.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** high
- **Scope:** The ODF drawing backend emits box/text font sizes from the pre-written named
  paragraph styles, so a graphical report's scale-to-fit factor (which the cairo backend
  applies to the rendered text) is not reflected in ODT output. Make the ODF draw output
  reflect the scaled font size, achieving parity with the PDF/cairo output. / out of
  scope: the reverted approach of moving `begin_report` code into `init` / restructuring
  the report generation flow (paulfranklin: such rework belongs in a design discussion,
  not this fix); the ancestor chart (untested by the reporter — verify but do not expand
  scope to it blindly); non-graphical (text) reports.
- **Repro instruction:** On `maintenance/gramps61`, generate a graphical Descendant Chart
  (≥3 generations) to ODT, letter/portrait, with a "scale tree to fit" Size option; open
  in LibreOffice: boxes shrink but the text does not, overflowing the boxes. Compare to
  the PDF output, which is correct.
- **Test file:** `gramps/plugins/test/odfdoc_drawscale_test.py` (core `test/` package,
  `*_test.py` suffix). The test MUST drive the production ODF draw path
  (`ODFDoc.draw_box`/`draw_text`/`center_text` under an applied scale) and assert the
  emitted font size is scaled — not a reimplementation of the scaling (principles §3.4).
  Verify parity against the cairo path's effective size where feasible.
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause region: `gramps/plugins/docgen/odfdoc.py:1861-1985` `draw_text`/`draw_box`/
  `center_text` using `pstyle.get_font()` / `font.get_size()` from named paragraph styles
  written by `_write_styles_file` at `odfdoc.py:1221-1290`, so the report's scale factor
  is not applied).
- **New/removed files:** adds `gramps/plugins/test/odfdoc_drawscale_test.py` (a test, no
  translatable strings) → register in `po/POTFILES.skip`. No other `.py` added/removed.
- **Prior-art check (triage cycles):** searched `gramps/plugins/docgen/odfdoc.py` on
  `upstream/maintenance/gramps61` — styled-note/https/black/license churn but no
  draw-text scaling fix; the 2012 begin_report→init attempt was reverted (not present).
  No open/closed PR found for a current fix. Not already upstream.
- **Mantis:** 5733
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Two concrete defects introduced by the patch must be fixed before accept: 1. KeyError crash in draw_box: when GraphicsStyle.para_name is "" (the default), _scaled_text_style does a direct dict lookup that raises KeyError(''). Add a .get()-style fallback to the old non-scaled behaviour when the paragraph style is absent. 2. FScaledN name collision: override style names "FScaled%d" collide with a user stylesheet containing a paragraph style literally named "Scaled1", producing duplicate ODF style definitions (invalid ODF). Use a collision-proof prefix or check for existing names before writing. Also fix the cairo-parity test assertion (reads from the same mutated stylesheet — can never fail independently; assert on the emitted ODF value instead).
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
