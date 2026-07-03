Review task: fix issue 8622 so filtering the "Select Source or Citation" dialog keeps existing citation children reachable under any shown source instead of forcing creation of a new citation.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect, success criterion, restored invariant, and selector-only scope: filtered selector sources must keep citation children selectable while standalone tree-view search should not regress (`brief.md:6`, `brief.md:12`, `brief.md:18`, `brief.md:27`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | I applied only the new test to an otherwise unpatched temp copy and it failed behaviourally, not by missing API: title search produced `[] != ['CIT_B1', 'CIT_B2']`, matching the test's intended fallback path (`patch.diff:385`, `patch.diff:401`). |
| C3 — C3 Change | PASS | Patch introduces a selector-specific model and wires only `SelectCitation` to it, preserving the plain `CitationTreeModel` for standalone views (`patch.diff:9`, `patch.diff:17`, `patch.diff:133`, `patch.diff:146`). |
| C4 — C4 Verification (red→green) | PASS | Gate reports green-with-fix and red-without-fix PASS (`check-gates.json:33`); I also ran the focused test in a patched temp copy with GTK 3 forced and got 4 tests OK, while the pre-fix temp copy had 2 behavioural failures and 1 skip. |
| C5 — C5 Causal adequacy | PASS | The root cause is the shared column/text building independent primary and secondary filters in target `gramps/gui/views/treemodels/treebasemodel.py:471`, and the new grouped filter keeps all citations for a shown source, including citation-driven sibling cases (`patch.diff:63`, `patch.diff:92`, `patch.diff:117`, `patch.diff:423`). |
| T1 — T1 Structure | N/A | Core-only patch; no addon layout is touched, matching the conformance gate's N/A result (`check-gates.json:59`). |
| T2 — T2 Shape | PASS | New test has the project GPL header and the added core test file is registered in `POTFILES.skip`; conformance gates also pass shape and potfiles checks (`patch.diff:208`, `patch.diff:190`, `check-gates.json:68`, `check-gates.json:77`). |
| T3 — T3 Runtime | PASS | Runtime gates report the core unit baseline matched and GUI interface smoke green, with only baseline tree-drift caveats unrelated to this patch (`check-gates.json:86`, `check-gates.json:95`). |
| T4 — T4 Contribution | N/A | Bundle contains no commit message or PR description artifact to review, and the contribution gate marks this N/A (`check-gates.json:104`). |
| T5 — T5 Judgment | PASS | The implementation follows the brief's preferred judgment call by isolating changed search semantics to the selector and pinning the standalone model's independent secondary search as unchanged (`brief.md:31`, `brief.md:35`, `patch.diff:450`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because no per-fix dogtail GUI repro exists (`check-gates.json:41`), a human must decide whether the headless model red→green evidence is sufficient or manually clear the actual Add Existing Citation dialog UX described in §6; impact is final confidence that the live selector expands/selects as intended, not just its model. |

Target-state caveat: `$PDCA_TARGET` is readable but stale relative to `patch.diff`; it lacks `CitationTreeSelectorModel` and the new test file, and `git apply --check` fails only on drifted `po/POTFILES.skip`. I treated that as a target-state caveat, not a C4 defect, and grounded affected changed-file citations on `patch.diff`.

## §6 Human Clearance Items

1. Validation fitness-to-purpose: run Gramps with the patch applied, open a person, go to Source Citations, choose Add Existing Citation..., search for text matching a source title, click Find, expand the matching source, and confirm an existing citation row is visible and selectable without creating a new citation. Also search for text matching one citation page and confirm sibling citations under that shown source remain reachable.
