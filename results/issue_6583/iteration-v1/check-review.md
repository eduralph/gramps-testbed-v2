# Check Review

Target-state caveat: `$PDCA_TARGET` is readable, but it is currently on `fix/bug-8850-gedcom-import-cal-date-case-sensitive`, not the briefed `maintenance/gramps61` branch. Because `patch.diff` is absent and the brief explicitly allows a no-patch verification disposition, I treated the automated "no patch.diff" C4 failures as a harness/artifact-shape mismatch rather than a patch defect.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief gives a narrow success criterion: confirm Add/Edit/Merge/Remove list-view toolbar controls no longer carry the reported ellipsis labels, with no patch if confirmed (`brief.md:12`). |
| C2 — C2 Reproduction (red pre-fix) | N/A | The original red condition is documented as historical v4.0.0 behavior, while this cycle is current-state verification on `maintenance/gramps61`, not a new fix needing a live red pre-fix run (`brief.md:9`, `brief.md:28`). |
| C3 — C3 Change | N/A | No source patch is expected for the accepted success path: the brief says "Verification, not a new fix (no patch if confirmed)" and the review directory has no `patch.diff` (`brief.md:14`). |
| C4 — C4 Verification (red→green) | PASS | Current-state source verification is green for the requested label check: list-view actions are defined as `"Add"`, `"Remove"`, `"Merge"`, and `"Edit"` without ellipses (`gramps/gui/views/listview.py:226`, `gramps/gui/views/listview.py:237`); the automated C4 failures are only "no patch.diff" (`check-gates.json:33`, `check-gates.json:42`). |
| C5 — C5 Causal adequacy | PASS | The defect turns on inconsistent trailing ellipses in Add/Edit/Merge toolbar action labels, and the relevant `ActionGroup` entries no longer contain those labels; remaining ellipsis strings are progress/status text, not toolbar action labels (`gramps/gui/views/listview.py:226`, `gramps/gui/views/listview.py:674`, `gramps/gui/views/listview.py:1388`). |
| T1 — T1 Structure | N/A | No addon layout is present or changed; the gate also classifies T1 as addon-only and not applicable without an addons-source path (`check-gates.json:60`). |
| T2 — T2 Shape | N/A | No checkable Python patch or new/removed core Python file is present, matching the gate's no-patch/no-checkable-path result (`check-gates.json:69`, `check-gates.json:78`). |
| T3 — T3 Runtime | PASS | Runtime gates are not regressed: unit baseline matches known reds and GUI smoke is green, with only baseline-tree-drift caveats reported (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description wrapper is present, which is acceptable for a no-patch verification bundle unless the human elects to publish a documentation/closure PR (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the branch-target caveat and no-patch verification artifact are acceptable for closing this cycle; impact is whether this proceeds as a resolved verification or must be rerun against an exact `maintenance/gramps61` checkout before sign-off (`brief.md:20`, `check-gates.json:33`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: decide whether source-level evidence plus any required manual UI sign-off satisfies the user-visible toolbar-label purpose; impact is closing Mantis 6583 as already fixed versus requiring a follow-up UI/text check (`brief.md:32`, `brief.md:40`). |

## §6 Human Clearance Items

1. T5 Judgment: Clear the target-state/artifact-shape caveat. `$PDCA_TARGET` is readable but not on the named branch, and the automated C4 gate failed because it expected `patch.diff`; decide whether this no-patch verification bundle may stand or must be rerun on an exact `maintenance/gramps61` checkout.
2. Validation fitness-to-purpose: Perform or accept the manual UI sign-off described by the brief. The source evidence shows no Add/Edit/Merge toolbar action ellipsis in `listview.py`, but the human must decide whether that is enough to resolve the reported user-visible inconsistency.
