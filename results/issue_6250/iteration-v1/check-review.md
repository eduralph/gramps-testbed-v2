# Check Review

## Scope Notes

Reviewed artifacts in this directory: `brief.md` and `check-gates.json`. `patch.diff` is absent; this is also recorded by the C4 gate (`check-gates.json:33`-`check-gates.json:38`).

`$PDCA_TARGET` is readable at `/home/eddie/workspace/gramps`, but it is checked out on `fix/bug-8850-gedcom-import-cal-date-case-sensitive`, not the requested `maintenance/gramps61`; this is a target-state caveat, not a patch defect. The cited target source only corroborates that the cairo workaround site exists in the readable checkout (`gramps/plugins/lib/libcairodoc.py:669`-`gramps/plugins/lib/libcairodoc.py:715`).

## Verdict Table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief gives a checkable investigative success criterion for `Pango.AttrList.get_iterator()` availability and explicitly says no functional change should ship (`brief.md:13`-`brief.md:20`). |
| C2 — C2 Reproduction (red pre-fix) | N/A | The brief states there is no user-facing repro because the workaround prevents the original error, and defines the probe instead (`brief.md:31`-`brief.md:34`). |
| C3 — C3 Change | FAIL | `patch.diff` is absent, so there is no reviewable written finding/change artifact even though the brief expects the investigation result to be recorded in the bundle (`brief.md:35`-`brief.md:37`). |
| C4 — C4 Verification (red→green) | FAIL | The configured verification gate failed because no `patch.diff` was present in the result bundle, leaving no artifact-backed red/green or probe evidence to inspect (`check-gates.json:33`-`check-gates.json:38`). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: decide whether the correct supported GI stack on `maintenance/gramps61` was actually verified, because that determination controls whether the workaround at `gramps/plugins/lib/libcairodoc.py:669` remains required or becomes cleanup work. |
| T1 — T1 Structure | N/A | No addon path is present in the absent patch artifact, and the gate classifies addon structure as not applicable (`check-gates.json:51`-`check-gates.json:56`). |
| T2 — T2 Shape | N/A | No checkable changed Python file is available because `patch.diff` is absent; the shape gate records N/A for lack of a checkable `.py` path (`check-gates.json:60`-`check-gates.json:65`). |
| T3 — T3 Runtime | PASS | The runtime baseline gate passed with the recorded known reds, with only a baseline-tree-drift caveat rather than a new failure (`check-gates.json:78`-`check-gates.json:83`). |
| T4 — T4 Contribution | N/A | No commit message or PR description is included in the bundle, so contribution-wrapper checks do not apply (`check-gates.json:87`-`check-gates.json:92`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether an investigation-only cycle can be accepted without `patch.diff` or another reviewable written finding, because accepting it would sign off an artifact gap rather than a documented verification result. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: decide whether the available evidence is fit to resolve Mantis 6250's open condition, because the brief requires either cleanup follow-up if available or wontfix/by-design if unavailable (`brief.md:13`-`brief.md:20`). |

## §6 Human Clearance Items

1. C5 — Causal adequacy: Decide whether verification was performed against the supported PyGObject/Pango stack for `maintenance/gramps61`; impact is the ticket disposition and whether the workaround is obsolete.
2. T5 — Judgment: Decide whether to accept an investigation bundle that lacks `patch.diff` and therefore lacks a reviewable written finding; impact is sign-off versus returning to Do for a concrete artifact.
3. V — Validation: Decide whether the artifact set is fit for Mantis 6250's purpose despite the missing patch artifact and target-branch caveat; impact is whether Check can endorse resolution or must require a rerun/rebundle.
