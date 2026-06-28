## Verdict

Target-state caveat: `$PDCA_TARGET` was readable, but the checkout was not on the briefed `maintenance/gramps61` branch; production citations below use that target where the relevant source is present, and citations for patch-added files use `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief gives a concrete verification target: `Note.get_preview()` must use `interface.note-preview-length`, with status-bar residue reserved for follow-up rather than this fix scope (`brief.md:12`, `brief.md:16`, `brief.md:23`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added tests encode the old-red condition by setting lengths below and above 79 and expecting those configured limits, which would fail under the brief's hardcoded-79 behavior (`patch.diff:53`, `patch.diff:59`, `brief.md:27`). |
| C3 — C3 Change | PASS | The patch is scoped to verification: it adds `gramps/gen/lib/test/note_test.py` and registers that new core test in `po/POTFILES.skip` as the brief requires (`patch.diff:1`, `patch.diff:83`, `brief.md:30`, `brief.md:37`). |
| C4 — C4 Verification (red→green) | FAIL | The configured C4 verification gate reports `essential-line retry for 6.1 also FAILED` and labels it a real failure, so green post-fix verification is not established (`check-gates.json:33`, `check-gates.json:37`). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: accept whether closing the causal chain on the Preview-column path is adequate while the target still has a 40-character Note status-bar truncation that the brief says should be follow-up, because this determines whether issue 8597 can be closed or must split scope (`gramps/gen/lib/note.py:282`, `gramps/gui/views/treemodels/notemodel.py:122`, `gramps/gen/utils/db.py:353`, `gramps/gen/utils/db.py:359`, `brief.md:16`). |
| T1 — T1 Structure | N/A | No addon-source path is touched, so addon structure rules do not apply to this core verification patch (`check-gates.json:51`, `check-gates.json:55`). |
| T2 — T2 Shape | PASS | The new Python test carries the GPL header and the new core test file is added to `po/POTFILES.skip`, satisfying the applicable shape/POTFILES requirements (`patch.diff:7`, `patch.diff:12`, `patch.diff:87`, `patch.diff:91`). |
| T3 — T3 Runtime | PASS | The broader core unit baseline gate passed against the recorded baseline despite known unrelated reds and tree-drift caveat (`check-gates.json:78`, `check-gates.json:82`). |
| T4 — T4 Contribution | N/A | The bundle contains no commit message or PR description artifact for contribution-wrapper review (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | FAIL | Review judgment cannot recommend sign-off while overall gates are failed due to the C4 verification failure (`check-gates.json:3`, `check-gates.json:33`, `check-gates.json:37`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: decide whether the verification-only artifact is fit to resolve the Mantis issue despite failed C4 automation and the deliberately deferred status-bar path, because this is the product/release acceptance call (`brief.md:12`, `brief.md:15`, `brief.md:16`, `check-gates.json:105`). |

## §6 Human Clearance Items

1. C5 causal adequacy: decide whether the patch's `Note.get_preview()` coverage is sufficient to close the Preview-column defect while tracking the remaining status-bar 40-character path as a follow-up, or whether that residue keeps the issue open.
2. V validation fitness-to-purpose: decide whether to accept this verification bundle only after C4 is rerun green, or to reject/return it now because the configured verification gate failed.
