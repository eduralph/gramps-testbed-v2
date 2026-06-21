# Build notes — issue 7084 / dateparser-partial-date-modifier-roundtrip

## Disposition: VERIFY-FIRST CLOSE — defect does NOT reproduce on maintenance/gramps61.
No production patch, no regression test. Routes to §6 NEEDS-HUMAN per the brief's
conditional Success criterion. The brief mandates this outcome on non-reproduction and
explicitly forbids manufacturing a change to satisfy the gate.

---

## Independent re-run THIS Do beat (2026-06-21) — run, not recalled

I did not accept the prior conclusion on recall. I re-ran the reproduction from scratch this
beat against the `/home/eddie/workspace/gramps-6.1` worktree:

- `git -C gramps-6.1 log --oneline -1` = `b679c084f6`
- `git -C gramps-6.1 rev-parse upstream/maintenance/gramps61` = `b679c084f6…`
  → **HEAD == target-branch tip**.
- `git -C gramps-6.1 status -s gramps/gen/datehandler/ gramps/gen/lib/date.py` = empty
  → **pristine code under test** (no local edit).

The repro drives the **production** `GrampsLocale(lang="en_GB").date_parser` /
`.date_displayer` — the same objects the DateTest tool and the app use, no re-implementation —
under `LC_ALL=en_GB.utf8`. The `gramps.gen.datehandler` parser/displayer are pure-`gen`
(no `gi`/GUI import), so the round-trip runs headless under plain `python3`. It applies BOTH
the DateTest tool's own fail criterion (`src.mod != MOD_TEXTONLY and parsed.mod ==
MOD_TEXTONLY`) AND a stricter EQUAL-Date compare (modifier, quality, year, month). Verbatim:

> **This-beat span-inclusive re-confirmation (2026-06-21).** I extended the partial-date
> sweep to also cover the open-span / range modifiers (`MOD_FROM`, `MOD_TO`, `MOD_RANGE`,
> `MOD_SPAN`) that landed via `70520be80c` "Add support for open spans" — 132 partial-date
> cases (month+year, no day) × 6 display formats = **792** display→re-parse round-trips under
> `en_GB.utf-8`, **0 failures, 0 `MOD_TEXTONLY`**. Covers single dates (NONE/BEFORE/AFTER/
> ABOUT) and spans (RANGE/SPAN with every slash1×slash2 combination), all qualities. The
> consolidated script is the bundle's `verify_partial_roundtrip.py`.

```
=== literal strings ===
before May 1900           mod=1 qual=0 ymd=(1900, 5, 0) TEXTONLY=False
after May 1900            mod=2 qual=0 ymd=(1900, 5, 0) TEXTONLY=False
about May 1900            mod=3 qual=0 ymd=(1900, 5, 0) TEXTONLY=False
estimated Jan 1847        mod=0 qual=1 ymd=(1847, 1, 0) TEXTONLY=False
calculated Jan 1847       mod=0 qual=2 ymd=(1847, 1, 0) TEXTONLY=False
May 1900                  mod=0 qual=0 ymd=(1900, 5, 0) TEXTONLY=False
Jan 1847                  mod=0 qual=0 ymd=(1847, 1, 0) TEXTONLY=False
May 1900/01               mod=0 qual=0 ymd=(1901, 5, 0) TEXTONLY=False
before May 1900/01        mod=1 qual=0 ymd=(1901, 5, 0) TEXTONLY=False
before May 1945           mod=1 qual=0 ymd=(1945, 5, 0) TEXTONLY=False
literal TEXTONLY failures: 0
category sweep: checked=3456 tool_fail=0 strict_fail=0
```

The partial-date category sweep = 6 displayer formats × 2 calendars × 3 qualities ×
{MOD_NONE,BEFORE,AFTER,ABOUT} × {plain, dual-year slash} × months 1–12 = **3456** display→
re-parse round-trips, with **0 tool failures and 0 strict-equal failures**. All 10
reporter-class literals (incl. note ~0033xxx's own "before May 1945") parse to a proper `Date`
with the right modifier, quality, month, year and **0 `MOD_TEXTONLY`**. The defect does
**not** reproduce on maintenance/gramps61.

This matches every prior Do beat's figures (earlier runs swept 432, 444, 1296, 1728, 3456,
5184 cases — all 0 failures, the gate-image container run included). The conclusion is stable
and independently re-confirmed this beat.

---

## What I verified (target branch: gramps-project/gramps @ maintenance/gramps61)

Production path under test:
- `gramps/gen/datehandler/_dateparser.py` — `DateParser` (English; the brief's Scope).
- `gramps/gen/datehandler/_datedisplay.py` — `DateDisplay.display_formatted`, all 6 formats
  (`_datedisplay.py:835` `DateDisplayEn`, `:843` `DateDisplayGB`; base `DateDisplay` at
  `_datedisplay.py:66`). The English/GB displayers emit the reporter's textual-month strings.
- `gramps/gen/lib/date.py` — `Date.MOD_TEXTONLY` is the failure sentinel; the DateTest tool
  flags a fail when `dateval.modifier != MOD_TEXTONLY and ndate.modifier == MOD_TEXTONLY`
  (`gramps/plugins/tool/dateparserdisplaytest.py`).

Every partial-date class the reporter named — month+year with a modifier, with a quality,
with a dual-year slash — round-trips to an equal `Date` (right month, year, modifier, quality)
across all six display formats. The invariant the brief asks to restore is **already intact**
on gramps61.

## Root cause of the non-reproduction (two sentences)

The 2013 report drove a developer-only tool against a then-buggy English parser; the specific
partial-date + modifier/quality/slash failures were subsequently fixed in the gramps61
ancestry. The relevant landed commits on `gramps/gen/datehandler/_dateparser.py`
(`git -C gramps-6.1 log --oneline -- gramps/gen/datehandler/_dateparser.py`) are
`829a8bd01d` "DateParserEN failures under the DateTest tool" (slash/double-dated cases),
`dd29d9f29c` "Fix datehandlers for round trip", `30a58130a5` "Date input: allow yyyy-mm for
iso format", and `70520be80c` "Add support for open spans" — all present in the target
branch's history; recent commits on the file are black/mypy/GPL reformat only.

## Why no patch / no test

- **Brief mandate.** The Success criterion routes a non-reproduction to §6 and forbids
  manufacturing a change. There is no live divergence to fix and nothing to assert red→green:
  a regression test would be **green on the unmodified tree** (no red leg), which is not a
  valid C4 red→green proof and would only encode behaviour that already holds — scaffolding,
  not a fix.
- **Test file.** The brief names `gramps/gen/datehandler/test/dateparser_test.py` to extend
  *only if* a live failure is found. None was, so it is left untouched (clean git status).
- **POTFILES.** No `.py` added or removed → `T2-potfiles` is N/A.
- **C4-verify.** With no `patch.diff`, the red→green mechanic has nothing to revert — the
  `PDCA-UNVERIFIABLE` / §6 NEEDS-HUMAN path (INTEGRATION §3) applies. This is a verify-first
  close, not a verifiable fix.

## Test-coverage gap I found (context for the human, NOT shipped this beat)

The existing round-trip suite `gramps/gen/datehandler/test/datehandler_test.py::test_simple`
(`datehandler_test.py:90`) iterates `for day in (5, 27)` (`datehandler_test.py:111`) — it
**never exercises the partial (day=0) month+year case** that is this ticket's whole subject.
So although the production code round-trips partial dates correctly (proven above), there is
no *automated* assertion guarding that property; that absence is plausibly why the ticket was
left open for "others with different results". This is a coverage observation, not a defect.
Per the brief's conditional Success criterion (ship a test **only if** a live failure is
found — none was), I do **not** ship a test this beat: a `day=0` round-trip case added now
would pass on the unmodified tree (no red leg), so it is not a C4 red→green regression test
and the brief forbids manufacturing a change. If the maintainer wants the partial-date
property locked in, the clean follow-up is a separate *coverage* item adding `0` to the
`test_simple` day loop (a ~1-line change, judged on its own as test-hardening, not as a fix
for 7084) — flagged here so the human can decide at sign-off.

## For the human at §6 sign-off

- The non-reproduction matches the brief's stated likely outcome and the maintainer's 2017
  finding (paulfranklin on `829a8bd01d` could not reproduce the `"before May …"` failures and
  left the ticket open "in case others have different results").
- **Disposition marker shipped this beat:** `close-disposition` = `not-reproducible` (the Do
  artifact standing in for `patch.diff` on the no-fix close path, state.py:53). Prior Do beats
  wrote build-notes but never the marker, so the bundle stayed at PLANNED and kept re-running
  Do; writing it advances the bundle to Check (gates N/A — close disposition) and on to §6.
- Suggested Mantis disposition: **resolved / no-change-needed on 6.1** — partial-date
  display→parse round-trips for all reporter classes; cite the four ancestry commits above.
- Reproduction is re-runnable from the bundle against a `gramps-6.1` checkout (set
  `PYTHONPATH`/`GRAMPS_RESOURCES` to the checkout, `LC_ALL=en_GB.utf8`). Every repro script
  drives the production parser/displayer (no re-implementation) and needs only `gramps.gen` on
  the path — no GUI, no DB. The consolidated headline run this beat is
  `verify_partial_roundtrip.py` (792 partial-date + span round-trips across all 6 formats,
  0 failures, 0 `MOD_TEXTONLY`). Earlier beats' wider sweeps are retained for the audit trail:
  `repro_verify_thisbeat.py` (3456 cases, 0 tool-fail + 0 strict-fail),
  `repro_container_reconfirm.py` (run in `gramps-testbed:ubuntu-6.1.0`, the gate image, 1296
  cases, 0 fails), `repro_strict_equal_partial.py` (slash-aware EQUAL-Date sweep, 5184 cases,
  0 strict-fails), `repro_faithful_datetest_tool.py` (faithful replica of
  `dateparserdisplaytest.py`'s exact date generation, all 6 formats — 0 tool failures).

## Alternatives considered and rejected

- **Ship a green-on-clean round-trip test anyway** (as a guard). Rejected: it has no red leg
  (C4 cannot prove red→green; `run-verify` would have no production file to revert), and it
  encodes already-holding behaviour — the brief explicitly forbids manufacturing a change to
  satisfy the gate. Concretely it would add ~30 lines to `dateparser_test.py` that pass before
  and after with **zero** diff to production, i.e. pure scaffolding.
- **Touch `_dateparser.py` to "harden" the partial path.** Rejected: no confirmed live
  divergence; the Invariant-to-restore is already satisfied, so the smallest change that
  restores it is the empty change. Any edit would be a behaviour change with no failing case
  behind it — forbidden by the brief and by principles §1.2/§2 (smallest change that restores
  the invariant; here that is none).
