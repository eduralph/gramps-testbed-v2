# build-notes — issue 6825 / surname-plugins-ignore-group-mapping

## Root cause (verified on maintenance/gramps61)

Surname-grouping consumers resolved the group name two incompatible ways, and
neither honoured the **database-wide** name-group table:

- `Name.get_group_name()` (`gramps/gen/lib/name.py:360-366`) returns the per-name
  `group_as` override if set, else the **raw** primary surname. It never consults
  the db global mapping.
- The only db-aware resolver is
  `NameDisplay.name_grouping_name(db, pn)` (`gramps/gen/display/name.py:1102-1117`):
  `group_as` if set, else `db.get_name_group_mapping(primary_surname)`. This is the
  canonical "what does this name group under" function.

"Group As → **Group All**" in the name editor sets the *global* mapping and
**clears** the local override (`gramps/gui/editors/editname.py:462` `set_group_as("")`
+ `:501` `db.set_name_group_mapping(surname, ngm)`). So after the repro,
`get_group_name()` for Jones returns "Jones" (no override), while
`name_grouping_name(db, …)` returns "Smith".

Consumer state on gramps61 (verified, in-memory sqlite db, mapping Jones→Smith):

| consumer | grouping call | result |
|---|---|---|
| TopSurnamesGramplet `record_surnames` | `Name.get_group_name()` (`topsurnamesgramplet.py:70-73`) | Jones & Smith **separate** |
| SameSurnames `run()` target | `get_group_name()` (`samesurnames.py:121`) | local-only |
| SameSurnames `SameSurname.apply_to_one` | **raw** `get_surname()` (`samesurnames.py:60-63`) | matches literal surname |
| FilterByName "unique surnames" | `get_group_name()` (`filterbyname.py:466`) | local-only |

Two user-visible failures result:
1. **Local override** (the brief's named divergence): TopSurnames groups Jones under
   Smith (count 2), but double-clicking it opens SameSurnames where the filter matches
   the *raw* surname "Smith" → Jones (raw surname "Jones") is missing. Gramplet says 2,
   report shows 1.
2. **Global mapping** (the repro's "Group All"): no consumer groups Jones under Smith
   at all — they are counted/listed separately everywhere.

This is exactly the brief's invariant violation: consumers do **not** apply the same
Group-As mapping (local override *and* the global table) consistently.

## Fix — route every surname-grouping consumer through the canonical resolver

The smallest change that restores the invariant is to make every consumer resolve the
group with the one db-aware function that already honours both mechanisms,
`name_displayer.name_grouping_name(db, name)`:

- `samesurnames.py`: `SameSurname.apply_to_one` now matches the **group name** (not
  raw surname); `run()`'s target resolution + filter build are extracted into the
  import-light `_same_surname_handles(database, person)` (using `name_grouping_name`),
  which `run()` calls — so production and the test drive one implementation.
- `topsurnamesgramplet.py`: `record_surnames` takes `db` and tallies by
  `name_grouping_name`; `main()` passes `self.dbstate.db`.
- `filterbyname.py`: the "unique surnames" tally uses `name_grouping_name`.

After the fix, all consumers resolve Jones→"Smith" for both local and global grouping,
so they agree (verified: see test below).

## Scope — why three files, not one (and not four)

The brief's SELF-TEST: "the property is 'all surname consumers agree on the grouping',
widen any fix to the divergence, not one module." Verify-first showed the divergence
genuinely spans **TopSurnamesGramplet, SameSurnames, and FilterByName "unique
surnames"** w.r.t. the global table — fixing only SameSurnames would make it group
Jones under Smith while TopSurnames/FilterByName still split them, *re-introducing* the
inconsistency under the very repro the brief specifies ("Group All"). So TopSurnames
**must** change for the Success criterion (it is the consumer SameSurnames is required
to agree with), and FilterByName is "any remaining surname-counting consumer".

`StatsGramplet` is out — its surname listing was removed (it now counts incomplete
names; `statsgramplet.py` no longer tallies surnames), matching the brief's "obsolete".

**Rejected — the reporter's 2013 `Utils.get_surname()` refactor.** That shape adds a
*new* shared helper and changes four plugins' call sites to it. The cause here is not a
missing helper — the canonical resolver `name_grouping_name` already exists; the bug is
consumers not *using* it. So the invariant-restoring change is 3 call-site swaps to
existing infra (samesurnames apply_to_one + run, topsurnames record_surnames,
filterbyname tally) — no new module, no `po/POTFILES` change. The 2013 approach would
add an extra indirection (a `Utils` function) on top of the same call-site edits, i.e.
strictly more surface for no behavioural gain, and would not by itself honour the global
table unless that helper took a `db` too.

## Test — `gramps/plugins/gramplet/test/topsurnamesgramplet_test.py`

Extended the existing import-light test (option b in the brief; chosen over a new
`samesurnames_test.py` so the patch ships **one** `*_test.py` for C4's single-module
runner, and because this file already drives `record_surnames`). The existing 5 tests
are updated for the new `record_surnames(db, …)` signature via a tiny `FakeDb`
(empty mapping ⇒ identical to the old behaviour, so they still pass).

New `SurnameGroupingConsistencyTest` builds a real in-memory sqlite db (Smith, Jones)
with `set_name_group_mapping("Jones", "Smith")` and drives the **production** paths:
- `SameSurname(["Smith"]).apply_to_one(db, …)` — the real filter rule run() builds,
- `_same_surname_handles(db, …)` — the function run() calls,
- `record_surnames(db, …)` — the TopSurnames tally,
asserting the two consumers gather the **same** {Smith, Jones} group.

**Import-light / headless:** the test imports `samesurnames` (which imports
`gramps.gui.plug.quick`) **inside** the test methods. Verified headless: the green leg
runs all 9 tests under plain `python3 -m unittest` with no display (mirrors C4 core
mode); gramps GUI editor tests (`editreference_test.py`) already import `gramps.gui`
top-level in the same headless suite, so the quick-view import is safe.

## Verification (local C4-equivalent — docker gate needs approval here)

Could not invoke the docker `run-verify.sh` in this environment (it requires
interactive approval). Ran the identical red→green mechanic in-process instead
(apply patch → run module → `git checkout` the 3 production files keeping the test →
re-run → restore):

- GREEN (patch applied): `Ran 9 tests … OK` (rc 0).
- RED (production reverted, test kept): rc 1 — and the decisive signal is a genuine
  **grouping** assertion, not an API artifact:
  `test_samesurnames_filter_honors_global_mapping … AssertionError: False is not true`
  (`SameSurname` matched raw surname → globally-grouped Jones not gathered with Smith).
  The TopSurnames legs additionally red via the `record_surnames` signature change.

So C4 (green-with-fix ∧ red-without-fix) holds. `black --check --target-version py314`
reports all 4 touched files unchanged (commit-hook clean).

## Files / housekeeping
- No `.py` added or removed → no `po/POTFILES.in`/`POTFILES.skip` change
  (`topsurnamesgramplet_test.py` is pre-existing, already in POTFILES.skip:583).
- Citations are against the gramps-6.1 worktree (upstream/maintenance/gramps61,
  HEAD b679c084f6).
