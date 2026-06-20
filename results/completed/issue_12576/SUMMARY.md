# Result — issue 12576 / ** persian-approximate-date-conversion-fabricates-day

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** Converting an **approximate** date (day unknown — day == 0, e.g. "March 2022") between calendars fabricates a **precise** day in the target calendar, so an imprecise date silently becomes a precise (and wrong) one. Reported on the Persian calendar (Mantis 12576): the reporter sees an unknown-day date turn into a specific Persian day. The maintainer noted "the approximate date now seems to be a precise date... not sure what is right."
- Success criterion: ** Converting a date whose day is unknown (day == 0) from one calendar to another **preserves the unknown day** (the converted date's day stays 0), rather than producing a specific day. Concretely: a Gregorian `Date` set to 2022/03/00 converted to the Persian calendar must keep day == 0 (today it becomes 1400/12/10).
- Repo + branch target: ** gramps (core) @ `maintenance/gramps61` — branched from `upstream/maintenance/gramps61`; forward-merged to `master` (INTEGRATION §2).
- Scope (one logical fix) / out of scope: ** Make `Date.convert_calendar` preserve a zero (unknown) day component across the conversion instead of replacing it with a fabricated value from the SDN round-trip. The one logical change is in the calendar-conversion path (`gramps/gen/lib/date.py:1843` `convert_calendar`, which does `year, month, day = Date._calendar_change[calendar](self.sortval)` and overwrites `dateval` with concrete values). / **out of scope:** the unknown-**month** mapping ambiguity (a Gregorian month spans two Persian months — flag for the human, do not try to "solve" which target month an unknown-day date belongs to); the originally-reported exact-date case (already fixed, see below); rewriting the SDN math in `gcalendar.py`.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** POSSIBLY-FIXED → verify first (original case fixed; this targets the residual approximate-date defect)
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change)
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): pass — T2 – N/A: no addons-source path in patch.diff (core-only change)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — bash: line 39:   254 Trace/breakpoint trap   (core dumped) GRAMPS_RESOURCES=. python3 -m xmlrunner discover -p "*_test.p
- T3 runtime: addon unit suites (whole-suite baseline): fail — → pip install logs (3 failure(s)): gramps-testbed-v2/test-results/install-logs/
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — Generated XML report: test-results/TEST-unittest.suite._ErrorHolder-20260605211554.xml
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 12576 / persian-approximate-date-conversion-fabricates-day

Advisory, artifact-only review. Inputs seen: `patch.diff`, `brief.md`,
`check-gates.json`. `build-notes.md` was withheld by design; every Basis below is
re-derived from the diff and the brief, not copied from the gate's own reasoning.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:10` states a concrete, falsifiable success criterion: Gregorian `2022/03/00` → Persian must keep `day == 0` (today fabricates `1400/12/10`). Load-bearing field present and unambiguous for the day component. |
| C2 — C2 Reproduction (red pre-fix) | PASS | No standalone C2 gate, but `C4-verify red-without-fix=PASS` (check-gates rows, `element:C4`) proves the regression is red without the fix; the test `date_test.py:~1804` encodes the brief's repro (`set_yr_mon_day(2022,3,0)` → `convert_calendar(CAL_PERSIAN)` → `get_day()==0`). |
| C3 — C3 Change | PASS | `patch.diff` adds the day-preservation guard exactly in the scoped path: non-compound `if self.dateval[Date._POS_DAY]==0: day=0` (~`date.py:1856`) and compound `if self.dateval[Date._POS_RDAY]==0: nday=0` (~`date.py:1867`), right after the `Date._calendar_change[...]` overwrite. No out-of-scope files touched (only `date.py`, `date_test.py`); month mapping left untouched per brief. |
| C4 — C4 Verification (red→green) | PASS | Gating gate `C4-verify` = `green-with-fix=PASS / red-without-fix=PASS` (check-gates `element:C4`, `gating:true`). Regression demonstrably fails pre-fix and passes post-fix in isolation. |
| C5 — C5 Causal adequacy | PASS | Root cause re-derived from diff: `sortval` is an SDN (always a concrete day) and `Date._calendar_change` returns a concrete day, discarding the source `dateval`'s zero marker; the guard restores `day=0` only when the source day was 0, addressing the mechanism directly rather than masking a symptom. Known-day path is left intact and pinned by `test_known_day_still_converts` (`date_test.py:~1819`). The residual month-mapping ambiguity is out of scope (see §6 / V), not a defect in this causal claim. |
| T1 — T1 Structure | N/A | Addon-layout rule (folder==id / target_version / fname / no `__init__.py`). `patch.diff` touches only core paths under `gramps/gen/lib/`; no addons-source tree in the bundle, so the rule has no surface to apply to. |
| T2 — T2 Shape | N/A | Addon coding-style rule (GPL header, no diagnostic print). Core-only change; both edited files pre-exist with headers (unchanged). Re-derived from the diff: no `print(...)`/debug statements introduced, comments are explanatory not diagnostic — so nothing the rule targets is violated even though the rule itself is addon-scoped. |
| T3 — T3 Runtime | NEEDS-HUMAN | All three whole-suite baselines are `fail`: core unit suite `Trace/breakpoint trap (core dumped)`, addon-unit `pip install` failures (3), GUI smoke error (check-gates `element:T3`, `gating:false`). These are not attributable from artifacts to a 2-line pure-Python edit in `date.py` and look like environment/baseline breakage (native crash, dependency install, headless Gtk) — a human must confirm they are pre-existing baseline noise and not a regression masked by the non-gating status. C4 ran the targeted test green in isolation, so the regression itself executes. |
| T4 — T4 Contribution | N/A | Commit-message / PR-wrapper rule. No `commit-msg.txt` or `pr-description.md` in the bundle (check-gates `element:T4`), so there is no contribution artifact to evaluate. |
| T5 — T5 Judgment | PASS | Advisory: change is minimal and tightly scoped (guard only on `day==0`), self-documents the bug-12576 rationale and the deliberate month exclusion in-comment (`patch.diff:9–12`), and ships three regression tests covering both conversion directions plus a known-day non-regression. Sound engineering judgment; final judgment remains the human's at sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Whether "preserve unknown day" is the correct product behaviour — versus the unresolved question of *which* Persian month a day-unknown Gregorian date maps to (a Gregorian month spans two Persian months; the maintainer was explicitly unsure) — is the load-bearing decision the brief flags for human confirmation (`brief.md:20–21`). The fix yields e.g. `1400/12/00`, with month `12` inherited unvalidated from the SDN round-trip. |

