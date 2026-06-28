# Check Review

## 1. Artifact caveat

`patch.diff` is absent from the review directory, and the gate artifact records the same missing-patch condition for both verification commands (`check-gates.json:37`, `check-gates.json:46`). `PDCA_TARGET` was readable, so source citations below use `/home/eddie/workspace/gramps`; where the missing patch prevents reviewing the proposed change, the basis is grounded in the supplied artifacts.

## 2. Verdict table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the defect, success criterion, invariant, GUI surface, scope, and reproduction path clearly enough to test against (`brief.md:9`, `brief.md:12`, `brief.md:15`, `brief.md:24`, `brief.md:28`). |
| C2 — C2 Reproduction (red pre-fix) | FAIL | The brief gives a manual repro and expects an AT-SPI repro test, but the gates show no configured/recorded red pre-fix reproduction result (`brief.md:28`, `brief.md:31`, `check-gates.json:15`). |
| C3 — C3 Change | FAIL | The review cannot identify or inspect the proposed code change because the required `patch.diff` artifact is missing, despite C3's oracle being `patch.diff` (`check-gates.json:24`, `check-gates.json:26`). |
| C4 — C4 Verification (red→green) | FAIL | Red-to-green verification did not run against a patch: both unit and GUI verification gates fail on `no patch.diff`, which is an artifact failure rather than a target-state compile/apply defect (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:42`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | FAIL | The target source supports the likely causal area: `SourceView` connects only source signals while `ListView` connects exactly its `signal_map`, and citation views wire `citation-update`; however no patch is present to show the defect is causally fixed (`gramps/plugins/view/sourceview.py:117`, `gramps/gui/views/listview.py:844`, `gramps/plugins/view/citationlistview.py:150`, `gramps/plugins/view/citationtreeview.py:143`). |
| T1 — T1 Structure | N/A | The brief scopes this as a core GUI change, not an addon layout change, and the T1 gate also reports addon structure as not applicable (`brief.md:24`, `check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | N/A | No changed Python file can be shape-reviewed because `patch.diff` is missing; this is already captured as the C3 artifact failure, not a separate style finding (`check-gates.json:69`, `check-gates.json:73`, `check-gates.json:78`, `check-gates.json:82`). |
| T3 — T3 Runtime | FAIL | Runtime gates are not clean: the core unit baseline reports four new failures, although the GUI smoke gate is green (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description was included, and the brief keeps the work in draft until Check sign-off, so contribution-wrapper checks do not apply to this artifact bundle (`brief.md:46`, `check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | FAIL | Reviewer judgment cannot accept a bundle with no patch and no red-to-green verification, because the success criterion turns on visible citation-row refresh after save (`brief.md:12`, `check-gates.json:37`, `check-gates.json:46`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: after a complete patch and verification bundle exist, a human must decide whether the GUI behavior satisfies the user-facing purpose: the saved citation row refreshes in-place in Sources view without navigation (`brief.md:12`, `brief.md:24`). |

## §6 Human clearance items

1. **V — Validation — fitness-to-purpose:** Decide, after `patch.diff` and red-to-green evidence are supplied, whether the user-visible Sources view behavior meets the success criterion. Impact: without this clearance, the review can only reject the current artifact bundle, not confirm the fix is fit for release.
