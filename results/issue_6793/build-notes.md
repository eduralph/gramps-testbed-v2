# Build notes — issue 6793 (surname gramplets disagree on unique count)

## Root cause (two sentences)
Each gramplet that shows a "unique surnames" total enumerated surnames by its own
rule: Top Surnames counted distinct **group names** across primary + alternate names
(`topsurnamesgramplet.py:130-137`), Surname Cloud reported a *separate* count of
distinct non-empty `get_surname()` strings (`surnamecloudgramplet.py:101-117,183`),
and Statistics reported `len(set(database.surname_list))` — the db's primary-name
surname index (`statsgramplet.py:189-191`). Because the three rules count different
things, the same tree produced three different totals (reporter saw 244 vs 449).

## Fix
Introduce **one** canonical rule and route every reporting gramplet through it:

- **New `gramps/plugins/lib/libsurnames.py`** — an import-light module (no `gi` /
  `gramps.gui`) holding the single rule:
  - `record_surnames(person, surnames, representative_handle)` — **moved verbatim**
    from `topsurnamesgramplet.py:54-78` (same docstring, same representative logic).
  - `count_unique_surnames(db)` — `len()` of the `record_surnames` tally over
    `db.iter_people()`; the canonical figure for gramplets that don't build the tally.
- **`topsurnamesgramplet.py`** — imports `record_surnames` from the new lib
  (`from gramps.plugins.lib.libsurnames import record_surnames`) instead of defining
  it; dropped the now-unused `from gramps.gen.lib import Person`. Its reported number
  is unchanged (it already used this rule).
- **`surnamecloudgramplet.py`** — replaced the inline tally + the divergent `namelist`
  accumulation (base `:101-117`) with a `record_surnames(...)` call, and changed the
  reported total from `len(namelist)` to `len(surnames)` (base `:183`). The number now
  matches the cloud the gramplet actually draws (the cloud is keyed by group name).
- **`statsgramplet.py`** — `len(set(database.surname_list))` → `count_unique_surnames(database)`
  (base `:191`); import added at `:35`. The `hasattr(database, "surname_list")` guard
  is kept so the row still appears under the same condition as before.
- **`po/POTFILES.skip`** — registered the two new `.py` (no translatable strings):
  `gramps/plugins/lib/libsurnames.py` and the test
  `gramps/plugins/gramplet/test/surnamecount_test.py` (doc 16 §Adding and removing
  Python files; T2-potfiles).

The single shared rule is `record_surnames`; `count_unique_surnames` is a thin `len`
wrapper over it. All three gramplets therefore derive the figure from one
implementation, so agreement is by construction.

## Canonical rule chosen — and why (this is the NEEDS-HUMAN call)
**A unique surname = a distinct surname *group name*, taken across each person's
primary and alternate names** (empty / "no surname" counts as one bucket if present,
matching Top Surnames' existing behaviour).

Why this rule:
- It is what **Top Surnames already reported** — so that gramplet's number does not
  change.
- It is what the **Surname Cloud visualisation is keyed on** (`surname_sort` / the
  cloud links are group names) — so the Cloud's *number* now matches its own *picture*.
- It counts **alternate-name surnames** (e.g. a married name added as an alternate
  name — the reporter's exact scenario), which the old Statistics `surname_list` rule
  silently dropped (the index stores only the first surname part of the *primary* name —
  `gen/db/generic.py:2598-2602`).

Alternatives considered and rejected (cost shown, not adjectives):
1. **Standardise on `database.surname_list`** (Statistics' old rule). Cheapest for
   Statistics (no per-person scan), but it counts only `primary_name.surname_list[0]`
   (`gen/db/generic.py:2598-2602`) — it ignores alternate names *and* secondary surname
   parts, the least faithful notion of "unique surnames". Adopting it would force Top
   Surnames **and** Surname Cloud to abandon group-name counting and rebuild their
   clouds from the index — rewriting the cloud-building loops in both
   (`topsurnamesgramplet.py:113-153`, ~40 lines, and `surnamecloudgramplet.py:94-186`,
   ~90 lines), versus the 2-line touch this fix makes to each. Rejected: most churn to
   the two cloud gramplets *and* the weakest definition.
2. **Standardise on distinct non-empty `get_surname()`** (Surname Cloud's old `namelist`
   rule). It disagrees with surname *grouping* (e.g. "af Ekenstam" groups under
   "Ekenstam") and excludes the no-surname bucket inconsistently with Top Surnames, so
   it would *change* Top Surnames' number and still not match the cloud. Rejected.

The chosen rule is the smallest behavioural change that makes the three agree: Top
Surnames unchanged, Surname Cloud's number aligned to its own cloud, only Statistics'
number meaningfully changes. **Which rule is canonical remains the human's design call
at sign-off** (brief Disposition / fitness-to-purpose).

## Scope discipline
Did **not** touch the cloud weighting/font-size visualisation, surname *grouping*
config, or the patronymic-origin question (issue 6988). 6988 also edits
`topsurnamesgramplet.py`/`statsgramplet.py`; this change is independent (count
*consistency*, not patronymic *membership*) and must not be co-scheduled with 6988.

## Test — `gramps/plugins/gramplet/test/surnamecount_test.py` (NEW)
Follows the established import-light pattern of the sibling
`topsurnamesgramplet_test.py` (builds `Person` fixtures, drives the production routine
directly — no `gi`/GUI import, so it runs under the headless C4 runner). It:
- drives the **production** `count_unique_surnames` / `record_surnames` (imported via
  the gramplets' own import paths — not a re-implementation), on a fixture tree that
  exercises the divergence cases (shared surname, married/alternate name, alternate-only
  surname, no-surname person);
- asserts the dict-building path (Top Surnames / Surname Cloud) and the wrapper path
  (Statistics) give the **same** total on the same tree;
- asserts the three gramplets reference the **same** shared functions
  (`assertIs`), i.e. one rule — the agreement the brief's Success criterion names.

### Red→green (verified)
Ran in an isolated worktree freshly checked out at the target base
(`upstream/maintenance/gramps61`, `b679c084f6`):
- **GREEN with the patch applied:** all 4 tests pass.
- **RED with production reverted, test kept:** `ModuleNotFoundError: gramps.plugins.lib.libsurnames`
  — without the unifying production module the gramplets have no shared rule and the
  test cannot run. (The divergent old rules lived inside the GUI `main()` generators,
  which are not headless-callable; per the brief the test drives the extracted routine,
  matching the `topsurnamesgramplet_test.py` precedent.)
- `git apply --check` of `patch.diff` against the clean base passes.
- `black --check` passes on all five touched/added Python files.

> Note: the Docker-based `run-verify.sh` C4 runner requires an interactive permission
> grant this autonomous session could not obtain, so the red→green was reproduced with
> plain `python3 -m unittest` against a clean `git worktree` of the target base (the
> same headless mechanic the C4 runner applies). The existing
> `topsurnamesgramplet_test.py` still passes after `record_surnames` was relocated.

## Commit-readiness
`black` clean on `libsurnames.py`, `statsgramplet.py`, `surnamecloudgramplet.py`,
`topsurnamesgramplet.py`, `surnamecount_test.py`. New files carry the GPL header
(T2-shape) and are registered in `po/POTFILES.skip` (T2-potfiles).
