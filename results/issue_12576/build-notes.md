# Build notes — issue 12576 (persian approximate-date conversion fabricates day)

## Target
gramps core @ `maintenance/gramps61` (HEAD `d6a61b942f` at build time).

## Root cause
`Date.convert_calendar` (`gramps/gen/lib/date.py:1843`) converts by SDN
round-trip: it computes `year, month, day = Date._calendar_change[calendar](self.sortval)`
(`date.py:1853`). `self.sortval` is an SDN — a *specific* day — produced by
`_calc_sort_value` (`date.py:1823`), which calls `_zero_adjust_ymd`
(`date.py:1835`) and so turns an unknown day (`day == 0`) into day 1 before
computing the serial number. The reverse `_calendar_change` function
(`persian_ymd`, `gramps/gen/lib/gcalendar.py:587`) always returns a concrete day.
The result: the unknown-day marker carried on the source `dateval`
(`Date._POS_DAY`, `date.py:616`) is discarded, and an approximate date
(e.g. Gregorian 2022/03/00, "March 2022") silently becomes precise
(1400/12/10 Persian). Confirmed by direct repro against the unpatched tree:

```
greg->persian day0: (1400, 12, 10) day= 10     # bug: precise day invented
persian->greg day0: (2022, 2, 20)  day= 20     # same defect, other direction
exact:              (1400, 11, 30)              # already-fixed exact case OK
```

The brief's stated current value `(1400, 12, 10)` reproduced exactly.

## Fix
Preserve a zero day across the conversion, in `convert_calendar`
(`date.py:1853`–`1864` on the clean tree):

- After computing `year, month, day`, if `self.dateval[Date._POS_DAY] == 0`
  set `day = 0`.
- For compound dates (range/span), the second date's day is likewise restored:
  if `self.dateval[Date._POS_RDAY] == 0` set `nday = 0` before rebuilding
  `dateval`.

This guards only the **day** component. The unknown-**month** mapping
ambiguity (a Gregorian month overlaps two Persian months) is explicitly out of
scope per the brief — month is left exactly as the SDN round-trip produced it,
so behaviour there is unchanged.

Post-patch repro:

```
greg->persian day0: (1400, 12, 0) day= 0       # unknown day preserved
persian->greg day0: (2022, 2, 0)  day= 0       # both directions
exact:              (1400, 11, 30)              # exact case still correct
```

## Why this approach (alternatives ruled out)
- **Reading the zero off `dateval` rather than the SDN** — the SDN cannot carry
  "unknown day" (it is by construction a single day), so the marker must come
  from the source `dateval`. This is the minimal, local, information-preserving
  guard.
- **Rewriting `_calc_sort_value` / `gcalendar.py` SDN math** — rejected: out of
  scope, and would risk the already-merged exact-date fix (`d627d5648a`,
  PR gramps#1351). `gcalendar.py:589`'s commented `# related to bug 12576` line
  is left untouched per the brief.
- **Skipping conversion entirely when day == 0** — rejected: the year and month
  still need converting (March 2022 → an appropriate Persian year/month); only
  the *day* must stay unknown.

## Test
`gramps/gen/lib/test/date_test.py` — new `ConvertCalendarUnknownDayTest`
(`BaseDateTest` subclass, appended before the `__main__` block). Three cases:
- Gregorian→Persian with day 0 → `get_day() == 0` (the brief's headline case),
- Persian→Gregorian with day 0 → `get_day() == 0` (the symmetric case),
- exact 2022-02-19 → 1400/11/30 guard, so the fix doesn't regress precise dates.
Pure / headless (no Gtk).

## Verification status
- **Red→green proven via the public `Date` API** (the exact assertions the test
  makes): buggy `(1400, 12, 10)`/day-20 on the unpatched tree → `day == 0` both
  directions with `patch.diff` applied, exact case unchanged (outputs above).
- **Patch applies cleanly** to the clean `maintenance/gramps61` checkout
  (`git apply --check` OK).
- The engine C4-verify gate (`run-verify.sh`) and the full unittest run could
  **not** be executed in this build sandbox: the in-container `pip install` (and
  the full `gramps` import's config-dir writes) require network/escalation that
  is gated behind human approval here. The authoritative red→green check is
  Check's C4-verify gate, which runs the unittest in the proper container with
  display + D-Bus + AT-SPI — it will exercise the test class directly.
