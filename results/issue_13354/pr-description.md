## Root cause

The Convert2Rel batch-op's `description` attribute (the tooltip shown in the Media Manager tool) contains a misspelling: "viz-a-viz" instead of the correct loanword "vis-à-vis". This is a purely translatable English-source string defect with no behavioral impact.

## Fix

Changed the single misspelled word in `gramps/plugins/tool/mediamanager.py:640`:
- `"viz-a-viz the base path as given in the Preferences, "`
+ `"vis-à-vis the base path as given in the Preferences, "`

The canonical accented form "vis-à-vis" (UTF-8 `à` U+00E0) is used, consistent with Gramps' existing typography. The surrounding tooltip text was left untouched per scope. Two new test files are registered in `po/POTFILES.skip`.

## Verified against

- `gramps/plugins/tool/mediamanager.py:640` — the misspelled help string on the target branch (maintenance/gramps61)
- `gramps/plugins/tool/mediamanager.py:635–644` — the Convert2Rel class under test, which carries the `description` attribute as a class variable
- `po/POTFILES.skip` — insertion point for test file registration following existing `gramps/plugins/tool/__init__.py`

## Test

New test package `gramps/plugins/tool/test/`:
- `gramps/plugins/tool/test/__init__.py` — empty package marker (lines 1–1)
- `gramps/plugins/tool/test/mediamanager_test.py` — unittest exercising the production `Convert2Rel.description` attribute

The test (`gramps/plugins/tool/test/mediamanager_test.py:65–71`) reads the shipped class attribute directly and asserts both:
1. `"viz-a-viz"` is NOT present in the help text
2. `"vis-à-vis"` IS present in the help text

Red→green: With the fix in place, both assertions pass. Reverting `mediamanager.py` (keeping the test) causes both to fail, proving the test detects the regression. The test follows the core convention (`*_test.py` suffix in a `test/` package) and will be discovered by `run-unit.sh -p "*_test.py"`.

Fixes #13354
