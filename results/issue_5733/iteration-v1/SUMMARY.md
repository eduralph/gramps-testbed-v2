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
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix Gramps issue 5733 so ODF graphical descendant-chart output scales draw-text font sizes when "scale tree to fit" scales the boxes.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the defect, success criterion, invariant, and scope for ODT draw-text scaling parity with PDF/cairo at brief.md:5, brief.md:12, brief.md:18, and brief.md:26. |
| C2 — C2 Reproduction (red pre-fix) | PASS | I restored the production file to pre-fix in a temp clone and the added test failed red with 16.00pt emitted vs 8.00pt expected; the failing assertions are the scaled box and center-text checks at patch.diff:338 and patch.diff:372. |
| C3 — C3 Change | PASS | The patch records init-time F-style text properties, computes current draw-time properties, serializes scaled overrides, and switches draw_text/draw_box/center_text spans to that style at patch.diff:23, patch.diff:78, patch.diff:140, patch.diff:162, patch.diff:182, and patch.diff:194. |
| C4 — C4 Verification (red→green) | PASS | Focused verification in a patched temp clone passed green (`python3 -m unittest gramps.plugins.test.odfdoc_drawscale_test`: 3 tests OK) after the same test failed red pre-fix; the configured C4 gate failure is an unavailable worktree caveat at check-gates.json:33, not a patch defect. |
| C5 — C5 Causal adequacy | PASS | The target old code writes fixed F styles from init-time font sizes and draw spans reference those fixed names at /home/eddie/gramps/gramps/gramps/plugins/docgen/odfdoc.py:651 and /home/eddie/gramps/gramps/gramps/plugins/docgen/odfdoc.py:1884, while the patch reads current font props and overrides only when changed at patch.diff:113. |
| T1 — T1 Structure | N/A | Core-only patch with no addon layout surface; the conformance gate also reports addon structure N/A at check-gates.json:51. |
| T2 — T2 Shape | PASS | The new test has the project GPL header at patch.diff:210 and is registered in POTFILES.skip at patch.diff:402; check-gates reports both shape and potfiles pass at check-gates.json:60 and check-gates.json:69. |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: the whole-suite runtime gate crashed before producing JUnit at check-gates.json:78, so a human must decide whether the focused red/green test is sufficient or rerun the full core suite in a working Gramps test lane before merge. |
| T4 — T4 Contribution | N/A | No commit-msg.txt or pr-description.md is present in the artifact bundle, matching the T4 N/A gate result at check-gates.json:87. |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: because /home/eddie/gramps/gramps is on stale/different `master` and the patch targets maintenance/gramps61, a human must accept the target-state caveat and the backend-wide ODF draw-text override scope before sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: XML-level red/green is verified, but a human must confirm LibreOffice-rendered ODT output visually meets the user-facing "text fits scaled boxes like PDF" criterion from brief.md:12. |

§6 Human Clearances

1. T3 Runtime: decide whether to waive the whole-suite runner crash or rerun the Gramps core suite in a valid lane; the focused test was verified red-to-green, but the full runtime gate did not execute tests.
2. T5 Judgment: decide whether the stale `master` target caveat is acceptable for this artifact review and whether applying the fix at the ODF draw backend level is the intended scope for maintenance/gramps61.
3. V Validation: perform the manual fitness check from brief.md:34: generate a graphical Descendant Chart to ODT on letter/portrait with "scale tree to fit", open it in LibreOffice, and compare to PDF; clear only if the ODT box text visibly scales down and fits the scaled boxes.

### Advisory — adversary

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] T3 — T3 Runtime — DECISION OWED: the whole-suite runtime gate crashed before producing JUnit at check-gates.json:78, so a human must decide whether the focused red/green test is sufficient or rerun the full core suite in a working Gramps test lane before merge.
- [ ] T5 — T5 Judgment — DECISION OWED: because /home/eddie/gramps/gramps is on stale/different `master` and the patch targets maintenance/gramps61, a human must accept the target-state caveat and the backend-wide ODF draw-text override scope before sign-off.
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: XML-level red/green is verified, but a human must confirm LibreOffice-rendered ODT output visually meets the user-facing "text fits scaled boxes like PDF" criterion from brief.md:12.
- [ ] **No machine-verified red→green exists at review time.**
- [ ] **New crash path: `draw_box` with non-empty text and a draw style whose

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): Two concrete defects introduced by the patch must be fixed before accept: 1. KeyError crash in draw_box: when GraphicsStyle.para_name is "" (the default), _scaled_text_style does a direct dict lookup that raises KeyError(''). Add a .get()-style fallback to the old non-scaled behaviour when the paragraph style is absent. 2. FScaledN name collision: override style names "FScaled%d" collide with a user stylesheet containing a paragraph style literally named "Scaled1", producing duplicate ODF style definitions (invalid ODF). Use a collision-proof prefix or check for existing names before writing. Also fix the cairo-parity test assertion (reads from the same mutated stylesheet — can never fail independently; assert on the emitted ODF value instead).
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
