# PR description

## Root cause

The Top Surnames gramplet assigned a representative for every group name from a person's primary and alternate names, without preferring primary-name carriers. When the Same Surnames quick view re-derived the clicked surname from the representative's *primary* name, surnames held only as alternates would resolve to a different person's primary surname. For the reported scenario (person P1 with primary "A" + alternate "B", person P2 with primary "B"), clicking "B" opened the report for surname "A" instead.

## Fix

This is a test-only patch that adds a regression test for the reported scenario. The underlying production bug was already fixed by commit e39dc09e2e, which modified `record_surnames()` to only assign or rewrite the representative when the surname matches the person's primary name or when no representative has been chosen yet. This ensures primary-name carriers always win, making the result independent of database iteration order.

## Verified against

- `gramps/plugins/gramplet/topsurnamesgramplet.py:54-78` — the `record_surnames()` function that was fixed to prefer primary-name carriers (commit e39dc09e2e)
- `gramps/plugins/gramplet/test/topsurnamesgramplet_test.py` — existing test suite for surname tally; the new test extends this module with a case modeling the exact reported scenario

## Test

Added `test_reported_repro_6826_clicked_surname_resolves_to_primary_carrier` (topsurnamesgramplet_test.py:154-186), which models the reported defect (P1 primary "A" + alternate "B", P2 primary "B") and verifies:
- The representative for surname "B" is P2 (the primary-B carrier), not P1 (the alternate-name carrier)
- This holds true for *both* database iteration orders, confirming the fix's order-independence
- The surname counts are correct (B counted twice, A once)

The test imports `record_surnames` directly from the production module (no mocking), confirming the fix is stable against future refactors. It runs headless (only `gramps.gen.*` dependencies, no GTK/GUI), enabling deterministic CI verification.

Fixes #6826
