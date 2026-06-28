# PR description

## Root cause

In narrative text reports (Detailed Descendant, Detailed Ancestor, etc.), the spouse in a marriage sentence is rendered with the spouse's currently-preferred (primary) name using `name_display.display(spouse)`. When the spouse later divorces and remarries, their preferred name changes to a later married name, so the past-tense sentence about the *earlier* marriage silently becomes ambiguous — the reader cannot tell which marriage the sentence refers to.

The shared narrator method (`gramps/plugins/lib/libnarrate.py:2369-2372` on the target branch) needs to name the spouse by a stable reference unaffected by later name changes.

## Fix

Added two helper functions to `gramps/plugins/lib/libnarrate.py`:
- `_get_birth_name(person)` — scans the person's primary and alternate names, returning the first name of type `NameType.BIRTH` if present
- `_get_spouse_name(spouse, name_display)` — displays the spouse using their birth name when present; otherwise falls back to the currently-preferred name (preserving output for everyone without a separate birth name)

Modified `Narrator.get_married_string()` to call `_get_spouse_name()` instead of the inline `name_display.display(spouse)` code. This single change in the shared narrator fixes the spouse-naming issue for all narrative reports that use it.

Added `NameType` import after the existing imports.

Registered the new test files (`gramps/plugins/lib/test/__init__.py` and `gramps/plugins/lib/test/libnarrate_test.py`) in `po/POTFILES.skip` as test-only files with no translatable strings.

## Verified against

- `gramps/plugins/lib/libnarrate.py:39` — import location for NameType
- `gramps/plugins/lib/libnarrate.py:91-94` — where the new helper functions are added
- `gramps/plugins/lib/libnarrate.py:2369-2372` — the original spouse-naming code replaced by the helper call
- `po/POTFILES.skip:610+` — test file registration area

## Test

New regression test in `gramps/plugins/lib/test/libnarrate_test.py` (gramps core test format: `test/` package, `*_test.py` suffix) drives the production `Narrator.get_married_string()` path over in-memory Gramps objects with three test cases:

1. `test_uses_birth_name_not_later_preferred_married_name` — spouse whose preferred name is a later married name but who retains her birth name as an alternate must be named by the stable birth name in the sentence, not the later name
2. `test_stable_when_a_later_preferred_name_is_acquired` — the same spouse before and after acquiring a later preferred married name must yield the identical sentence (the stability guarantee)
3. `test_falls_back_to_preferred_name_without_a_birth_name` — non-regression guard: when the spouse has no birth name, the preferred name is still used (backward compatibility)

The test is import-light (no `gi` / gramps.gui), so it runs under the headless C4 runner. Verified red→green: tests 1 and 2 fail without the fix (AssertionError on the spouse surname), test 3 stays green both ways.

Fixes #4862
