# Check Review

Target-state caveat: `$PDCA_TARGET` is readable but is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` and does not contain this bundle's changes; `gramps/gui/views/tags.py` still matches the patch's old blob (`235be79c82`) with the inline columns and no search binding at `gramps/gui/views/tags.py:478`. Citations for bundled added/changed lines therefore use `patch.diff`; this is not a C4 blocker.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief gives a concrete UI defect and success criterion: Organize Tags search must either target Name or be removed, within `gramps/gui/views/tags.py` scope (`brief.md:13`, `brief.md:24`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The pre-fix target has the tag list columns and `ListModel` creation but no search binding (`gramps/gui/views/tags.py:478`, `gramps/gui/views/tags.py:485`), matching the brief's Ctrl-F/no-selection-move repro (`brief.md:29`); the red-without-fix gate passed (`check-gates.json:37`). |
| C3 — C3 Change | PASS | The patch chooses the allowed "search column = Name" resolution by defining Name as model column 2 and calling `set_search_column` on the actual `namelist` TreeView (`patch.diff:16`, `patch.diff:44`, `patch.diff:63`). |
| C4 — C4 Verification (red→green) | PASS | The configured per-fix verification reports green-with-fix and red-without-fix PASS (`check-gates.json:33`, `check-gates.json:37`); the missing GUI dogtail repro is non-gating/unverifiable, not a stale-target compile/apply failure (`check-gates.json:42`, `check-gates.json:47`). |
| C5 — C5 Causal adequacy | PASS | The change directly binds GTK interactive search to the visible Name model column while preserving the existing column order (`patch.diff:19`, `patch.diff:29`, `patch.diff:44`), which satisfies the invariant that the enabled search control must have an effect. |
| T1 — T1 Structure | N/A | The bundle touches core GUI/test/translation files, not an addon layout; the configured T1 gate also reports addon structure N/A (`patch.diff:1`, `patch.diff:70`, `patch.diff:193`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | The new test carries the GPL header and the added core test files are registered in `POTFILES.skip` as required by the brief (`patch.diff:76`, `patch.diff:92`, `patch.diff:201`, `patch.diff:204`). |
| T3 — T3 Runtime | PASS | The whole core unit baseline and GUI smoke gates both pass, with only recorded baseline drift caveats (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is in the bundle, so the contribution-wrapper gate is explicitly N/A (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | PASS | Scope is narrow and coherent: production code changes only the Organize Tags TreeView search setup, while tests cover the column index and binding side effect (`patch.diff:60`, `patch.diff:63`, `patch.diff:155`, `patch.diff:170`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because the GUI dogtail repro is absent/unverifiable and the unit test uses a recording stand-in for the TreeView, a human must decide whether the artifact evidence is sufficient for the actual user-facing Ctrl-F/type-ahead behavior (`check-gates.json:42`, `check-gates.json:46`, `patch.diff:105`, `patch.diff:113`). |

## §6 Human Decisions Owed

1. V — Validation — fitness-to-purpose: decide whether the red→green unit evidence plus the direct `set_search_column(_TAG_NAME_COL)` change is sufficient to accept the real Organize Tags UI behavior, or whether a manual/dogtail validation artifact is required before sign-off.
