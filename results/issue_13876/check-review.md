# Check Review

Target-state caveat: `$PDCA_TARGET` is readable at `/home/eddie/workspace/gramps`, but it is on `fix/bug-8850-gedcom-import-cal-date-case-sensitive` rather than the brief's `maintenance/gramps61` target; the touched `libsourceview.py` preimage matches the patch index and `git apply --check` succeeds, while added-file citations are therefore grounded on `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 -- C1 Spec | PASS | The brief defines the failing workflow, success criterion, invariant, scope, and repro target tightly enough to judge the patch (`brief.md:9`, `brief.md:12`, `brief.md:15`, `brief.md:25`, `brief.md:30`). |
| C2 -- C2 Reproduction (red pre-fix) | PASS | The required failure is "citation remains after delete" (`brief.md:30`), and the red/green gate reports red-without-fix exercised and passed as a red check (`check-gates.json:33`, `check-gates.json:37`). |
| C3 -- C3 Change | PASS | The target helper classifies non-source selected handles as citations (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:49`) but then always removes a source (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:101`), and the patch replaces that with type-dispatched removal (`patch.diff:11`). |
| C4 -- C4 Verification (red->green) | PASS | Core verification reports green-with-fix and red-without-fix both PASS (`check-gates.json:33`, `check-gates.json:37`); GUI AT-SPI was skipped/non-gating, so final GUI fitness is deferred to V (`check-gates.json:42`, `check-gates.json:46`). |
| C5 -- C5 Causal adequacy | PASS | The defect path is causal: selected citation handles flow to `("Citation", handle)` (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:49`), backlink cleanup already uses `obj_type` (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:97`), and only the terminal remove call was hard-coded to source (`/home/eddie/workspace/gramps/gramps/plugins/lib/libsourceview.py:101`). |
| T1 -- T1 Structure | N/A | No addon-source layout is touched; the artifact changes core library/test/POTFILES paths only (`patch.diff:1`, `patch.diff:16`, `patch.diff:166`; `check-gates.json:60`). |
| T2 -- T2 Shape | PASS | The new core test carries the project GPL header (`patch.diff:22`) and the new Python test files are registered in `POTFILES.skip` as requested by the brief (`brief.md:40`, `patch.diff:174`). |
| T3 -- T3 Runtime | PASS | Runtime gates report the core unit baseline matched and the GUI smoke was green, with only baseline drift caveats recorded (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 -- T4 Contribution | N/A | No commit message or PR description artifact is present in the bundle, and the contribution gate marks that wrapper check N/A (`check-gates.json:105`, `check-gates.json:109`). |
| T5 -- T5 Judgment | PASS | The patch stays inside the scoped delete behavior and supporting test/i18n registration; duplicate confirmation dialogs and source-row changes remain out of scope (`brief.md:25`, `brief.md:27`, `patch.diff:1`, `patch.diff:16`, `patch.diff:166`). |
| V -- Validation -- fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human must decide whether the headless production-helper red/green evidence is sufficient for the GUI success criterion after confirmation, because the GUI-specific interface repro was skipped (`brief.md:12`, `check-gates.json:42`, `check-gates.json:46`). |

## §6 Human Decisions

1. V -- Validation -- fitness-to-purpose: decide whether to accept the core helper red/green proof as sufficient for the user-facing Citation Tree delete workflow, despite the skipped GUI AT-SPI repro. Impact: accepting clears sign-off on behavior; rejecting requires a runnable GUI reproduction before this can be called fit for purpose.
