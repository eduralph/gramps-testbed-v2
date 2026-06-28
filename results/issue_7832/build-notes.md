# Build notes — issue 7832 / get-age-dateless-birth-masks-dated-fallback

## Root cause (verified on target b679c084f6, maintenance/gramps61)

`get_age` (gramps/gen/utils/db.py:95) delegates birth/death event selection to
`get_birth_or_fallback`/`get_death_or_fallback`. Those return the *primary* Birth/Death
event the moment one exists (db.py:58-62 / 79-83 on the unpatched tree), **regardless of
whether it carries a usable date**. So a person with a dateless (place-only) primary
Birth event never reaches the dated baptism fallback (db.py:64-70 unpatched), and
`get_age` then computes nothing — the `birth_date.get_valid() and not is_empty()` guard
(db.py:120-122) is false and `age` stays `None`. Fan Chart colouring (fanchartview,
which calls `get_age`) and every other age consumer loses the value.

## Fix

Add an opt-in `require_date=False` parameter to `get_birth_or_fallback` and
`get_death_or_fallback`, plus a shared `_has_usable_date(event)` helper that applies the
exact same validity test `get_age` already uses (`date.get_valid() and not
date.is_empty()`). When `require_date=True`:
- a primary event without a usable date is skipped instead of returned, and
- a fallback event without a usable date is skipped (the loop `continue`s) so the search
  can keep looking for a dated one.

`get_age`'s fallback branch (db.py:108-110) now calls both with `require_date=True`.

Patched lines (target paths, post-fix file):
- gramps/gen/utils/db.py:53-62 — new `_has_usable_date` helper.
- gramps/gen/utils/db.py:65-93 — `get_birth_or_fallback` gains `require_date`, primary
  guard + fallback `continue`.
- gramps/gen/utils/db.py:96-124 — `get_death_or_fallback` gains the same.
- gramps/gen/utils/db.py:138-139 — `get_age` passes `require_date=True`.
- po/POTFILES.skip — registers the new test (matches the existing `*_test.py` entries).

## Why this shape and not the alternatives

- **Why not change `get_birth_or_fallback`'s *default* behaviour to require a date?**
  Explicitly out of scope (brief Scope): non-age callers legitimately want the dateless
  primary event — e.g. displaying a birth *place* when only a place is recorded
  (`gramps/gen/utils/db.py:get_birth_or_fallback` is called from many such sites). A
  default change would silently alter every one of those. An opt-in parameter defaulting
  to `False` leaves all existing callers byte-for-byte identical and adds the new
  behaviour only on the age path. This is the smallest change that restores the
  correctness requirement ("age must use the best *dated* event available").

- **Why not fix it entirely inside `get_age` (no signature change)?** That would mean
  re-walking `person.get_primary_event_ref_list()` inside `get_age`, duplicating the
  fallback-selection logic that already lives in the two helpers (the role/`is_*_fallback`
  filtering). Concretely that is ~12 duplicated lines per kind (~24 lines) re-implementing
  what `get_birth_or_fallback`/`get_death_or_fallback` already do, and it would drift from
  them. The chosen approach adds the date check *once* (the 8-line `_has_usable_date`
  helper) and reuses the existing selection loops — net +38/-6 in db.py.

- **Death symmetry.** The brief scope says "birth (or death)". Requiring a date in the
  death fallback is harmless (get_age already demands a valid death date at db.py:125) and
  fixes the symmetric case (dateless primary Death + dated Burial), so both helpers get
  the parameter.

## Test

gramps/gen/utils/test/db_test.py (NEW) drives the **production** `get_age` path (the same
function fanchartview calls — no re-implementation, principles §3.4). It is import-light:
only `gramps.gen.{db,lib,utils.db}` — no `gi`/`gramps.gui` — so it runs under the headless
C4 runner. Two cases:
1. `test_dateless_birth_falls_back_to_dated_baptism` — dateless place-only Birth + dated
   Baptism + dated Death ⇒ age 50 (the bug; `None` pre-fix).
2. `test_dated_primary_birth_unaffected` — dated primary Birth + differently-dated Baptism
   ⇒ age computed from the *birth* (50, not the baptism's 51), proving the dated-primary
   path is untouched.

## Verification

`PDCA_BUNDLE=…/results/issue_7832 ./engine/scripts/ubuntu/run-verify.sh`:
`C4-verify: green-with-fix=PASS / red-without-fix=PASS`. The red leg failed exactly on
case 1's assertion (`unexpectedly None`), while case 2 passed in both legs (no
regression). Ran on the essential line because the host's `gramps-6.1` upstream worktree
had unrelated uncommitted changes; the fix depends only on the standard
`headless-ut-segfault` essential fix (`essential-dependency.json`), not on anything
specific to this patch.

`black` run over both touched `.py` files: `db.py` unchanged, `db_test.py` reformatted
(committed as such). Patch is commit-ready for maintenance/gramps61.
