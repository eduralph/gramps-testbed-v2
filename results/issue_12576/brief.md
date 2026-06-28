# Brief — issue 12576 / persian-calendar-leap-day-conversion

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** persian-calendar-leap-day-conversion
- **Defect:** Converting a valid Persian (Jalali) calendar date through Gramps's SDN
  conversion is wrong at the leap-year boundary. `persian_ymd(persian_sdn(1400, 12, 30))`
  returns `(1401, 1, 1)` instead of `(1400, 12, 30)` — 1400 is a Persian leap year, so
  Esfand (month 12) has 30 days and that date is valid. The reporter's example
  (Persian 1400/11/30 ≡ 2022-02-19) and other leap-boundary dates are misinterpreted.
- **Success criterion:** For valid Persian leap-year dates — at minimum month 12 day 30
  of a leap year (e.g. 1400) — round-tripping through `persian_sdn` → `persian_ymd`
  returns the identical `(year, month, day)`. Demonstrable by a unit test on
  `gramps/gen/lib/gcalendar.py` that is red pre-fix and green post-fix (pure-function
  C4-verify; no GUI, no whole-suite dependency).
- **Invariant to restore:** Calendar↔SDN conversion is a lossless bijection over valid
  dates: `persian_ymd(persian_sdn(y, m, d)) == (y, m, d)` for every valid Persian date.
  (Internal Gramps calendar-correctness invariant — Tier C, no external canon. Rationale:
  the Serial Day Number is a canonical absolute day index, so encoding a valid date to it
  and decoding back MUST be the identity; a divergence is by definition a conversion bug.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low — the defect is contained to the leaf conversion helpers in one
  file (`gcalendar.py`); these functions have no cross-file call ripple and no GUI reach.
- **Scope:** the incorrect Persian→SDN→Persian round-trip at the leap-year boundary in
  `gramps/gen/lib/gcalendar.py` (`persian_sdn` / `persian_ymd`; note the dormant
  `# ...related to bug 12576` comment block already in `persian_ymd`). / out of scope:
  the other calendars (Gregorian/Julian/Hebrew/French/Islamic), the `Date` class, date
  parsing, and date display/formatting.
- **Repro instruction:** with gramps on the path —
  `from gramps.gen.lib.gcalendar import persian_sdn, persian_ymd` then
  `persian_ymd(persian_sdn(1400, 12, 30))` → yields `(1401, 1, 1)` (wrong; must be
  `(1400, 12, 30)`). A loop over month/day of leap year 1400 surfaces the boundary case.
- **Test file:** gramps/gen/lib/test/gcalendar_test.py (new core test, `*_test.py`
  suffix; run via `run-unit.sh` discovery). The test MUST call the production
  `persian_sdn`/`persian_ymd` directly — no reimplementation of the arithmetic.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds `gramps/gen/lib/test/gcalendar_test.py` → register in
  `po/POTFILES.skip` (test module, no translatable strings).
- **Prior-art check (triage cycles):** searched by path `gramps/gen/lib/gcalendar.py`
  across `upstream/maintenance/gramps61` + `master` merged history — only black/license/
  pylint reformat commits touch it; no functional Persian-conversion fix, and the
  bug-12576 comment is still present. No matching open/closed fork PR by this path. →
  unfixed; fix is necessary.
- **Mantis:** 12576
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
