# Build notes — issue 6988 (surname-count-includes-patronymic-nonprimary)

## Root cause (verified against target `maintenance/gramps61`, worktree `gramps-6.1`)

A person's surname can carry several components (a `Surname` list). The family
name is the *primary* component; a Russian patronymic is a **non-primary**
component of origin `NameOriginType.PATRONYMIC`. `Name.get_surname()`
(`gramps/gen/lib/surnamebase.py:180-205`) concatenates **all** components, so
"Иванов" + patronymic "Петрович" formats as `"Иванов Петрович"`.

The surname gramplets keyed their unique-surname tallies off that full string:

- **Surname Cloud** — the *Total unique surnames* `namelist` was built from
  `name.get_surname().strip()` (`surnamecloudgramplet.py:111-117`). Three people
  "Иванов" with different patronymics → three list entries.
  (Its main per-surname dict at `:104` already groups correctly via
  `get_group_name()`, which is why the bug reporter saw the cloud's *displayed*
  surnames collapse to "Иванов" while the *count* fragmented.)
- **Statistics** — *Unique surnames* was `len(set(database.surname_list))`
  (`statsgramplet.py:191`). `Db.add_to_surname_list`
  (`gramps/gen/db/generic.py:2591-2610`) keys off `surname_list[0].surname` —
  positional, origin-blind — so a record whose patronymic sits first fragments
  the set (sam888's tracker note: "Unique surnames: 3").

`topsurnamesgramplet.py` was **already fixed** for grouping (it uses
`get_group_name()` via `record_surnames`, commit e39dc09e2e), so it is left
untouched — the remaining fragmenting routines are the two above, exactly the
two the brief cites.

## Fix

One shared, import-light counting routine that both gramplets route through —
`get_counting_surname(name)` in a new module
`gramps/plugins/gramplet/surnamecounter.py`. It drops **non-primary** surname
components of patronymic/matronymic origin, then reuses the *production*
`Name.get_surname()` formatting on the kept components (it builds a throwaway
`Name` over the filtered list rather than re-implementing the prefix/connector
formatting — principles §3.4, no parallel copy). When there is nothing
patronymic to drop, or the patronymic is the only component, it returns the
unchanged `name.get_surname()` string, so existing behaviour is preserved for
every non-patronymic name.

Wiring:
- `surnamecloudgramplet.py:111-117` → `get_counting_surname(name)` for the
  `namelist` tally.
- `statsgramplet.py` → accumulate `unique_surnames` from each person's primary
  name via the helper in the existing person loop, and display
  `len(unique_surnames)` instead of `len(set(database.surname_list))`. The
  `hasattr(database, "surname_list")` visibility guard is kept, so the line
  still appears under exactly the same condition as before.

## Why "exclude patronymic-origin non-primary" rather than "group by primary"

The disposition is NEEDS-HUMAN (exclude vs group is the human's call). I chose
the **origin-aware exclusion** of only patronymic/matronymic non-primary
components, not the blunter `get_group_name()` (which returns the primary
surname alone and would silently drop *every* secondary surname — e.g. a Spanish
maternal name "García **Pérez**" would become "García"). The exclusion keeps
legitimate secondary family surnames intact (test
`test_non_patronymic_secondary_surname_preserved`) while collapsing exactly the
patronymic the bug is about. This matches the brief's framing ("distinguishing
surname origin") and is the smaller behavioural change.

Cost of the rejected `get_group_name()` alternative was not the diff size (it
would be a smaller diff — one helper line) but **scope of behavioural change**:
it alters the count for *any* multi-component primary name, patronymic or not,
whereas the chosen routine touches only patronymic/matronymic carriers. The
human can still flip to grouping at sign-off by changing the one filter
predicate in `surnamecounter.py`.

## Known nuance for the human (Statistics only)

`database.surname_list` stores the *bare* `surname_list[0].surname` (no prefix);
`get_counting_surname` returns the formatted family surname (with prefix/
connector). For **prefixed** surnames ("van der Berg") the Statistics count key
therefore changes from "Berg" to "van der Berg" — arguably more correct and now
consistent with how the Surname Cloud and Top Surnames render the same name, but
it is a behavioural change beyond the patronymic case. It does **not** attempt
the cross-gramplet count *unification* (issue 6793, explicitly out of scope): the
two gramplets still count different populations (Cloud: primary+alternate names;
Stats: primary names only). It only removes patronymic fragmentation within each.

## New files registered

Both new `.py` files have no translatable (`_()`) strings, so both go in
`po/POTFILES.skip` (doc 16): `gramps/plugins/gramplet/surnamecounter.py` and the
test `gramps/plugins/gramplet/test/patronymic_surname_count_test.py`. The
`test/__init__.py` already exists upstream. The POTFILES.skip hunk is written
against the clean `HEAD` (the shared worktree carried an unrelated bundle's
edits to that file, so the hunk was crafted from `git show HEAD:po/POTFILES.skip`
rather than the dirty working copy).

## Verification (red → green)

The bundled C4 runner (`run-verify.sh`) requires Docker, which this sandbox
would not authorise. I ran the equivalent red/green by hand against the **clean**
`gramps-6.1-lane0` upstream worktree (the same worktree class C4 patches), via
`python3 -m unittest` (headless, import-light — the test imports only
`gramps.gen.lib` and the new helper, no `gi`/`gramps.gui`):

- **GREEN** (patch applied): all 6 tests pass.
- **RED** (production reverted — `surnamecloudgramplet.py`, `statsgramplet.py`,
  `po/POTFILES.skip` checked out, `surnamecounter.py` removed; test kept): the
  test errors with `ModuleNotFoundError: gramps.plugins.gramplet.surnamecounter`
  — it genuinely depends on the production routine, not a copy.

The test drives `get_counting_surname` directly — the same routine both
gramplets call — on a constructed `Name` carrying a primary "Иванов" plus a
`PATRONYMIC`-origin "Петрович", asserting the counting surname is "Иванов" while
documenting the buggy `name.get_surname() == "Иванов Петрович"` contrast.

`black 26.5.0` was run over all four touched/added files before generating the
patch (commit-ready for gramps' own pre-commit hook); the patch applies cleanly
to clean `maintenance/gramps61` (`git apply --check` OK).
