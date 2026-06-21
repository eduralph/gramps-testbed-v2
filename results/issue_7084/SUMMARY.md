# Result — issue 7084 / dateparser-partial-date-modifier-roundtrip

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: As filed (2013, against the developer "Check Localized Date Displayer and
- Success criterion: **Verify-first, then conditional.** Do MUST first reproduce on
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the partial-date (month + year, no day) parse path in the English date parser,

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_7084
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2-potfiles – N/A: no patch.diff
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 7084 / dateparser-partial-date-modifier-roundtrip

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)
**Artifacts present:** `brief.md`, `check-gates.json`
**Artifacts absent:** `patch.diff` (no such file in bundle), `build-notes.md` (deliberately withheld)
**`$PDCA_TARGET`:** unset — all path:line citations grounded against `check-gates.json` and `brief.md` only
**Overall gate result (from engine):** `fail` (C4, gating: true)

---

## §1 Bundle summary

The builder produced **no patch**. The `check-gates.json` engine records C4 as a hard failure
(`"result": "fail"`, `"gating": true`) because no `patch.diff` appeared in
`results/issue_7084`. The remaining change-gated elements (C1, C2, C3, C5, T5, V) were
recorded as `"none"` — not run — and T1/T2/T4 were self-scored N/A by the engine due to the
absent diff.

This outcome is consistent with the brief's **verify-first, then conditional** disposition
(`brief.md:16–21`): if no live round-trip failure is found on `maintenance/gramps61`, no patch
ships and the bundle is expected to route to §6 as a verify-first close. However, that path
requires human confirmation that the builder actually ran the reproduction step and found
nothing — evidence of that run is not visible in the present artifacts.

---

## §2 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md` is fully present and unambiguous: defect class (partial-date display→parse round-trip failure, Mantis 7084), verify-first success criterion (`brief.md:16–21`), invariant (`brief.md:23–27`), repo/branch (`gramps-project/gramps @ maintenance/gramps61`, `brief.md:28`), repro instruction (`brief.md:46–48`), scope with prior-art signal (`brief.md:31–43`), §6 routing clause for the no-reproduction case (`brief.md:19–21`) |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No reproduction evidence in any artifact; `check-gates.json:8` records `"result": "none"` (not run); `build-notes.md` withheld; brief explicitly allows no-reproduction as the likely outcome (`brief.md:18`), but a human must confirm the builder ran DateParser over DateDisplay output for the partial-date classes on `maintenance/gramps61` and documented the result |
| C3 — C3 Change | N/A | No `patch.diff` present; per `brief.md:19–21` no patch is correct if nothing reproduces; engine self-scored T1/T2/T4 N/A for the same reason (`check-gates.json:55, 65, 92`); this verdict is conditional on C2 human clearance confirming no live failure was found |
| C4 — C4 Verification (red→green) | FAIL | `check-gates.json:37–40`: `"result": "fail"`, `"gating": true`, reason `"run-verify.sh: no patch.diff in results/issue_7084"`; mechanical gate expects a diff and found none; the brief's verify-first close path (`brief.md:19–21`) provides a stated exception, but waiving this gating failure requires explicit human sign-off — see §6 |
| C5 — C5 Causal adequacy | N/A | No patch produced; without a proposed change there is no causal chain to assess; if C2 resolves to confirmed no-reproduction, C5 does not apply |
| T1 — T1 Structure | N/A | Engine self-scored: `check-gates.json:55`: "N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)"; no addon path implicated regardless of patch status |
| T2 — T2 Shape | N/A | Engine self-scored: `check-gates.json:65`: "N/A: no checkable .py path in patch.diff"; no diff to inspect for GPL header or `print()` advisory; T2-potfiles likewise N/A (`check-gates.json:73`) |
| T3 — T3 Runtime | PASS | Engine recorded pass: `check-gates.json:82–83`: "matches recorded baseline: 7 known test red(s)"; ⚠ note baseline tree drift warning (`"recorded detached@674e3b"`) — baseline was captured at a detached HEAD state; human should confirm baseline commit is on the `maintenance/gramps61` line |
| T4 — T4 Contribution | N/A | Engine self-scored: `check-gates.json:92`: "N/A: no commit-msg.txt or pr-description.md in the bundle"; correct for a no-patch verify-first close |
| T5 — T5 Judgment | NEEDS-HUMAN | No patch to judge against the brief's scope constraint; no builder reasoning visible in artifacts (`build-notes.md` withheld); human must assess whether the verify-first execution was adequate (which strings were tested, which locale, which `gramps61` HEAD) and whether the scope constraint (`brief.md:31–43`) was respected |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human item; no patch shipped; human must confirm that a verify-first close is the correct disposition for Mantis 7084 and that the ticket should be updated accordingly |

---

## §3 Key observations

