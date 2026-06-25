# Build notes — issue 6826 (topsurnames-representative-wrong-surname)

## Disposition: verify-first / POSSIBLY-FIXED — duplicate of 11101

The reported defect is already fixed in the target tree. Commit **e39dc09e2e**
"Fix Top Surnames gramplet opening report for the wrong surname" (Fixes #11101)
reworked the representative selection. So this bundle ships **only the 6826 repro
as a regression test**; there is no production change to make.

- Target branch: gramps-project/gramps @ `maintenance/gramps61` (worktree
  `../gramps-6.1`, HEAD `b679c084f6`, with e39dc09e2e present).
- Production helper under test: `record_surnames()` at
  `gramps/plugins/gramplet/topsurnamesgramplet.py:54-78`.

## Root cause (for context — already fixed)

Pre-fix `main()` (the body now in `record_surnames`) wrote
`representative_handle[surname] = person.handle` **unconditionally** for every
group name from a person's primary *and* alternate names. So for any surname the
**last-iterated** person carrying it (primary or alternate) won the representative
slot. The Same Surnames quick view (`samesurnames.py run()`) re-derives the clicked
surname from the representative's *primary* name — so if the representative held the
clicked surname only as an alternate, the report opened for that person's *primary*
surname instead. Reported repro: P1 primary "A" + alternate "B", P2 primary "B";
clicking "B" showed "People sharing the surname 'A'".

The fix (`topsurnamesgramplet.py:75-78`) only (re)assigns the representative when
`surname == primary_surname or surname not in representative_handle`, so a
primary-name carrier always wins and order no longer matters.

## What I built

Extended the existing test
`gramps/plugins/gramplet/test/topsurnamesgramplet_test.py` (core convention:
`test/` package + `*_test.py` suffix, per INTEGRATION §3) with
`test_reported_repro_6826_clicked_surname_resolves_to_primary_carrier`
(`topsurnamesgramplet_test.py:154-186`). It models the **exact reported repro**
(P1 primary A + alt B, P2 primary B) and asserts `representative_handle["B"] == "P2"`
(the primary-B carrier) for **both** iteration orders — the order-independence the
bug violated. It also pins the surname counts (B counted twice, A once).

The test drives the **production** `record_surnames` (imported directly at
`topsurnamesgramplet_test.py:39`), not a copy — the same callable `main()` routes
through at `topsurnamesgramplet.py:120`. The unit is import-light: the module pulls
only `gramps.gen.*` (`Gramplet`, `Person`, `PersonHandle`), no `gramps.gui` / `gi`,
so it runs headless.

## Why a distinct test rather than relying on the existing 11101 cases

The existing `test_representative_*` cases use Webb/Allen and already exercise the
same mechanism, but the brief's Success criterion is the *reported 6826 scenario*
(primary A + alt B vs primary B, click B). I added a case named and structured to
that repro so the verify-first record shows the reported case specifically resolves,
and so it survives independently if the 11101 cases are ever refactored.

## Red→green evidence

`run-verify.sh` returns **PDCA-UNVERIFIABLE** (test-only patch — no production file
for the red leg to revert), expected for verify-first and flagged in the brief →
§6 NEEDS-HUMAN under the C6 guard.

I proved the red→green out of band (import-light, no Docker hang risk):
- **Green** on the fixed tree: all 6 tests pass against the real
  `record_surnames`.
- **Red** on pre-fix logic: monkeypatching `record_surnames` back to the
  unconditional-overwrite version makes the new test fail with
  `AssertionError: 'P1' != 'P2'` for order `('P2','P1')` — i.e. "B" resolves to the
  primary-A carrier, the exact bug. This confirms the test is a genuine regression,
  not a tautology.

## Out of scope (note for the human — separate, deeper concern)

The residual case where a surname appears **only** as an alternate name (no person
holds it as primary) still re-derives from the representative's primary name in
`samesurnames.py run()` and cannot match. That is *not* the 6826 reported repro and
is a separate concern (the existing
`test_alternate_only_surname_falls_back_to_first_seen` documents the best-effort
fallback). Not addressed here.

## Commit-readiness

`black --check` reports the touched test file unchanged (gramps' pre-commit
formatter). No `.py` added/removed → no `po/POTFILES.*` change (T2-potfiles N/A).
