# check-advisory-adversary.md — issue 5733 (odf-drawchart-text-not-scaled)

Adversarial pass. I attempted to refute the evidence, the fix, and the verdict.
All citations are on the brief's target branch `upstream/maintenance/gramps61`
(note: the `$PDCA_TARGET` working checkout is on `master`, where the patch does
**not** apply — POTFILES.skip context differs; it applies cleanly to gramps61).

## Refutations that landed

- NEEDS-HUMAN — **No machine-verified red→green exists at review time.**
  `check-gates.json` C4 (gating) = **fail** ("core worktree /home/eddie/gramps/gramps-6.1-lane1
  missing") and T3 = **fail** (runner exited 1, no JUnit XML — pre-test crash). Both are
  infra failures, but it means any reviewer claim that the fix is "verified red→green" is
  unwarranted from the gates alone. I re-ran the proof independently on a scratch export of
  `upstream/maintenance/gramps61`: **red** pre-fix (2 failures, emitted 16.00pt vs expected
  8.00pt — the exact defect) and **green** post-fix (3/3 pass). My run is advisory only;
  the deterministic C4/T3 gates must be re-run on repaired infra before sign-off.

- NEEDS-HUMAN — **New crash path: `draw_box` with non-empty text and a draw style whose
  paragraph-style name is unset/missing now raises `KeyError`.** The patched
  `draw_box` calls `_scaled_text_style(para_name)` (gramps/plugins/docgen/odfdoc.py:1997
  patched), which does `get_style_sheet().get_paragraph_style(para_name)`;
  `StyleSheet.get_paragraph_style` indexes the dict directly
  (gramps/gen/plug/docgen/stylesheet.py:369) and `GraphicsStyle` defaults to
  `para_name = ""` (gramps/gen/plug/docgen/graphicstyle.py:103). Empirically confirmed on
  the patched tree: `doc.draw_box("NoParaBox", "hello", …)` → `KeyError('')`, where
  pre-patch the same call emitted (sloppy but non-fatal) output. Pre-patch `draw_box`
  never resolved the paragraph style at all. No **shipped** report hits this (all
  non-empty-text `draw_box` call sites set a paragraph style; the empty-text calls, e.g.
  statisticschart.py:1087, calendarreport.py:259, skip the new lookup via `if text:`),
  but third-party/addon reports calling the public DrawDoc API can. A `.get()`-style
  fallback to the old dangling-"F" behaviour would remove the regression.

- **`FScaledN` override names can collide with a user-named style.** Override names are
  generated as `"FScaled%d"` (odfdoc.py:1854 patched, `_scaled_text_style`), while `init()`
  writes a `"F%s"` text style for every paragraph style name (odfdoc.py:652 unpatched).
  A style sheet containing a paragraph style literally named `Scaled1` therefore yields
  **two** `<style:style style:name="FScaled1">` definitions with different sizes —
  empirically confirmed on the patched tree (2 definitions, 8.00pt and 20.00pt), which is
  invalid ODF and renders ambiguously. Only reachable via a custom user style sheet with
  that exact name (report-defined names are `CG2-*` etc.), so low likelihood — but a
  collision-proof prefix (or checking existing names) would close it.

- **The "cairo parity" assertion in the test is a tautology, not a parity check.**
  `odfdoc_drawscale_test.py:150-155` computes `cairo_effective` by reading the same style
  sheet the test itself just mutated — no cairo code executes, so
  `assertAlmostEqual(cairo_effective, expected)` can never fail independently. The brief
  allowed "where feasible", and the core assertion (emitted ODF size == scaled size) is
  genuine and on the production path, but the reviewer should not credit the test with
  *verified* cairo parity — parity rests on the (documented, plausible) claim that the
  cairo backend reads the font at draw time, which this test does not exercise.

## Refutation attempts that failed (fix survived)

- **Attempted to show the test's scale simulation diverges from production.** It does not:
  `descendtree.py:1474-1529` (`scale_styles`) performs exactly the mutation the test's
  `_apply_report_scale` performs (get sheet → scale para font → `add_paragraph_style` →
  `doc.set_style_sheet`), and `cli/plug/__init__.py:781-783` / :900-911 confirm
  `doc.init()` runs **before** `begin_report()` (the bug's precondition). The test drives
  the real `ODFDoc.draw_box`/`center_text`, not a copy — C5's pass is warranted.
- **Attempted to break the fix end-to-end.** Ran the real Descendant Chart →
  ODT (`name=descend_chart, scale_tree=2`) on the example database against the patched
  tree: box-text spans reference `FScaled1/FScaled2` at **2.79pt** while the stale named
  styles keep 9/16pt; content.xml is well-formed XML. The unscaled run (`scale_tree=0`)
  emits **zero** `FScaled` styles and spans reference the original `FCG2-*` names — the
  common case is byte-compatible, as the third test asserts.
- **Attempted to break the byte-identity reuse claim** (`_draw_text_properties` vs the
  inline `init()` formatting, including the trailing-space/`"/> "` seam and the `%.2fpt`
  rounding): the strings are identical; a scale factor that rounds to the same 2-decimal
  size correctly reuses the named style.
- **Attempted misordered-styles corruption:** `add_scaled_text_styles` writes to `cntnt2`,
  which lands inside `<office:automatic-styles>` before the `init()`-written styles in
  `cntnt` and before `</office:automatic-styles>` (odfdoc.py:749-756, 774-790 unpatched
  numbering) — same mechanism as `add_styled_notes_styles`; ordering is valid.

## Bottom line

The fix is real and I could not break it on any shipped-report path; the two concrete
weaknesses found (addon-reachable `KeyError('')` in `draw_box`, `FScaledN` name collision)
are edge-case robustness regressions a human should adjudicate, and the deterministic
C4/T3 gates still need a clean re-run — the current gate file proves nothing.
