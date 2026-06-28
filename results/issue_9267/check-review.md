# Check Review

Grounding note: `$PDCA_TARGET=/home/eddie/workspace/gramps` is readable, and `git apply --check patch.diff` succeeds there. The target checkout is pre-patch, so existing-behavior citations are grounded on `$PDCA_TARGET`, while added/changed-code citations are grounded on `patch.diff`. `build-notes.md` was not used.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief states the defect, success criterion, invariant, and scope for People flat list re-sort after a display-name format change (`brief.md:9`, `brief.md:13`, `brief.md:16`, `brief.md:25`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The repro describes stale row order until DB reopen, and the red-without-fix verification gate passed (`brief.md:29`, `brief.md:30`, `check-gates.json:33`, `check-gates.json:37`). |
| C3 — C3 Change | PASS | The patch invalidates sort before rebuilding on format changes and makes flat rebuilds recompute cached sort keys in both search and filter paths (`patch.diff:288`, `patch.diff:298`, `patch.diff:45`, `patch.diff:65`, `patch.diff:76`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | Core red→green verification passed, but the GUI AT-SPI repro was skipped/unverifiable; DECISION OWED: decide whether model-level red→green evidence is sufficient for this GUI-surface bug (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:41`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | PASS | The causal chain matches the patch: preferences emit `nameformat-changed`, the existing person-view callback only rebuilt, `ListView` reused model data, and flat rebuilds reused `full_srtkey_hndl_map()` unless empty (`gramps/gui/configure.py:1491`, `gramps/plugins/lib/libpersonview.py:181`, `gramps/gui/views/listview.py:361`, `gramps/gui/views/treemodels/flatbasemodel.py:589`). |
| T1 — T1 Structure | N/A | This is a core-only patch, not an addon-layout change, so addon structure rules do not apply (`patch.diff:1`, `patch.diff:273`, `check-gates.json:60`). |
| T2 — T2 Shape | PASS | The new core test carries the project GPL header and is registered in `po/POTFILES.skip`; shape and potfiles gates passed (`patch.diff:93`, `patch.diff:313`, `check-gates.json:69`, `check-gates.json:78`). |
| T3 — T3 Runtime | NEEDS-HUMAN | The unit runtime baseline crashed before producing JUnit while the GUI smoke passed; DECISION OWED: decide whether to accept this non-gating infrastructure gap or require a clean rerun (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description is present in the artifact bundle, so contribution-wrapper review is not applicable (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | NEEDS-HUMAN | The patch also invalidates sort on `placeformat-changed`, while the brief centers name-format sorting and excludes other-column sorting; DECISION OWED: decide whether this scope expansion is acceptable (`brief.md:13`, `brief.md:25`, `brief.md:27`, `patch.diff:281`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Fitness-to-purpose is user-visible People flat behavior, and the GUI repro was not exercised; DECISION OWED: manually/owner-confirm that changing Display Name format re-sorts the live People flat list without reopening (`brief.md:13`, `brief.md:29`, `check-gates.json:41`). |

## §6 Human Clearances

1. C4 — Verification sufficiency: core red→green evidence exists, but the GUI AT-SPI repro was skipped. Human must decide whether the model-level regression test adequately covers the GUI callback path, or whether sign-off requires a successful GUI repro.
2. T3 — Runtime evidence: the unit baseline failed before JUnit output, while GUI smoke passed. Human must decide whether this is acceptable non-gating infrastructure noise or whether a clean unit-suite rerun is required.
3. T5 — Scope judgment: the implementation handles `placeformat-changed` as well as `nameformat-changed`. Human must decide whether that small expansion is acceptable despite the brief’s name-format focus and out-of-scope note for other-column sorting.
4. V — Fitness-to-purpose: the actual product criterion is live People flat list re-sort after changing Display Name format. Human must confirm the UI behavior because the automated GUI repro did not run to red/green completion.
