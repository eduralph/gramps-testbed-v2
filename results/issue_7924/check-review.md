Task under review: fix Mantis 7924 so a parent primary editor resolves dirty child primary editors before committing, preserving child references instead of silently dropping them.

Target caveat: `$PDCA_TARGET` is `/home/eddie/gramps/gramps`, readable and patch-applicable, but it is on `master` at `aef9f35ec6` while the brief targets `maintenance/gramps61`; new-code citations therefore use `patch.diff` where the target has not been patched.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the required complete graph outcome and abort alternative for the Family→Person flow, not just a warning (`brief.md:18`, `brief.md:24`, `brief.md:29`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The red condition is re-derived from target source: mother child editor is opened with callback (`gramps/gui/editors/editfamily.py:946`), callback is the only mother-handle write (`gramps/gui/editors/editfamily.py:969`), but save reads/commits mother before close (`gramps/gui/editors/editfamily.py:1294`, `gramps/gui/editors/editfamily.py:1308`, `gramps/gui/editors/editfamily.py:1340`). |
| C3 — C3 Change | FAIL | The patch routes only `define_ok_button` clicks through the resolver (`patch.diff:15`, `patch.diff:26`), but parent window close still offers SaveDialog with `self.save` directly (`gramps/gui/editors/editprimary.py:247`, `gramps/gui/editors/editprimary.py:255`), missing the brief's OK/save shared path. |
| C4 — C4 Verification (red→green) | FAIL | Official red→green verification did not run: `run-verify.sh` failed because `/home/eddie/gramps/gramps-6.1-lane1` is missing (`check-gates.json:33`, `check-gates.json:37`); I applied the patch to a temp copy and only the focused unit test passed: `Ran 12 tests ... OK`. |
| C5 — C5 Causal adequacy | FAIL | The save-boundary cause is only partially addressed: OK clicks resolve children first (`patch.diff:48`, `patch.diff:71`), but the existing close→Save path can still commit the parent before child resolution (`gramps/gui/editors/editprimary.py:244`, `gramps/gui/editors/editprimary.py:255`). |
| T1 — T1 Structure | N/A | Addon layout rules do not apply because the patch is core-only with no `addons-source` path (`check-gates.json:51`, `check-gates.json:55`). |
| T2 — T2 Shape | PASS | New core files have GPL headers and are registered in POTFILES.skip (`patch.diff:137`, `patch.diff:153`, `patch.diff:372`, `patch.diff:388`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: decide whether the runtime gate's pre-test crash is acceptable infra debt or must be rerun before merge; baseline runner exited 1 with no JUnit XML (`check-gates.json:77`, `check-gates.json:82`), while my feasible focused unit run passed 12 tests. |
| T4 — T4 Contribution | N/A | No commit message or PR-description artifact is present, so contribution-wrapper checks are not applicable to this artifact-only review (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | FAIL | Reviewer judgment is not merge-ready because the implementation misses an in-scope save entry point and therefore does not cover the full shared save lifecycle (`brief.md:36`, `brief.md:45`, `gramps/gui/editors/editprimary.py:255`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human must validate the GUI fitness-to-purpose on the reporter flow and decide whether OK-only behavior is sufficient despite the brief requiring shared OK/save coverage (`brief.md:24`, `brief.md:32`, `brief.md:156`). |

## §6 Human Clearance Items

1. T3 runtime gate: rerun or explicitly waive the whole-suite baseline after fixing the missing lane/worktree issue reported by `check-gates.json`; the focused patched-temp run only proves `gramps.gui.test.savecascade_test` passes.
2. V fitness-to-purpose: manually drive the reporter flow in the GUI and also test parent window close → Save while the child editor is dirty; the current patch appears to cover OK clicks but not that close/save path.
