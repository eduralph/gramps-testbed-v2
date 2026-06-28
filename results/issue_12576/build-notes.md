# Build notes — issue 12576 / persian-calendar-leap-day-conversion

**Disposition: NO PATCH — verify-first close (`manual-verification`).** The brief's
Success criterion cannot be satisfied without *corrupting* the calendar, because its
governing premise is factually wrong: **Persian year 1400 is NOT a leap year.** The
round-trip invariant the brief asks me to "restore" **already holds** for every valid
Persian date on `maintenance/gramps61` — I verified it over 3000 years and >1 million
contiguous Serial Day Numbers with zero failures. The brief's headline example
`persian_ymd(persian_sdn(1400, 12, 30)) == (1400, 12, 30)` is asking for the round-trip
of an **invalid date** (Esfand 30 of a common year does not exist); the current code
*correctly* normalises it to `(1401, 1, 1)`. There is nothing to fix, and the demanded
fix would be a regression.

Per STOP/diagnose discipline I am surfacing this as a brief defect rather than
fabricating a patch that makes an invalid date "valid".

All citations below are on `maintenance/gramps61` (worktree `/home/eddie/workspace/gramps-6.1`,
HEAD `cbe5699b2e`, last touched gcalendar.py = `b3a5cf346f`).

---

## The code in question

- `gramps/gen/lib/gcalendar.py:567-584` — `persian_sdn(year, month, day)` (Persian → SDN).
- `gramps/gen/lib/gcalendar.py:587-612` — `persian_ymd(sdn)` (SDN → Persian).
- `gramps/gen/lib/gcalendar.py:589-590` — the dormant, commented-out
  `# sdn = math.floor(sdn) + 0.5` line the brief flags ("related to bug 12576").
- `gramps/gen/lib/gcalendar.py:108` — `_PRS_EPOCH = 1948320.5`.

This is the Fourmilab/Behrooz *arithmetic* Persian calendar (the 2820-year cycle /
`682/2816` leap rule). Its leap-year determination agrees with the standard 33-year
cycle around the dates in question.

## What the brief claims vs. what is true

Brief (lines 9-23): "1400 is a Persian leap year, so Esfand (month 12) has 30 days and
that date is valid", and asserts `persian_ymd(persian_sdn(1400,12,30))` *should* return
`(1400,12,30)`.

**1400 is a common (non-leap) year.** Three independent authorities agree:

1. **The algorithm's own arithmetic.** Year length `persian_sdn(y+1,1,1) - persian_sdn(y,1,1)`:
   1399 → 366 days (leap), **1400 → 365 days (common)**, 1401/1402 → 365, 1403 → 366.
