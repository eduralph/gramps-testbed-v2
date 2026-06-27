## Root cause

The Surname Cloud and Statistics gramplets enumerate the full multi-component surname string (via `Name.get_surname()`) without distinguishing origin, so non-primary surnames of patronymic origin inflate and fragment the tally. A person with a primary family surname "Иванов" plus a separate `PATRONYMIC`-origin surname therefore produces one entry per patronymic variant ("Иванов Петрович", "Иванов Сергеевич", "Иванов Андреевич") instead of a single family surname count.

The root cause is located in how the gramplets key their counts: Surname Cloud builds its `namelist` from `name.get_surname().strip()` (surnamecloudgramplet.py:111-117), and Statistics tallies `len(set(database.surname_list))` which is keyed off `surname_list[0].surname` positionally without origin awareness (statsgramplet.py:191).

## Fix

A shared counting routine `get_counting_surname(name)` in a new module `gramps/plugins/gramplet/surnamecounter.py` filters the surname list to drop non-primary components of `PATRONYMIC` or `MATRONYMIC` origin, then reuses the production `Name.get_surname()` formatting on the kept components. This collapses patronymic noise while preserving other secondary surnames (e.g., Spanish maternal names).

Both gramplets are wired to route through this helper:
- **Surname Cloud** (surnamecloudgramplet.py): the `namelist` tally now calls `get_counting_surname(name)` for each name instead of `name.get_surname()`.
- **Statistics** (statsgramplet.py): unique surnames accumulate via the helper from each person's primary name, and the display shows `len(unique_surnames)` instead of `len(set(database.surname_list))`.

The new test file (`gramps/plugins/gramplet/test/patronymic_surname_count_test.py`) drives the production routine on a constructed `Name` carrying a primary surname plus a `PATRONYMIC`-origin component, asserting the counting surname strips the patronymic while documenting the buggy `name.get_surname()` output for contrast.

Both new `.py` files are registered in `po/POTFILES.skip` (no translatable strings).

## Verified against

- `gramps/plugins/gramplet/surnamecloudgramplet.py:111-117` — the `namelist` tally that enumerates surnames for the cloud display.
- `gramps/plugins/gramplet/statsgramplet.py:84-114` — the person loop and surname tallying section where unique surnames are now accumulated via the helper.
- `gramps/plugins/gramplet/statsgramplet.py:189-191` — the display of unique surname count that switches from `len(set(database.surname_list))` to the accumulated set.
- `po/POTFILES.skip` — the POTFILES skip list where new non-translatable modules are registered.

## Test

The regression test (`gramps/plugins/gramplet/test/patronymic_surname_count_test.py`) drives the production `get_counting_surname()` helper directly with a constructed `Name` bearing a primary "Иванов" plus a `PATRONYMIC`-origin "Петрович", asserting the counting surname is "Иванов" alone. Additional test cases verify that different patronymics of the same family surname map to the same counting key, that matronymics are collapsed identically, that non-patronymic secondary surnames are preserved (e.g., "García Pérez"), and that edge cases (single-component names, only-patronymic names) fall back to the existing behavior.

Red/green verification was performed by hand against the clean upstream `gramps-6.1-lane0` worktree via `python3 -m unittest`:
- **RED**: production files reverted, test file kept → `ModuleNotFoundError: gramps.plugins.gramplet.surnamecounter` (test genuinely depends on the helper, not a copy).
- **GREEN**: patch applied → all 6 tests pass.

## Design choice — NEEDS-HUMAN

**Should patronymic surnames be excluded or grouped?** This fix chooses **origin-aware exclusion** of only patronymic/matronymic non-primary components, preserving every other secondary surname (e.g., a Spanish maternal name "García **Pérez**" stays intact as "García Pérez"). The alternative — using `get_group_name()` — would silently drop *all* secondary surnames, collapsing "García Pérez" to "García" alone.

The exclusion approach is the smaller behavioral change and matches the brief's framing of "distinguishing surname origin." However, the correct treatment of patronymic surnames in counts is a design call for the human at sign-off. If grouping by primary surname alone is preferred, the single predicate in `surnamecounter.py:150` can be changed.

**Note for Statistics gramplet:** a secondary behavioral change occurs with prefixed surnames ("van der Berg"). The Statistics count key changes from the bare surname ("Berg", from `database.surname_list[0].surname`) to the formatted family surname with prefix ("van der Berg", from `get_counting_surname()`). This is arguably more correct and now consistent with the Surname Cloud and Top Surnames displays, but it is a change beyond the patronymic case.

Fixes #6988
