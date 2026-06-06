---
title: "Gramps 6.1 Wiki Manual - Core Development - Testing"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

How Gramps **core** is tested — the framework, the layout conventions, the fixtures, and the static-analysis gate that runs alongside the suite. Audience: a contributor working on [`gramps-project/gramps`](https://github.com/gramps-project/gramps) on `maintenance/gramps61`.

A passing test suite is what lets a fix land without manual GUI regression. Two layout conventions are easy to get wrong — the test directory name and the test-file naming — and getting them wrong puts the test where the runner won't find it. They are spelled out below; the normative MUST/SHOULD rules live in [[16-guidelines]], which this page is the how-to companion to.

> **The one rule to memorise.** Core uses a **`test/` package (singular)** holding **`<module>_test.py`** files (the suffix). Get this right and the `-p "*_test.py"` runner finds the test; get it wrong and it won't. ([[16-guidelines]] §Testing; `docs/INTEGRATION.md` §3.)

## Framework: stdlib `unittest`

Use stdlib `unittest` — subclasses of `unittest.TestCase`. **Do not use pytest.** Core CI runs the suite with `python3 -m unittest`; pytest isn't installed, so pytest-only features (fixtures, `parametrize`, plugins) break the suite. (`gramps/AGENTS.md` §Testing; [[16-guidelines]] §Testing MUST.)

```python
import unittest

from .. import constfunc


class TestHasDisplay(unittest.TestCase):
    def test_consistent_with_display_env(self):
        self.assertEqual(constfunc.has_display(), expected)


if __name__ == "__main__":
    unittest.main()
```

The relative import (`from .. import constfunc`) is the in-tree pattern: a `test/` package sits *beside* the module it exercises, so the module under test is the parent package. See `gramps/gen/test/constfunc_test.py:23` for the live form.

### Class-header navigation comment

The class-header navigation comment from `gramps/AGENTS.md` §Class Headers is **unconditional** — it applies to `unittest.TestCase` subclasses too, not just shipping classes. ([[16-guidelines]] §Source structure SHOULD; PR 2326 round 2.)

```python
# ------------------------------------------------------------
#
# TestHasDisplay
#
# ------------------------------------------------------------
class TestHasDisplay(unittest.TestCase):
    ...
```

## Layout: `test/` (singular) beside the module

Each core source tree ships its tests in a **`test/` subpackage** (singular) alongside the modules it covers, each with an `__init__.py`:

```
gramps/gen/lib/
├── person.py
├── family.py
└── test/
    ├── __init__.py
    ├── person_test.py        # <module>_test.py — the SUFFIX
    └── family_test.py
```

This is verified across the checkout — 30 `test/` packages on `maintenance/gramps61`, and **zero** `tests/` (plural) directories anywhere under `gramps/`:

```bash
find gramps -type d -name test  | wc -l   # 30
find gramps -type d -name tests | wc -l   # 0
```

Representative homes: `gramps/gen/lib/test/`, `gramps/gen/db/test/`, `gramps/gui/test/`, `gramps/plugins/importer/test/`, `gramps/cli/test/`.

> **MUST NOT** create a `tests/` (plural) directory under `gramps/`. It (a) hides the test from the `-p "*_test.py"` discovery pattern and (b) can trip the [Mantis 12691](https://gramps-project.org/bugs/view.php?id=12691) submodule-binding trap. This cost iterations on issue 13636, where the wrong layout was used for a core fix. ([[16-guidelines]] §Testing MUST NOT; `docs/INTEGRATION.md` §3.)

### Filename: the `_test.py` **suffix**

Test files are named `<module>_test.py` — the suffix form. CI discovers by suffix:

| Aspect    | Core convention      |
|-----------|----------------------|
| Directory | `test/` (singular)   |
| File      | `<module>_test.py`   |
| Naming    | suffix               |
| Discovery | `-p "*_test.py"`     |

Live examples: `gramps/gen/test/constfunc_test.py`, `gramps/gui/test/user_test.py`, `gramps/plugins/test/imports_test.py`.

## Running the suite

From the gramps checkout root, with `GRAMPS_RESOURCES` pointing at the source tree:

```bash
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

`GRAMPS_RESOURCES=.` tells Gramps to load its data files from the checkout instead of an installed copy — run from source for development, never from an installed copy ([[16-guidelines]] §Source structure MUST). The `-p "*_test.py"` pattern is what selects the suffix-named files; this is the same invocation CI and the testbed's `run-unit.sh` use (`docs/INTEGRATION.md` §3).

Run a single module or directory while iterating:

```bash
# One test module by dotted path
GRAMPS_RESOURCES=. python3 -m unittest gramps.gen.test.constfunc_test

# Just one package's tests
GRAMPS_RESOURCES=. python3 -m unittest discover -s gramps/gen/lib/test -p "*_test.py"
```

## mypy is enforced

Core **enforces `mypy`** — changes must pass static type analysis before they merge (`gramps/AGENTS.md` §Type Checking; [[16-guidelines]] §Testing MUST). Invoke it with no arguments from the checkout root — it reads `mypy.ini`:

```bash
mypy
```

`mypy.ini` scopes the run to both the package and the test trees, and excludes plugin-registration files:

```ini
[mypy]
files = ./gramps, ./test
exclude = .*gpr\.py$
```

So `*.gpr.py` registration files are not type-checked, but the rest of `gramps/` **and** the top-level `test/` tree are (`mypy.ini:1-3`). Because the test files are in scope, type-hint your `TestCase` code too. Type hints use Python 3.10+ syntax — `X | None`, `list[X]`, handle types from `gramps/gen/types.py` — see [[16-guidelines]] §Coding style and [[11-code-analysis]] for the full static-analysis story (Black, mypy, pylint).

## The `example.gramps` fixture

`example.gramps` is the canonical populated database — the one triage and developers reproduce against. It ships with the source at **`example/gramps/example.gramps`**, and is the fixture to use for any code that traverses a real database, because it carries the cross-typed backlinks, ID normalisations, and absent optional fields that real user data has and a hand-built stub doesn't.

In-tree DB-traversal tests load it via `import_as_dict`, joining against the test-data copy that `TEST_DIR` resolves to (`gramps/gen/const.py:425` → `data/tests/example.gramps`):

```python
import os
import unittest
from typing import Any, ClassVar

from ....const import TEST_DIR
from ....db.utils import import_as_dict
from ....user import User

EXAMPLE = os.path.join(TEST_DIR, "example.gramps")


# ------------------------------------------------------------
#
# BaseTest
#
# ------------------------------------------------------------
class BaseTest(unittest.TestCase):
    db: ClassVar[Any]

    @classmethod
    def setUpClass(cls):
        """Import the example database once for all tests in the class."""
        cls.db = import_as_dict(EXAMPLE, User(), person_prefix="I%04d")
```

This is the live pattern from `gramps/gen/filters/rules/test/person_rules_test.py:105` and `:139-160`. `setUpClass` imports the DB **once per class**, not once per test — loading the example database is heavy. The prefixes (`person_prefix="I%04d"`, …) match the example file's Gramps IDs so assertions can reference known IDs. For the data-access APIs these tests call against the loaded DB, see [[06-data-access]].

> Two copies exist: `example/gramps/example.gramps` is the canonical user-facing fixture the brief and triage cite; `data/tests/example.gramps` (via `TEST_DIR`) is the in-tree copy the suite imports. They are the same example dataset; cite the former when describing the fixture, use the latter (`TEST_DIR`) inside a `test/` package.

## What to test

- **MUST — the bug a fix closes.** Every bug fix ships a regression test that **fails pre-fix and passes post-fix** (red-before / green-after). Doc-only PRs are the only exception. ([[16-guidelines]] §Testing SHOULD / §Contributor workflow MUST.) Demonstrate the red→green: run the new test against the unpatched tree (it fails), apply the fix, run again (it passes) — a green run on the patched tree alone proves nothing. The testbed's C4 gate (`run-verify.sh`) mechanises exactly this assertion (`docs/INTEGRATION.md` §3).
- **SHOULD — each distinct flow of logic.** Happy path, error cases, edge cases (empty DB, missing optional fields, IDs at normalisation boundaries). (`gramps/AGENTS.md` §Testing.)
- **One real-data scenario** against `example.gramps` for any DB-traversal code — the shape a hand-built object can't reproduce.

What *not* to test: the Gramps API's own contract. If `db.get_person_from_handle(h)` returns `None` for a missing handle, that's Gramps' behaviour; your test verifies *your* code handles `None`, not that Gramps returns it.

## What the test catches that a manual run doesn't

| Failure mode | Where it surfaces |
|--------------|-------------------|
| `gen` self-containment breach — `gramps.gen.*` importing `gramps.gui.*` | mypy + import-time test failure; see [[16-guidelines]] §Source structure |
| Type regressions | `mypy` (enforced) |
| Backlink class-name comparison bug (`if cls is Person:` always `False`) | `example.gramps`-backed traversal test; [[16-guidelines]] §Runtime |
| DB-shape assumptions a stub hides | `example.gramps`-backed test |
| The specific bug a fix closed | the regression test (red→green) |

See [[09-debug]] for turning a reproduction script into one of these tests, and [[11-code-analysis]] for the static checkers (Black / mypy / pylint) that run before the suite.

## See also

- [[06-data-access]] — the DB-API patterns the `example.gramps`-backed tests exercise.
- [[09-debug]] — turning a repro into a regression test.
- [[11-code-analysis]] — Black, mypy, and pylint; the static gate around the suite.
- [[16-guidelines]] §Testing — the normative MUST/SHOULD rules this page is the how-to for.
- `gramps/AGENTS.md` §Testing / §Type Checking — the in-repo coding standard.
- [Mantis 12691](https://gramps-project.org/bugs/view.php?id=12691) — the submodule-binding trap a `tests/` package under core can hit.

<!--wiki:{{stub}}-->