## §6 — Items the human must clear

1. **(V) Validation fitness-to-purpose — load-bearing.** Confirm that preserving
   `day == 0` is the intended behaviour and that inheriting the SDN-derived target
   **month** (e.g. Persian `12` for Gregorian March 2022) without validation is
   acceptable. The brief deliberately scopes the unknown-month ambiguity out
   (`brief.md:12,20–21`); the converted result is month-precise but day-unknown,
   and the maintainer was unsure what the month should be. This is the key
   behavioural sign-off.

2. **(T3) Runtime suites red.** Three non-gating whole-suite baselines fail: the
   **core unit suite core-dumped** (`Trace/breakpoint trap`), addon-unit `pip
   install` failed (3), and the GUI smoke test errored. Determine whether these are
   pre-existing baseline/environment failures (most likely, given a pure-Python
   2-line change and a native crash + dependency-install errors) or a genuine
   regression. The targeted C4 regression passed in isolation, so confirm the core
   unit suite is green on the unpatched baseline before attributing the crash to
   anything in this change.

## Notes (advisory, non-blocking)

- The fix correctly guards the **compound** (range/span) second endpoint via
  `Date._POS_RDAY`, not just the simple-date `Date._POS_DAY` — good coverage,
  though no compound-date regression test is included; the two added tests exercise
  only simple dates. Consider a range fixture if compound conversion matters.
- `test_known_day_still_converts` pins the previously-fixed exact case
  (`1400/11/30 ↔ 2022-02-19`), guarding against the guard over-firing on known days.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 — T3 Runtime — All three whole-suite baselines are `fail`: core unit suite `Trace/breakpoint trap (core dumped)`, addon-unit `pip install` failures (3), GUI smoke error (check-gates `element:T3`, `gating:false`). These are not attributable from artifacts to a 2-line pure-Python edit in `date.py` and look like environment/baseline breakage (native crash, dependency install, headless Gtk) — a human must confirm they are pre-existing baseline noise and not a regression masked by the non-gating status. C4 ran the targeted test green in isolation, so the regression itself executes.
- [x] V — Validation — fitness-to-purpose — Always-human. Whether "preserve unknown day" is the correct product behaviour — versus the unresolved question of *which* Persian month a day-unknown Gregorian date maps to (a Gregorian month spans two Persian months; the maintainer was explicitly unsure) — is the load-bearing decision the brief flags for human confirmation (`brief.md:20–21`). The fix yields e.g. `1400/12/00`, with month `12` inherited unvalidated from the SDN round-trip.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-05

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
