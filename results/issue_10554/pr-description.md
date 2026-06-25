# Distinguish adopted relationships from step relationships

## Root cause

The relationship calculator (`gramps/gen/relationship.py:908-935`) defined relationships by a binary birth/non-birth distinction, and `__apply_filter` and `get_sibling_type` rendered every non-birth link with the `"step"` qualifier. Even though the database records an adopted child-reference explicitly with `ChildRefType.ADOPTED`, the calculator collapsed ADOPTED, STEPCHILD, FOSTER, and other non-birth types to one bucket, so reports (particularly the Narrative Web) call an adopted child a stepchild — genealogically and legally incorrect.

## Fix

The change threads the `ChildRefType` through the relationship paths as a third class of link (birth / **adopted** / step), keeping "step" behavior unchanged for non-adopted, non-birth links. Key modifications to `gramps/gen/relationship.py`:

1. **New path codes and sibling type** (`relationship.py:908-935`): Added `REL_MOTHER_ADOPT="n"`, `REL_FATHER_ADOPT="d"`, `REL_FAM_ADOPT="D"` to denote adopted parent links; introduced `ADOPT_SIB=5` for adopted siblings; added `ADOPT="adopted "` as the localizable qualifier.

2. **Path building in `__apply_filter`** (`relationship.py:1524-1650`): The method now emits the adopt code when a `ChildRefType` is `ADOPTED`, else the existing NOTBIRTH code for other non-birth types.

3. **Adopted parent detection** (`relationship.py:1204+` area): New helper method `_get_adopted_parent_list` mirrors `_get_nonbirth_parent_list` and returns parents linked by adoption only.

4. **Sibling qualifier logic** (`relationship.py:1124-1170`): `get_sibling_type` now calls a new `_step_or_adopt_sib` method to distinguish whether a non-birth sibling connection is via an adopted or plain-step parent; true stepsiblings (different birth parents known) still return `STEP_SIB`.

5. **Single-relationship string qualifier** (`relationship.py:2235+` area, `get_single_relationship_string` method): The qualifier is now `""` for birth, `ADOPT` when `only_adopt(path)` returns true (i.e., the path's non-birth hops are all adopted), else `STEP`.

6. **Dual-parent adoption** (`relationship.py:1843-1915`): `_famrel_from_persrel` now maps adopted-to-adopted links to `REL_FAM_ADOPT`; `get_one_relationship` (`relationship.py:1990-2061`) includes the new codes in the order list so `.index()` cannot raise.

7. **New `only_adopt()` method** (`relationship.py:1880+`): Returns true iff a path's non-birth hops are all adopted (no plain-step hop), used to select the adopted qualifier.

8. **Test registration** (`po/POTFILES.skip:301`): Registered the new test file (no translatable strings) per doc 16.

Locale safety: The 22 locale overrides derive `step` from the `only_birth` *flag* (verified in `rel_nl.py:769` as representative), not by parsing the path. An un-updated locale does not crash on the new path codes `n`/`d`/`D` and keeps current "step" rendering for adopted links until updated — exactly the "default sensibly, untranslated but not wrong/crashing" the design required.

## Verified against

- `gramps/gen/relationship.py:908-935` — relationship code constants (REL_* and ADOPT_SIB)
- `gramps/gen/relationship.py:1124-1170` — `get_sibling_type` and new `_step_or_adopt_sib` logic
- `gramps/gen/relationship.py:1204-1250` — `_get_nonbirth_parent_list`; `_get_adopted_parent_list` inserted below it
- `gramps/gen/relationship.py:1524-1650` — `__apply_filter` path-building (added ADOPT check)
- `gramps/gen/relationship.py:1843-1915` — `_famrel_from_persrel` and family-relation logic
- `gramps/gen/relationship.py:1880-1910` — `only_birth` method; new `only_adopt` method appended
- `gramps/gen/relationship.py:1990-2061` — `get_one_relationship` order list updated
- `gramps/gen/relationship.py:2235-2350` — `get_single_relationship_string` qualifier logic
- `po/POTFILES.skip:299-303` — test registration

## Test

`gramps/gen/test/relationship_test.py` (new): A unit test that builds an in-memory database with a father/mother couple and three sons—one birth, one adopted, one stepchild—and asserts:

- An adopted child is NOT labelled "step" and reads as "adopted ..."
- A genuine stepchild is still labelled "step"
- Reciprocal adopted-parent relation is labeled "adopted"
- Adopted siblings are NOT labelled "step"

The test exercises the production path `get_one_relationship` (what the Narrative Web and every relationship consumer use). It runs under the headless test runner (no GUI imports; uses `make_database("sqlite")` pattern from `gramps/gen/utils/test/alive_test.py`). The regression contract is red without the production change (4 adopted assertions fail; step + birth guards pass) and green with it (7/7 pass).

Fixes #10554
