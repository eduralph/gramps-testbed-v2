# Check Review

Artifact-only review using `patch.diff`, `brief.md`, `check-gates.json`, and `$PDCA_TARGET` only for source line grounding. Target-state caveat: `$PDCA_TARGET/po/POTFILES.skip` has unrelated local `familyview` additions, so POTFILES additions are grounded on `patch.diff`; this is not treated as a C4 blocker.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect, invariant, scoped files, repro, and success criterion for escaped-markup paragraph splits (`brief.md:21`, `brief.md:49`, `brief.md:63`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The red condition is explicit and independently gated: escaped `&amp;` before `BOLD` should rebase bold to bytes 0..4, and C4 reports `red-without-fix=PASS` (`brief.md:63`, `check-gates.json:37`). |
| C3 — C3 Change | PASS | The patch removes the target markup-walk/reparse workaround (`gramps/plugins/lib/libcairodoc.py:685`, `gramps/plugins/lib/libcairodoc.py:711`) and calls a parsed-attr reindex helper instead (`patch.diff:73`, `patch.diff:140`). |
| C4 — C4 Verification (red→green) | PASS | The configured isolation verification reports both `green-with-fix=PASS` and `red-without-fix=PASS`, and the new test asserts the escaped-entity bold run offsets (`check-gates.json:33`, `check-gates.json:37`, `patch.diff:274`, `patch.diff:286`). |
| C5 — C5 Causal adequacy | PASS | The cause is directly addressed: target code counts bytes while walking serialized markup (`gramps/plugins/lib/libcairodoc.py:694`, `gramps/plugins/lib/libcairodoc.py:705`), while the replacement shifts/clamps parsed Pango attribute offsets (`patch.diff:169`, `patch.diff:183`). |
| T1 — T1 Structure | N/A | No addon-source structure is touched; the gate records doc-16 structure as addon-only and N/A for this core patch (`check-gates.json:51`, `check-gates.json:55`). |
| T2 — T2 Shape | PASS | New Python files carry GPL headers and are registered in POTFILES.skip, including the helper and test package entries (`patch.diff:98`, `patch.diff:200`, `patch.diff:321`, `patch.diff:331`, `check-gates.json:60`, `check-gates.json:73`). |
| T3 — T3 Runtime | PASS | Whole-suite baseline gate passes with only the recorded seven known reds; the reported baseline drift is a target-state caveat, not a new runtime failure (`check-gates.json:78`, `check-gates.json:82`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present, so the contribution-wrapper gate is explicitly N/A (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | PASS | The patch stays within the scoped paragraph attrlist reindex path and headless regression seam, leaving the brief's out-of-scope split-point, marklist, and other backend behavior untouched (`brief.md:49`, `brief.md:59`, `patch.diff:67`, `patch.diff:230`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: decide whether helper-level Pango AttrList red→green coverage is sufficient user-facing validation for cairo-rendered reports, because the success criterion is report-purpose correctness beyond the artifact gates (`brief.md:21`, `brief.md:28`). |

## §6 Human-Clearing Items

1. V — Validation — fitness-to-purpose: human sign-off must decide whether the headless production-seam test plus C4 red→green proof is enough validation for the cairo report pagination surface, or whether a rendered PDF/PS report sample is required before acceptance.
