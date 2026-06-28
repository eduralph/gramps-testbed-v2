# Check Review

Target caveat: `$PDCA_TARGET` was readable, but it was on `maintenance/gramps61` while the brief targets `maintenance/gramps60` (brief.md:21). I used the target tree where it confirmed existing behavior, and used `patch.diff` for proposed/new lines.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The success criterion is concrete: hyphenated given names or surnames must render with the hyphen intact in the DWR SVG tree, matching indexes/tabs (brief.md:14). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The target splitter treats hyphen as a separator and `calcTextTab()` rejoins fragments with spaces, reproducing the named defect path (`DynamicWeb/templates/dwr_default/data/dwr_svg.js:2939`, `DynamicWeb/templates/dwr_default/data/dwr_svg.js:2862`). |
| C3 — C3 Change | PASS | The patch changes only the tree text splitter from space-or-hyphen to spaces-only, directly on the scoped DWR SVG renderer path (patch.diff:10). |
| C4 — C4 Verification (red→green) | PASS | The verification gate reports green-with-fix and red-without-fix both passing as expected for the regression test (check-gates.json:33). |
| C5 — C5 Causal adequacy | PASS | The causal chain is sufficient: target code splits `txt` on hyphen, then same-line layout rejoins with `' '`, so preserving hyphens at the splitter prevents the rewrite (`DynamicWeb/templates/dwr_default/data/dwr_svg.js:2939`, `DynamicWeb/templates/dwr_default/data/dwr_svg.js:2862`). |
| T1 — T1 Structure | FAIL | The structure gate reports a DynamicWeb tests-package structure failure; this is non-gating in `check-gates.json` but remains an unresolved conformance result (check-gates.json:51). |
| T2 — T2 Shape | PASS | The added Python test carries the GPL header and standard `unittest` shape; the shape gate records pass/no checkable production Python issue (patch.diff:27, check-gates.json:60). |
| T3 — T3 Runtime | FAIL | Runtime addon matrix gates report new baseline deltas on unrelated addons for both gramps60/core 6.0 and gramps61/core 6.1, so the runtime row is not clean (check-gates.json:68, check-gates.json:77). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this review bundle, so contribution-wrapper checks do not apply (check-gates.json:86). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: accept whether changing hyphenated tree labels to wrap only on spaces is the intended scope tradeoff, since it preserves data fidelity but can change SVG line wrapping for hyphenated names (patch.diff:10). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must confirm a generated DWR report in-browser shows names like `Jan-Åke` and `HAMILTON-SMITH` with hyphens intact in the SVG tree, because the test verifies the JS splitter path but does not render Raphael/SVG DOM (brief.md:31). |

## §6 Human Clearances

- T5: Decide whether the scope accepts the line-wrapping behavior change caused by no longer treating hyphen as a tree-label word break. This matters because it is the direct fix for data fidelity, but it can affect visual wrapping for long hyphenated names.
- V: Perform or accept manual browser validation of a generated Dynamic Web Report tree containing hyphenated given and surname values. This matters because the automated test proves the red/green splitter behavior, not the full SVG rendering surface.