2. **The standard 33-year cycle** leap rule (`y % 33 ∈ {1,5,9,13,17,22,26,30}`):
   `1400 % 33 = 14` → common. 1399 → leap. (Algorithm and cycle agree for 1390–1402;
   they first diverge at 1403/1404, far from the brief's example.)
3. **The astronomical reality** (what Iran officially uses). Nowruz 1400 = 2021-03-21,
   Nowruz 1401 = 2022-03-21 → exactly **365 days** → year 1400 is common → Esfand 1400
   has 29 days → **there is no 1400/12/30.**

The reporter's *own anchor date* confirms it and confirms the current code is correct:
the reporter (note ~0063701 in `notes.json`) states **Persian 1400/11/30 (Bahman 30) ≡
Gregorian 2022-02-19.** On the current `maintenance/gramps61` code:

```
persian_sdn(1400,11,30) → gregorian_ymd → (2022, 2, 19)   ✓ matches reporter
gregorian_sdn(2022,2,19) → persian_ymd  → (1400, 11, 30)  ✓ exact round-trip
persian_sdn(1400,12,29) → gregorian_ymd → (2022, 3, 20)   ← last day of Esfand 1400
persian_sdn(1401,1,1)   → gregorian_ymd → (2022, 3, 21)   ← Nowruz 1401, the next day
```

Esfand 1400 ends on day **29** (2022-03-20); the next day is Nowruz 1401. So
`persian_sdn(1400,12,30)` encodes a day that, decoded, is `(1401,1,1)` — the algorithm
is self-consistent and astronomically correct.

## The invariant the brief wants is already satisfied

Invariant (brief lines 19-23): `persian_ymd(persian_sdn(y,m,d)) == (y,m,d)` for **every
valid Persian date**. I exhaustively checked this on the current code:

- **Every valid date, years 1..3000** (Esfand = 30 days only in the algorithm's leap
  years, 29 otherwise): **0 round-trip failures.**
- **Contiguous SDN bijection** over `persian_sdn(1,1,1) .. persian_sdn(3000,1,1)` =
  1,095,361 days: every SDN decodes to a date that re-encodes to the same SDN — **0
  failures.** A bijection is exactly the invariant's "lossless" requirement.

The only inputs that do *not* round-trip to themselves are **invalid** dates such as
`(Y,12,30)` for a common year Y (e.g. 1400) — and normalising an out-of-range day into
the following month/year is the correct, expected behaviour of a calendar decoder, not
a defect. The invariant is scoped to *valid* dates and it holds.

So the genuinely-valid leap-day case the brief *meant* to protect already works:
`persian_ymd(persian_sdn(1399,12,30)) == (1399,12,30)` (1399 IS leap), and likewise for
1391, 1395, 1408, 1412, 1416, …

## Why the reporter's tracker thread does not imply a gcalendar.py bug here

- The reporter's GUI symptoms ("won't let me save 1400 Bahman 30", "shows 1400/12/00")
  were *date-editor validation* issues — **explicitly out of scope** per the brief
  (lines 30-32) — and were addressed upstream (master `d627d564`, "Fix invalid Persian
  calendar dates", in this branch's history). The reporter's later "still happens in
  5.2.2 / 6.0.6" comments are about that editor layer, not the SDN conversion math.
- The dormant `# sdn = math.floor(sdn) + 0.5` line (gcalendar.py:589-590) is the
  half-day-noon normalisation from the original JD-based Fourmilab algorithm.
  **Re-enabling it makes things strictly worse**, because Gramps' `persian_sdn` already
  collapses the JD to an integer SDN via `int(math.ceil(... + _PRS_EPOCH - 1))`
  (gcalendar.py:584); adding `+0.5` then shifts decoding by a day. I measured it: over
  years 1300–1500 the dormant-line-enabled variant produces **2452** round-trip
  failures vs **151** for the current code (and all 151 of *those* are invalid
  `(Y,12,30)` common-year inputs, i.e. not real failures). The dormant line must stay
  dormant; it is correctly commented out.

## What I did NOT do, and why

- **I did not write `gramps/gen/lib/test/gcalendar_test.py` as a red→green test.** The
  brief's named assertion (`… == (1400,12,30)`) is red on the current code *because the
  code is right* and would only go green by making the code wrong. A red→green test here
  would be a test of a regression. (A green-only guard encoding the *correct* invariant
  — valid dates round-trip, 1400/12/30 normalises to 1401/1/1 — is writable and passes
  today, but that is a green→green regression guard, not the brief's deliverable, and a
  no-fix close ships no target-repo edit. The verification commands below stand in for
  it and are trivially re-runnable.)
- **I did not ship a `patch.diff`.** There is no correct code change. `publish.py:117-126`
  treats a missing / empty patch.diff as a no-fix close and returns 0, so this does not
  break `pdca publish`.
- **No `po/POTFILES.*` change** — no `.py` file added or removed.

## How to reproduce my verification (no GUI, pure functions)

Load gcalendar.py in isolation (it imports only `math`, so this is headless-safe and
does not pull in `gi`/`gramps.gui`):

```python
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gcal", "gramps/gen/lib/gcalendar.py")
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def algo_leap(y):            # the algorithm's own leap rule
    return g.persian_sdn(y+1,1,1) - g.persian_sdn(y,1,1) == 366

# 1) every VALID date round-trips (Esfand=30 only when leap):
for y in range(1, 3001):
    for m in range(1, 13):
        maxd = 31 if m <= 6 else (30 if (m <= 11 or algo_leap(y)) else 29)
        for d in range(1, maxd+1):
            assert g.persian_ymd(g.persian_sdn(y,m,d)) == (y,m,d), (y,m,d)
# 2) 1400 is common; its "Esfand 30" is invalid and normalises forward:
assert not algo_leap(1400) and algo_leap(1399)
assert g.persian_ymd(g.persian_sdn(1400,12,30)) == (1401,1,1)
assert g.persian_ymd(g.persian_sdn(1399,12,30)) == (1399,12,30)
# 3) reporter's anchor matches the current code:
assert g.gregorian_ymd(g.persian_sdn(1400,11,30)) == (2022,2,19)
assert g.persian_ymd(g.gregorian_sdn(2022,2,19)) == (1400,11,30)
print("all assertions pass — conversion is correct, no fix warranted")
```

## Recommendation to the human (sign-off)

Close 12576 against `maintenance/gramps61` as **not-a-defect / already-correct** for the
`gcalendar.py` conversion layer. If the *tracker item* is to be kept open, it should be
**re-scoped** to the date-editor validation behaviour (out of scope for this brief), not
to `persian_sdn`/`persian_ymd`. The brief should be corrected: its example must use a
genuine leap year (e.g. **1399**/12/30), and its claim that "1400 is a Persian leap year"
is incorrect.

## Files in this bundle

- `build-notes.md` — this rationale (withheld from the reviewer).
- `close-disposition` — `manual-verification` (routes the close call to the human).
- (no `patch.diff`, no test, no POTFILES change — no defect to fix.)
