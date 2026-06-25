# Brief — issue 13387 / date-estimated-range-overpadded-by-about-limit

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** date-estimated-range-overpadded-by-about-limit
- **Defect:** `Date.get_start_stop_range()` (gramps/gen/lib/date.py:998–1001) applies the
  ±"about" preference window (`behavior.date-about-range`, default 50 years) whenever
  `self.quality == Date.QUAL_ESTIMATED`, even for a *compound* date that already carries
  explicit bounds (MOD_RANGE / MOD_SPAN — e.g. "estimated between 1968 and 1978"). The
  explicit bounds are then widened by ±50 years, so the Age Calculator reports an absurd
  span (the report's example: "between 19 years and 94 years" for a person born 1936
  with an event "estimated between 1968 and 1978"). An explicit "between" should override
  the Preferences "about" limit.
- **Success criterion:** For an estimated *compound* date (quality = Estimated,
  modifier = RANGE or SPAN, e.g. 1968–1978), `get_start_stop_range()` returns the
  explicit start/stop bounds WITHOUT adding the about-range padding; a single estimated
  date with no explicit range still receives the about-range padding as before.
  Demonstrable by C4-verify against gramps/gen/lib/test/date_test.py.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md
  §1.1). (Correctness requirement: an explicitly bounded compound date defines its own
  range; the approximation window applies only when the bounds are not explicit.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium — a single function, but `get_start_stop_range()` feeds age
  calculation, date sorting, and place/date matching, so the reviewer must hold those
  consumers in view to confirm no regression to single-estimated / ABOUT / BEFORE /
  AFTER behaviour.
- **Scope:** the about-range padding in `get_start_stop_range()` must not widen a date
  that already has explicit compound (range/span) bounds — an explicit "between"
  overrides the Preferences "about" window. / out of scope: the BEFORE / AFTER /
  single-ABOUT padding paths; the default preference values; keeping the 'Estimated'
  quality flag itself (the report explicitly says pinning 'Estimated' on the result is
  still worthwhile — do not drop it); date display/formatting.
- **Repro instruction:** Build a Date and call
  `set(quality=Date.QUAL_ESTIMATED, modifier=Date.MOD_RANGE, value=(0,0,1968,False, 0,0,1978,False))`,
  then `get_start_stop_range()`. Pre-fix it returns padded bounds (≈1918 … ≈2028);
  post-fix it returns (1968-01-01 … 1978-12-31). (Manual GUI repro: an event dated
  "estimated between 1968 and 1978" shows a sane age, not "between 19 and 94 years".)
- **Test file:** gramps/gen/lib/test/date_test.py — must fail pre-fix (padded span) and
  pass post-fix (explicit span). The test calls the production `get_start_stop_range()`
  directly (principles.md §3.4).
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none (extends existing date_test.py).
- **Prior-art check (triage cycles):** searched gramps/gen/lib/date.py history on
  upstream/maintenance/gramps61 (pinned worktree) — the
  `MOD_ABOUT or QUAL_ESTIMATED` padding branch is present and unconditioned on
  compound-ness; no merged/open/closed PR found for this path. Not previously fixed.
- **Mantis:** 13387
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
