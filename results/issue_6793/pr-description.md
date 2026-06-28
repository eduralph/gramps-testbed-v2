# Fix: Make surname gramplets count unique surnames consistently

## Root cause

The Top Surnames, Surname Cloud, and Statistics gramplets each developed their own surname-counting approach independently: Top Surnames counted distinct group names (`topsurnamesgramplet.py:130-137`), Surname Cloud counted distinct non-empty `get_surname()` strings (`surnamecloudgramplet.py:101-117`), and Statistics used `len(set(database.surname_list))` which stores only primary-name surnames (`statsgramplet.py:189-191`). Because these three implementations count different things, the same tree produced three different totals (reporter observed 244 vs 449).

## Fix

Align the three divergent approaches by extracting Top Surnames' existing rule into a shared library and converging Surname Cloud and Statistics to use it. This gives the smallest behavioural change while eliminating the inconsistency:

- **New `gramps/plugins/lib/libsurnames.py`** — holds two functions:
  - `record_surnames(person, surnames, representative_handle)` — counts one person's surnames, moved verbatim from `topsurnamesgramplet.py:54-78`, already implementing the canonical rule.
  - `count_unique_surnames(db)` — wrapper that tallies all people and returns the distinct count; used by Statistics.
- **`gramps/plugins/gramplet/topsurnamesgramplet.py`** — imports `record_surnames` from libsurnames (`line 40`); count unchanged as it already used this rule.
- **`gramps/plugins/gramplet/surnamecloudgramplet.py`** — replaces inline enumeration (`lines 101-117`) with `record_surnames()` call and changes reported total from `len(namelist)` to `len(surnames)` (`line 183`), now aligning the count to the group names the cloud displays.
- **`gramps/plugins/gramplet/statsgramplet.py`** — imports `count_unique_surnames` and calls it instead of `len(set(database.surname_list))` (`lines 35, 191`), now counting alternate-name surnames.
- **`po/POTFILES.skip`** — registers the two new `.py` files per T2-potfiles gate.
- **New `gramps/plugins/gramplet/test/surnamecount_test.py`** — headless unittest verifying all three gramplets' paths agree on the same fixture tree.

**Why align on Top Surnames' approach:** It was already working (Top Surnames had no reported issues), matches the Surname Cloud's own keying (the cloud displays by group name, so the count should match its picture), and counts alternate-name surnames — which the Statistics index silently dropped. This choice gives the smallest behavioural change: Top Surnames unchanged, Surname Cloud aligned to its own visualization, only Statistics' count meaningfully increases (to include alternate names the old index excluded). Alternatives (standardizing on Statistics' rule) would require rewriting ~130 lines across both cloud gramplets versus the 2-line convergence here.

## Verified against

- `gramps/plugins/lib/libsurnames.py` — new module exports `record_surnames` and `count_unique_surnames`, implementing the canonical rule.
- `gramps/plugins/gramplet/topsurnamesgramplet.py:40` — imports the shared function.
- `gramps/plugins/gramplet/surnamecloudgramplet.py:30,45,183` — calls `record_surnames` and reports the shared count.
- `gramps/plugins/gramplet/statsgramplet.py:35,191` — imports and calls the wrapper function.
- `gramps/plugins/gramplet/test/surnamecount_test.py:232-264` — tests verify that `record_surnames` (dict-building path), `count_unique_surnames` (wrapper path), and the gramplets' re-imports all resolve to the same shared functions, so the three totals are identical on a fixture tree.
- `po/POTFILES.skip:611,638` — new files registered; no translatable strings present.

## Test

New `gramps/plugins/gramplet/test/surnamecount_test.py` drives the production counting routines on a fixture tree (6 people exercising shared surnames, alternate names, no-surname cases) and verifies:
1. `count_unique_surnames` returns the expected count (8 distinct group names).
2. The dict-building path (`record_surnames` tally) and the wrapper path both yield the same total on the same tree.
3. All three gramplets import the same shared functions (via `assertIs`), so the rule is one and only one.
4. Alternate-name surnames are counted (the old Statistics index silently dropped these).

Test fails RED without the libsurnames module (gramplets cannot import the shared rule) and passes GREEN with the patch applied (`python3 -m unittest gramps.plugins.gramplet.test.surnamecount_test` on the target base; existing `topsurnamesgramplet_test.py` still passes after `record_surnames` relocation).

Fixes #6793
