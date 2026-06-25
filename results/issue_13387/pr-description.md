## Root cause

`Date.get_start_stop_range()` applies the ±"about" padding (default 50 years) whenever `quality == QUAL_ESTIMATED`, but this incorrectly applies to compound dates with explicit bounds (MOD_RANGE / MOD_SPAN — e.g. "estimated between 1968 and 1978"). The explicit bounds are then widened, causing the Age Calculator to report absurd age spans; an explicit "between" should define its own range without approximation padding.

## Fix

Condition the estimated-quality padding on `not self.is_compound()` at gramps/gen/lib/date.py:998 so that the ±"about" window applies only to non-compound estimated dates. Compound estimated dates (RANGE/SPAN) now return their explicit bounds verbatim, while single estimated dates (MOD_NONE) retain the padding behavior.

## Verified against

- gramps/gen/lib/date.py:998 (the condition guarding the ±"about" padding branch, modified to add `and not self.is_compound()`)
- gramps/gen/lib/date.py:1955–1959 (the `is_compound()` method that checks MOD_RANGE/MOD_SPAN)
- gramps/gen/lib/test/date_test.py:1708+ (EstimatedCompoundRangeTest class with three regression tests)

## Test

EstimatedCompoundRangeTest (gramps/gen/lib/test/date_test.py:1708+) — three cases:
- `test_estimated_range_keeps_explicit_bounds`: estimated MOD_RANGE 1968–1978 returns (1968-01-01, 1978-12-31) with no padding
- `test_estimated_span_keeps_explicit_bounds`: estimated MOD_SPAN 1968–1978 returns (1968-01-01, 1978-12-31) with no padding  
- `test_single_estimated_date_still_padded`: single estimated date 1973 is still padded by behavior.date-about-range (verifies existing behavior is preserved)

Verified locally: pre-fix compound tests fail with over-padded bounds; post-fix all three pass and single-estimated still receives padding as before.

Fixes #13387
