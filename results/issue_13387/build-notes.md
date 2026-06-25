# Build notes — issue 13387

## Root cause

`Date.get_start_stop_range()` at `gramps/gen/lib/date.py:998` (maintenance/gramps61)
gates the ±"about" padding on:

```python
elif self.modifier == Date.MOD_ABOUT or self.quality == Date.QUAL_ESTIMATED:
```

The `self.quality == Date.QUAL_ESTIMATED` disjunct fires for *any* estimated date,
including a compound RANGE/SPAN date that already carries explicit bounds (e.g.
"estimated between 1968 and 1978"). The explicit start/stop are then widened by
±`behavior.date-about-range` (default 50y), so the Age Calculator reports an absurd
span. An explicit "between" should define its own range; the approximation window
only makes sense when the bounds are *not* explicit.

## Fix

`gramps/gen/lib/date.py:998` — add `and not self.is_compound()` to the estimated
disjunct:

```python
elif self.modifier == Date.MOD_ABOUT or (
    self.quality == Date.QUAL_ESTIMATED and not self.is_compound()
):
```

`is_compound()` is `self.modifier in [Date.MOD_RANGE, Date.MOD_SPAN]`
(`date.py:1955-1959`). MOD_ABOUT is never compound, so the first disjunct is
unaffected. This is the smallest change that restores the correctness requirement
(brief "Invariant to restore" note): an explicitly bounded compound date defines its
own range; the about-window applies only when the bounds are not explicit.

The 'Estimated' quality flag itself is *not* dropped (brief scope says keep it) — the
patch only changes the padding branch, not how the result's quality is set elsewhere.

## Why not other approaches

- **Drop the `QUAL_ESTIMATED` disjunct entirely** — rejected: it would stop padding a
  *single* estimated date (modifier MOD_NONE), which the brief keeps in scope as
  correct existing behaviour. The `test_single_estimated_date_still_padded` test pins
  that.
- **Guard at the call site (Age Calculator)** — rejected: `get_start_stop_range()`
  also feeds date sorting and place/date matching (`match_exact` at `date.py:1016`,
  brief "Difficulty"/consumers). Fixing one caller leaves the wrong range for the
  others. The cause is in the one function; fix it there.

## Scope confirmation (consumers held in view)

- BEFORE/AFTER/FROM/TO branches (`date.py:988-997`) — untouched.
- single-ABOUT padding (`MOD_ABOUT` disjunct) — untouched; MOD_ABOUT is not compound.
- single estimated (MOD_NONE + QUAL_ESTIMATED) — still padded (guarded by test).
- `match_exact`/`match` rely on `get_start_stop_range()` for compound dates: a tighter
  (un-padded) explicit range is the *correct* range for those comparisons too.

## Test

`gramps/gen/lib/test/date_test.py` — new `EstimatedCompoundRangeTest` after
`Test_set2` (insertion at line 1708). Calls the production `get_start_stop_range()`
directly (principles §3.4). Three cases:
- estimated MOD_RANGE 1968–1978 → (1968,1,1)…(1978,12,31), no padding.
- estimated MOD_SPAN 1968–1978 → same.
- single estimated 1973 → still padded by `config.get("behavior.date-about-range")`
  (read from config so the assertion is robust to the env's default, which is 10 in
  the test container, 50 in normal prefs).

Import-light: `date_test.py` imports only `gramps.gen.lib.date` /
`gramps.gen.datehandler` (no `gi` / `gramps.gui`), so it runs under the headless C4
core runner.

## Verification (red→green)

The docker-backed `run-verify.sh` could not be invoked in this session (docker calls
require an approval not available headless). Confirmed the contract locally against the
maintenance/gramps61 worktree (`/home/eddie/workspace/gramps-6.1`, detached at upstream
HEAD `b679c084f6`) with plain `python3 -m unittest`:

- Fix applied → all 3 tests pass (GREEN).
- Production revert, test kept → the two compound tests FAIL
  (`(1958,1,1) != (1968,1,1)`); the single-estimated guard still passes (RED).

This matches the C4 red-without-fix / green-with-fix mechanic. Worktree left clean for
the date files afterward.

## Formatting / commit-readiness

Ran `python3 -m black` on both touched files — "2 files left unchanged" (already
conforms to the target's black config). No new/removed `.py` files, so no
`po/POTFILES.in` / `.skip` change is needed (brief "New/removed files: none").
