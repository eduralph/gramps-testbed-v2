# Check Review

Artifact caveat: `patch.diff` is absent from this review directory. `$PDCA_TARGET` is set and readable at `/home/eddie/workspace/gramps`; it appears to be an unpatched base, not a stale or unreadable target. Blocking findings below are therefore artifact/evidence failures, not target-state ordering failures.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief states a concrete Persian leap-boundary defect, identity round-trip success criterion, scoped files, and required test/POTFILES handling (`brief.md:9`, `brief.md:14`, `brief.md:28`, `brief.md:37`, `brief.md:41`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | I re-derived the red case on readable `$PDCA_TARGET`: `persian_ymd(persian_sdn(1400, 12, 30))` returns `(1401, 1, 1)`, with the involved functions at `gramps/gen/lib/gcalendar.py:567` and `gramps/gen/lib/gcalendar.py:587`. |
| C3 — C3 Change | FAIL | No `patch.diff` exists in the artifact directory, so the proposed delta cannot be inspected despite C3 naming `patch.diff` as its oracle (`check-gates.json:24`). |
| C4 — C4 Verification (red→green) | FAIL | The configured C4 gate failed because there was no patch artifact to verify, so red-to-green evidence is absent (`check-gates.json:33`, `check-gates.json:37`). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | DECISION OWED: because the delta is absent, a human must decide whether to reject this cycle as an incomplete artifact bundle or request the builder's patch before judging whether the fix addresses the Persian leap-day cause without collateral calendar changes (`brief.md:28`, `check-gates.json:42`). |
| T1 — T1 Structure | N/A | Addon layout rules do not apply to the scoped core `gcalendar.py` change; no addon surface is in scope (`brief.md:25`, `brief.md:28`). |
| T2 — T2 Shape | FAIL | The brief requires a new core test plus `po/POTFILES.skip` registration, but absent `patch.diff` means neither shape requirement can be verified (`brief.md:37`, `brief.md:41`, `check-gates.json:69`). |
| T3 — T3 Runtime | PASS | Whole-suite baseline gate matched the recorded baseline with seven known reds, while noting baseline tree drift; this is baseline fitness only, not patch verification (`check-gates.json:78`, `check-gates.json:82`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present, so contribution-wrapper checks are not applicable to this artifact-only review (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: the human must decide whether Check may proceed on a bundle with no patch, since C3/C4/T2 cannot be substantively assessed from target base plus gates alone (`check-gates.json:3`, `check-gates.json:96`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: validation is always human-owned; here the human must withhold fitness-to-purpose sign-off until an inspectable patch and focused green test demonstrate the valid Persian-date bijection required by the brief (`brief.md:14`, `brief.md:19`). |

## Findings

1. Blocking artifact gap: `patch.diff` is missing. That prevents independent review of the code change, the new test, and the required POTFILES registration.
2. The original defect is real on the readable target base: the Persian leap-day round trip for `1400-12-30` still returns the next year.
3. The C4 failure is not being treated as a target staleness/apply failure. The gate failed because the patch artifact was unavailable.

## §6 Human Clearance Items

1. C5 — Causal adequacy: decide whether this cycle is rejected as incomplete now, or returned to the builder to supply `patch.diff` so the claimed root cause and fix can be reviewed.
2. T5 — Judgment: decide whether any non-blocking gates may be credited when the central patch artifact is missing; impact is whether Check can issue sign-off or must require artifact regeneration.
3. V — Validation fitness-to-purpose: decide, after patch evidence exists, whether the fix satisfies the project need: valid Persian leap-year dates must round-trip through SDN without date drift.
