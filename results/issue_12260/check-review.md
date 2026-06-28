# Check Review

## Target-State Caveat

`$PDCA_TARGET` was set and readable at `/home/eddie/workspace/gramps`, but the checked-out branch observed there is not the brief's stated `maintenance/gramps61` target (`brief.md:24`). The production `editlink.py` preimage matches the patch index for that file (`patch.diff:2`), and the patch applies cleanly to the target tree; added lines and the new test are therefore grounded on `patch.diff`, not treated as target defects.

## Verdict Table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | Brief provides defect, success criterion, invariant, scope, and test target; the detected Note-vs-handle contract conflict is escalated under C5/T5 (`brief.md:9`, `brief.md:16`, `brief.md:19`, `brief.md:29`, `brief.md:36`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix `_on_new_callback` dereferences `.handle` on its callback argument, and a real editor callback can emit only `get_handle()`, so the handle-string red case is re-derived (`gramps/gui/editors/editlink.py:156`, `gramps/gui/editors/editlink.py:160`, `gramps/gui/editors/editcitation.py:400`, `gramps/gui/editors/editcitation.py:401`). |
| C3 — C3 Change | PASS | Patch reads string callbacks as handles using the selected object type and preserves the object-callback path; the new test is registered in POTFILES.skip (`patch.diff:20`, `patch.diff:21`, `patch.diff:23`, `patch.diff:26`, `patch.diff:124`). |
| C4 — C4 Verification (red→green) | PASS | Gating verifier reports targeted red-without-fix and green-with-fix PASS; the missing GUI repro is non-gating and not a fabricated C4 blocker (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:42`, `check-gates.json:47`). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: target `EditNote.save` passes the object while `EditCitation.save` passes a handle, so a human must decide whether the Note/ToDo root cause is misstated or a different base is authoritative, because the patch fixes handle-string callbacks but not an independently proven Note-specific route (`gramps/gui/editors/editnote.py:381`, `gramps/gui/editors/editnote.py:383`, `gramps/gui/editors/editcitation.py:400`, `gramps/gui/editors/editcitation.py:401`, `patch.diff:20`). |
| T1 — T1 Structure | N/A | Core-only patch has no addons-source path, so addon layout structure does not apply (`check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | Existing touched production file has GPL header, the new test adds the GPL header, and the new core test is listed in POTFILES.skip (`gramps/gui/editors/editlink.py:1`, `patch.diff:37`, `patch.diff:53`, `patch.diff:124`). |
| T3 — T3 Runtime | FAIL | Whole-suite unit baseline runner exited before producing JUnit XML, while GUI smoke passed; this is runtime coverage debt rather than C4 red-green failure (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description is present in the bundle, so contribution-wrapper review does not apply (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: human must judge whether targeted C4 red-green is enough despite the non-gating unit-runner crash and absent GUI red→green repro, because that determines sign-off risk (`check-gates.json:37`, `check-gates.json:46`, `check-gates.json:91`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: human must validate fitness to the actual Mantis 12260 intent because artifact-only review confirms a handle-string callback fix but not the brief's specific Note/ToDo route (`brief.md:16`, `brief.md:33`, `brief.md:35`, `gramps/gui/editors/editnote.py:381`, `gramps/gui/editors/editnote.py:383`). |

## §6 Human Clearance Items

1. C5 — Decide whether the authoritative defect is the general handle-string new-object callback path, such as Citation, or specifically the Note/ToDo path described in the brief. Impact: if Note/ToDo is required, require an interface repro or corrected base evidence; if the handle-string path is the intended bug, causal adequacy clears.
2. T5 — Decide whether to accept sign-off risk with targeted C4 red-green passing while the whole-suite unit baseline crashed before JUnit and GUI red→green repro is absent. Impact: acceptance relies on the focused regression test rather than full runtime confidence.
3. V — Decide whether the patch is fit for Mantis 12260 on the intended maintenance base. Impact: this is the final approve/reject decision after resolving the scope and verification-risk questions above.
