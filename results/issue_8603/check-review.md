Task under review: fix Gramps issue 8603 so the Family editor Events tab refreshes the "Main Participants" name after a family participant is edited and saved from the same dialog.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the stale participant-name defect, success criterion, invariant, and exclusions clearly enough to judge the patch (`brief.md:6`, `brief.md:11`, `brief.md:16`, `brief.md:25`). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | DECISION OWED: confirm the red pre-fix GUI repro or committed AT-SPI case because the cited repro test is deliberately outside `patch.diff` and not present in this artifact bundle (`brief.md:31`, `brief.md:35`); source review supports the defect because `person-update` currently reaches only `load_data()` (`gramps/gui/editors/editfamily.py:503`, `gramps/gui/editors/editfamily.py:575`, `gramps/gui/editors/editfamily.py:582`). |
| C3 — C3 Change | PASS | The patch routes `person-update` to a new callback and preserves the top-panel refresh while adding an Events-tab rebuild (`patch.diff:9`, `patch.diff:18`, `patch.diff:30`, `patch.diff:32`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: accept only after a human or available CI runs the named GUI red→green repro, because I could verify `git apply --check` and compile a temporary patched copy, but the AT-SPI test/runner was not available here (`brief.md:35`, `check-gates.json:33`, `check-gates.json:42`). |
| C5 — C5 Causal adequacy | PASS | The cause and effect line up: the stale column is "Main Participants" (`gramps/gui/editors/displaytabs/eventembedlist.py:95`), event rows compute participants from DB data (`gramps/gui/editors/displaytabs/eventrefmodel.py:204`), the embedded list only tracks event signals (`gramps/gui/editors/displaytabs/eventembedlist.py:139`), and `rebuild_callback()` marks/rebuilds the view (`gramps/gui/editors/displaytabs/embeddedlist.py:635`). |
| T1 — T1 Structure | N/A | Core-only one-file patch; no addon layout, manifest, or target-version structure is implicated (`patch.diff:1`). |
| T2 — T2 Shape | PASS | Existing GPL header remains intact and the change adds a normal method in the existing class without new files or translation/POTFILES obligations (`gramps/gui/editors/editfamily.py:1`, `patch.diff:18`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: decide whether available CI/runtime evidence is sufficient despite local framework runners failing before tests; I verified the unpatched target and a temporary patched copy compile with `PYTHONPYCACHEPREFIX`, but `check-gates.json` reports unit/interface runner pre-test failures (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR wrapper artifact is in the bundle, so contribution-wrapper conformance cannot be assessed from these files (`check-gates.json:105`). |
| T5 — T5 Judgment | PASS | The change is narrowly scoped to the in-scope `person-update` refresh path and avoids the explicitly out-of-scope unsaved-data, Gallery/Note, and participant-computation rewrites (`brief.md:25`, `brief.md:28`, `patch.diff:9`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must validate the user-visible Family editor behavior with the target dataset/GUI because artifact review can show the callback path is plausible but cannot observe the rendered Events tab after a real rename (`brief.md:11`, `brief.md:31`). |

## 6. Human Clearance Items

1. C2 reproduction: on a pre-fix `maintenance/gramps61` checkout, load a tree with a family event whose main participant is the father, open Families -> the family -> Events, edit the father from the Family editor, rename him, press OK, and confirm the Events tab still shows the old name.
2. C4 verification: apply `patch.diff`, rerun the same scenario or the withheld `engine/interface/test_bug_0008603_family_event_participant_refresh.py`, and confirm the Events tab "Main Participants" column changes to the new name.
3. T3 runtime: clear the runner-level failures recorded in `check-gates.json` or replace them with CI evidence that reaches the relevant unit/interface tests rather than failing before test execution.
4. V fitness-to-purpose: decide whether rebuilding the family Events tab on every family-member `person-update` is acceptable UX/performance for this editor, given it is scoped to already-open Family editor data and uses the existing embedded-list rebuild mechanism.

Target-state caveat: `$PDCA_TARGET` was readable and `git apply --check --verbose patch.diff` succeeded, but the target checkout reported branch `master` while the brief names `maintenance/gramps61`; new-line citations for the proposed method therefore use `patch.diff`.
