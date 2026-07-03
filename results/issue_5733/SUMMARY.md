# Result — issue 5733 / odf-drawchart-text-not-scaled

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: A graphical descendant-chart report generated to ODT with a "scale tree to
- Success criterion: After the fix, a graphical descendant chart written to ODT with a
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: The ODF drawing backend emits box/text font sizes from the pre-written named

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Review task: fix Gramps bug 5733 so ODT graphical descendant-chart draw text uses the same scaled font size as the scale-to-fit report/PDF path.

Target caveat: `$PDCA_TARGET` is readable but stale for this review (`/home/eddie/gramps/gramps` is on `master`, lacks the patch, and rejects only the `po/POTFILES.skip` context); affected source citations below are therefore grounded on `patch.diff` as instructed.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief gives a concrete defect, success criterion, invariant, surfaces, and out-of-scope constraints for ODT draw-text scaling parity (`brief.md:6`, `brief.md:12`, `brief.md:18`, `brief.md:26`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added test asserts scaled ODF font size and documents the old failure as emitted `BASE_SIZE` instead of `BASE_SIZE * SCALE` (`patch.diff:375`, `patch.diff:390`); the C4 gate records `red-without-fix=PASS` (`check-gates.json:33`). |
| C3 — C3 Change | PASS | The patch records initial `F<name>` text properties, compares them to current post-scale font properties, writes non-colliding override styles, and switches draw spans to those styles (`patch.diff:25`, `patch.diff:117`, `patch.diff:167`, `patch.diff:193`). |
| C4 — C4 Verification (red→green) | PASS | Gate evidence says green-with-fix and red-without-fix both passed (`check-gates.json:33`); I also applied the code/test hunks in a local shared clone and ran `GRAMPS_RESOURCES=... python3 -m unittest gramps.plugins.test.odfdoc_drawscale_test`, which ran 5 tests OK. |
| C5 — C5 Causal adequacy | PASS | The causal path matches the defect: fixed styles are written before report scaling, then draw-time spans now use a style derived from the current font size (`patch.diff:9`, `patch.diff:123`, `patch.diff:140`, `patch.diff:210`). |
| T1 — T1 Structure | N/A | This is a core-code/test change, not an addon layout change; the patch touches `gramps/plugins/docgen/odfdoc.py`, adds `gramps/plugins/test/odfdoc_drawscale_test.py`, and updates `po/POTFILES.skip` only (`patch.diff:1`, `patch.diff:231`, `patch.diff:471`). |
| T2 — T2 Shape | PASS | The new test has the existing GPL header shape and the new core Python file is registered in `POTFILES.skip` (`patch.diff:237`, `patch.diff:471`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: the configured whole-suite runtime gate exited before producing JUnit XML (`check-gates.json:78`), while the focused regression test passes; human must decide whether this non-gating environment/bootstrap gap is acceptable for sign-off. |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in the bundle, so contribution-wrapper review does not apply (`check-gates.json:87`). |
| T5 — T5 Judgment | PASS | The solution stays in the ODF backend rather than the explicitly out-of-scope `begin_report` restructuring and covers the prior-attempt KeyError and style-name collision regressions (`brief.md:9`, `brief.md:62`, `patch.diff:133`, `patch.diff:443`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: artifact and focused test evidence show emitted scaled font sizes, but a human must decide whether that satisfies the user-visible LibreOffice fitness criterion for scaled graphical descendant charts (`brief.md:34`). |

## §6 Human Decisions

1. T3 Runtime: decide whether to clear sign-off despite the whole-suite runner bootstrap failure, given the focused patched-clone test passed and the recorded C4 red-to-green gate passed.
2. Validation fitness-to-purpose: decide whether the emitted ODF font-size parity demonstrated by the test is sufficient, or whether a manual LibreOffice descendant-chart inspection is required before acceptance.

### Advisory — adversary

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 — T3 Runtime — DECISION OWED: the configured whole-suite runtime gate exited before producing JUnit XML (`check-gates.json:78`), while the focused regression test passes; human must decide whether this non-gating environment/bootstrap gap is acceptable for sign-off.
- [x] V — Validation — fitness-to-purpose — DECISION OWED: artifact and focused test evidence show emitted scaled font sizes, but a human must decide whether that satisfies the user-visible LibreOffice fitness criterion for scaled graphical descendant charts (`brief.md:34`).
- [x] **Invariant only partially restored: `rotate_text` still emits the unscaled

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