1. **No patch is not automatically wrong here.** The brief's §Success criterion
   (`brief.md:16–21`) and disposition hint (`brief.md:61`) both make the no-patch, §6-routing
   outcome explicitly legitimate — and `brief.md:21` prohibits manufacturing a change to
   satisfy the gate. The engine's C4 FAIL reflects a mechanical expectation, not a
   brief violation. This distinction must be resolved by a human (§6 item 1).

2. **Reproduction evidence is the critical gap.** The entire conditional logic of the brief
   turns on whether a live round-trip failure exists on `maintenance/gramps61`. That question
   is unanswered by the available artifacts. Without `build-notes.md`, there is no record of
   which strings were exercised, under which locale, against which commit.

3. **T3 baseline drift warning** (`check-gates.json:83`). The engine passed T3 but flagged
   that the baseline was recorded at `detached@674e3b`. If this is not on the
   `maintenance/gramps61` lineage, the baseline comparison may not be meaningful. Low urgency
   for a no-patch bundle, but should be resolved before any future patch cycle on this issue.

4. **Prior-art signal is strong.** `brief.md:32–40` documents two relevant commits
   (`829a8bd01d`, `dd29d9f29c`) already in the `gramps61` ancestry that addressed the
   reported failures. The no-patch outcome is consistent with the brief's own prediction
   ("likely already fixed").

---

## §4 Items not reviewable from present artifacts

- **Builder's repro run** — which partial-date strings were exercised, which locale was active,
  what `DateParser` returned — is in `build-notes.md` (withheld). The review cannot verify C2
  from artifacts alone.
- **Whether any new test was written and discarded** — the brief (`brief.md:49–53`) says to
  extend `gramps/gen/datehandler/test/dateparser_test.py` only if a live failure is found. If
  no test appears in the bundle, that is consistent with no reproduction — but cannot be
  confirmed without the build notes.

---

## §5 Non-findings

- No patch was present to review for correctness, scope creep, or security issues.
- No new `.py` files were added; POTFILES.in registration is not at issue.
- No commit message or PR description to evaluate for workflow compliance.

---

## §6 NEEDS-HUMAN clearance items

The following items must be cleared by a human before this bundle can be closed in either
direction (verify-first close **or** reopen for a patch cycle).

**§6.1 — C4 gate waiver or reopen (blocks close)**
The C4 gating failure (`check-gates.json:37–40`) must be adjudicated. The human must
determine: (a) did the builder run the `DateParser`/`DateDisplay` round-trip on
`maintenance/gramps61` for the partial-date classes (`"before May 1900"`, `"about May 1900"`,
`"estimated Jan 1847"`, `"May 1900/01"`) and find no failure? If yes, C4 is excused per
`brief.md:19–21` and the gate is waived for this bundle. If no, or if the run cannot be
confirmed, the bundle must reopen with the builder required to document and produce a verified
repro run.

**§6.2 — C2 reproduction confirmation (blocks verify-first close)**
A human must sight the builder's reproduction run log (from `build-notes.md` or equivalent)
and confirm: which locale was used, which `gramps61` HEAD was checked out, which strings were
tested, and what `DateParser` returned for each. "We ran it and nothing failed" must be
evidenced, not assumed.

**§6.3 — T5 judgment sign-off**
A human must confirm that the builder respected `brief.md:31–43` scope constraints
(English-only, partial-date path, no sweep of historical DateTest lines), and that the
prior-art commits (`829a8bd01d`, `dd29d9f29c`) were explicitly checked as covering the
reported cases.

**§6.4 — V fitness-to-purpose**
A human must sign off that routing Mantis 7084 as a verify-first close is the correct final
disposition and, if so, that the ticket is updated to reflect "confirmed resolved by
`829a8bd01d` / `dd29d9f29c`" or equivalent — not left as an indefinite open with no outcome
recorded.

**§6.5 — T3 baseline drift (advisory, non-blocking)**
Human should confirm that the T3 baseline was recorded against a commit on the
`maintenance/gramps61` lineage (not an unrelated detached HEAD) before any subsequent patch
cycle uses this baseline as a reference.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C2 — C2 Reproduction (red pre-fix) — No reproduction evidence in any artifact; `check-gates.json:8` records `"result": "none"` (not run); `build-notes.md` withheld; brief explicitly allows no-reproduction as the likely outcome (`brief.md:18`), but a human must confirm the builder ran DateParser over DateDisplay output for the partial-date classes on `maintenance/gramps61` and documented the result
- [x] T5 — T5 Judgment — No patch to judge against the brief's scope constraint; no builder reasoning visible in artifacts (`build-notes.md` withheld); human must assess whether the verify-first execution was adequate (which strings were tested, which locale, which `gramps61` HEAD) and whether the scope constraint (`brief.md:31–43`) was respected
- [x] V — Validation — fitness-to-purpose — Always-human item; no patch shipped; human must confirm that a verify-first close is the correct disposition for Mantis 7084 and that the ticket should be updated accordingly

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-21

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
