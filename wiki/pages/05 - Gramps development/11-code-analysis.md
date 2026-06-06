---
title: "Gramps 6.1 Wiki Manual - Core Development - Code analysis"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

## Overview

What automated checks run against **gramps core** code, locally and in CI, and how to keep a core PR passing them. The goal is "PR opens green" — every gate below catches a class of issue more cheaply than a maintainer review round, and most of them also have a fast local form you can run before pushing.

This page is how-to / explanatory. The normative MUST/SHOULD form of these rules lives in [[16-guidelines]] (§Coding style, §Adding and removing Python files, §Verification before commit); the native in-repo coding standard is `gramps/AGENTS.md`. Cite those, not this page, in review.

Two layers of checks matter, and they are not the same thing:

| Layer | Examples | Who decides |
|-------|----------|-------------|
| **CI-enforced** — a red check blocks merge | Black, `mypy`, the unit-test run, the POTFILES check | deterministic; the bot |
| **Reviewer judgment** — guidance, not a gate | pylint ≥ 9, import grouping, class headers, `cb_` prefix, GNOME HIG compliance, `po/test/po_test.py` | a maintainer on the PR |

Knowing which layer a rule lives in tells you whether a local "it's clean" actually clears the bar. A green Black run proves the diff is Black-clean — nothing more. See [[16-guidelines]] §Verification before commit on not mistaking a green mechanical check for correctness.

## What CI enforces

Core CI runs as two GitHub Actions workflows. Confirmed on `maintenance/gramps61`:

| Check | Workflow | Step | Blocks merge |
|-------|----------|------|--------------|
| Black formatting | `.github/workflows/black.yml` | `uses: psf/black@stable` | yes |
| `mypy` static types | `.github/workflows/gramps-ci.yml:71` | `mypy` (reads `mypy.ini`) | yes |
| Unit-test suite | `.github/workflows/gramps-ci.yml:75` | `python3 -m unittest discover -p "*_test.py"` | yes |
| POTFILES check | `.github/workflows/gramps-ci.yml:80` | `intltool-update -m` | yes |

Everything else on this page is reviewer judgment. Local pre-commit (where you install it) covers the static checks only; test failures and POTFILES drift surface in the CI run, so watch the PR's checks after pushing (`gh pr checks <PR#> --watch`) — [[16-guidelines]] §Verification before commit.

## Black

[Black](https://black.readthedocs.io/) is an opinionated Python formatter. The lint workflow is bare `psf/black@stable` (`black.yml`), which checks the tree; a violation fails the **Lint** job and blocks the merge. CI is the authority — use the same Black version locally as CI to avoid a clean-locally / red-in-CI surprise.

Format only the files your PR touches, before committing — the changed-files invocation from `gramps/AGENTS.md` §Black:

```bash
git diff --name-only --diff-filter=ACMR origin/master...HEAD \
  | grep '\.py$' \
  | xargs --no-run-if-empty black
```

To preview what Black *would* change without rewriting, add `--check --diff`:

```bash
git diff --name-only --diff-filter=ACMR origin/master...HEAD \
  | grep '\.py$' \
  | xargs --no-run-if-empty black --check --diff
```

The traps are small diffs that look harmless: a mid-import blank line, a multi-line `.append()` collapsed onto one line, a trailing-comma rewrite. Black's failures are often pure whitespace and invisible in a casual read — run it rather than eyeballing.

## `mypy`

Core CI runs `mypy` with no arguments (`gramps-ci.yml:74`); it reads configuration from `mypy.ini` at the repo root. Type errors block the build. Verified `mypy.ini` contents on `maintenance/gramps61`:

```ini
[mypy]
files = ./gramps, ./test
exclude = .*gpr\.py$

[mypy-berkeleydb.*]
ignore_missing_imports = True
# … one such stanza per untyped third-party dependency
# (gi, cairo, PIL, lxml, icu, orjson, jsonschema, pycountry, …)
```

Two facts from that file are load-bearing:

- **`files = ./gramps, ./test`** — `mypy` checks the package *and* the top-level `test/` tree. A type error in a test counts.
- **`exclude = .*gpr\.py$`** — `*.gpr.py` plugin-registration files are excluded. They execute in an injected-name scope (`register`, `_`, `MODULE_VERSION` are bound by the loader, not imported) and would otherwise flood `mypy` with undefined-name errors.

Run it from the repo root:

```bash
mypy
```

A green `mypy` proves the annotations are internally consistent — it does not prove the function is correct. Use the modern hint shapes the standard mandates (`X | None`, `list[X]`, handle/ID types from `gramps/gen/types.py`); [[16-guidelines]] §Coding style has the normative list.

### `mypy` + discipline protect `gen` self-containment

`gramps.gen.*` MUST NOT import from any other Gramps submodule (`gramps.gui.*`, `gramps.plugins.*`, …) — `gen` is the headless, GUI-free core the rest of the program builds on (`gramps/AGENTS.md` §Submodule Import Rules; [[16-guidelines]] §Source structure). There is no dedicated CI rule that asserts this; it is held by two forces working together:

- **`mypy`** type-checks the whole tree under the same import graph the runtime uses, so a `gen → gui` import that drags GUI-only symbols into `gen` tends to surface as a type or resolution error rather than passing silently.
- **Reviewer discipline** is the real guard. A new `from gramps.gui...` inside `gramps/gen/` is a review reject regardless of whether the type checker happened to catch it.

Treat the rule as a hard MUST you self-enforce, not as something the gate will reliably catch for you.

## The unit-test suite

CI builds a wheel, then discovers and runs tests (`gramps-ci.yml:75`). Test failures block the merge:

```bash
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

The discovery pattern `*_test.py` is why core test files use the **`_test.py` suffix** and live in a **`test/` package (singular)** beside the module. Getting this wrong puts the test where the runner can't see it; the test layout and its rationale are in [[08-testing]] and [[16-guidelines]] §Testing. A bug-fix PR ships a regression test that fails pre-fix and passes post-fix.

## pylint — aim, not gate

`gramps/AGENTS.md` §Pylint and the upstream programming guidelines ask for **pylint ≥ 9 on new files**, and "changes to existing files shall not reduce the pylint score." This is **not gated by CI** — no workflow runs pylint. It is reviewer guidance.

The explicit ceiling on it (from `gramps/AGENTS.md` §Pylint): chasing the score must **never** come at the expense of code clarity, Black formatting, or any other rule in the standard. If a pylint suggestion conflicts with Black, Black wins; if it makes the code less clear, leave the warning. A lint flag is a symptom, not the bug — read the enclosing function before silencing it; an undefined name in shipping code usually means dead or broken code, not a missing import.

Run it from the `gramps` directory so import resolution treats the tree as a package; add `PYTHONPATH` if imports still fail:

```bash
PYTHONPATH=plugins/lib/ pylint --reports=n gramps/plugins/mapservices/googlemap.py
```

One convenience interaction: pylint does not raise `W0613: Unused argument` for methods named `cb_*`, which suits GTK signal handlers that receive arguments they ignore — see [Callbacks](#callbacks).

## PEP 8, where Black wins

Core code SHOULD be [PEP 8](https://www.python.org/dev/peps/pep-0008/) compatible — **except where PEP 8 conflicts with Black, in which case Black takes precedence** (`gramps/AGENTS.md` §PEP 8 and Indentation). You never resolve a PEP 8 / Black disagreement by hand; you run Black and accept its output. Concretely, the deltas you'll meet:

| Topic | PEP 8 says | What ships in core |
|-------|-----------|--------------------|
| Line length | ≤ 79 | Black's default (88), because Black sets it |
| String quotes | either | Black normalises to double quotes |
| Trailing commas, blank lines, wrapping | various | whatever Black produces |
| Indentation | 4 spaces | 4 spaces, never TABs |
| Space after comma | not explicit | required — a local addition PEP 8 doesn't mandate |

The space-after-comma rule and the no-TABs rule are the two PEP-adjacent conventions Black does *not* enforce for you, so they remain things a reviewer watches. TABs are forbidden in Python (4-space indentation); where TABs are unavoidable, as in Makefiles, they are 8-space stops at columns 9, 17, 25, … — do not set your editor's TAB stops to 4, which hides the problem rather than fixing it.

## Reviewer-judgment conventions

The rules below are not gated; a maintainer checks them by reading the diff. New code follows them; existing non-conforming code is left as-is until touched.

### Import grouping

Imports are organised into **three comment-headed sections**, each separated by a blank line (`gramps/AGENTS.md` §Import Grouping). The headers, with the boxed form core uses:

```python
# -------------------------------------------------------------------------
#
# Python modules
#
# -------------------------------------------------------------------------
import os
import logging

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
from gi.repository import Gtk

# -------------------------------------------------------------------------
#
# Gramps specific
#
# -------------------------------------------------------------------------
from gramps.gen.db.base import DbReadBase
from .mymodule import MyClass
```

Include only the sections that apply (a `gen` module with no GTK import omits the middle one). Within a submodule, relative imports (`.`) for the submodule's own modules and absolute `gramps.` imports for other submodules — never the reverse.

### Class-header nav comments

Every class — including `unittest.TestCase` subclasses — carries a boxed navigation comment so the class is findable when several share a file (`gramps/AGENTS.md` §Class Headers; PR 2326 round 2, cited in [[16-guidelines]] §Source structure):

```python
# ------------------------------------------------------------
#
# MyClass
#
# ------------------------------------------------------------
class MyClass:
    ...
```

This is navigation, not documentation — the Sphinx docstring does the documenting.

### `cb_` callbacks

Callback names are prefixed `cb_` (`gramps/AGENTS.md` §Callbacks):

```python
def cb_save(self, *args):
    ...
```

Besides signalling intent, the prefix suppresses pylint's `W0613: Unused argument` for the GTK signal handlers that get arguments they don't use.

## POTFILES: `po/test/po_test.py`

When a core PR adds or removes a `.py` file, the file must be listed in exactly one of `po/POTFILES.in` (contains translatable strings) or `po/POTFILES.skip` (deliberately none); a deleted file is removed from **both**. Core maintains these lists by hand — there is no autogeneration. ([[16-guidelines]] §Adding and removing Python files; `gramps/AGENTS.md` §Translation Files. Translation mechanics: [[12-internationalization]].)

There are two distinct checks, at two layers:

- **Developer-local** — the in-repo `po/test/po_test.py` (verified present) cross-checks `POTFILES.in` / `POTFILES.skip` against the tree: it flags a file that has translatable strings but is missing from `POTFILES.in`, a `POTFILES.in` entry whose file no longer exists, and similar drift. Run it before pushing:

  ```bash
  PYTHONPATH=../../gramps python po/test/po_test.py
  ```

- **CI-enforced** — the workflow's "POTFILES check" step (`gramps-ci.yml:80`) runs `intltool-update -m` and fails on a non-empty `missing` list. This is the gate that blocks merge; the local `po_test.py` is the faster, earlier-warning form you run yourself.

## UI-style review (GNOME HIG)

For changes to `gramps.gui.*`, code review adds a **UI-style dimension** that no static tool can check — it is pure reviewer judgment, grounded in the project's [UI style](wiki:UI_style) page and the [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/index.html). The recurring concerns a reviewer raises:

- **Follow the GNOME HIG** unless you can justify a deviation, and get buy-in from other developers before deviating.
- **Don't use colour to carry meaning** — themes vary (your dark-blue text on someone's dark-blue background) and many users are colour-blind. Use a different mechanism (e.g. italics, as the Person view does for a substituted date).
- **Be consistent** — reuse an existing mechanism for an existing concept rather than inventing a parallel one.
- **Buttons are for routine actions** (Add, Delete, Edit); obscure or rare actions belong in a right-click context menu.
- **Editors edit, they don't display** — Edit Person / Edit Family are data-entry dialogs; show derived or related data via a Quick Report, not in the editor, and never show derived data the user can't edit.
- **Set invalid controls insensitive** rather than letting the user click and wonder.
- **Edit each datum in exactly one place**, or two dialogs will overwrite each other.
- **Resist new options** — they confuse users and add maintenance; treat adding one as a last resort.

These are SHOULD-grade and argued on the PR, not asserted by a check — but a HIG objection from a maintainer is as blocking in practice as a red CI light.

## Run it all locally before pushing

A pragmatic pre-PR checklist for a core change:

```bash
# CI-enforced gates — these block merge if they fail:
git diff --name-only --diff-filter=ACMR origin/master...HEAD \
  | grep '\.py$' | xargs --no-run-if-empty black     # Black
mypy                                                  # static types
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
PYTHONPATH=../../gramps python po/test/po_test.py     # POTFILES (local form)

# Reviewer-judgment — clean these to save a review round:
PYTHONPATH=plugins/lib/ pylint --reports=n <changed-file>.py   # aim >= 9
# eyeball: import sections, class headers, cb_ prefixes, GNOME HIG
```

After pushing, watch the PR's CI until it finishes — local checks don't run the full test suite the same way (`gh pr checks <PR#> --watch`). See [[16-guidelines]] §Verification before commit.

## See also

- [[16-guidelines]] — the normative MUST/SHOULD rules these checks enforce (§Coding style, §Adding and removing Python files, §Verification before commit).
- [[08-testing]] — the unit-test conventions the `*_test.py` gate discovers.
- [[12-internationalization]] — the `_()` / `ngettext` rules and the POTFILES tooling behind the check above.
- `gramps/AGENTS.md` — the native in-repo coding standard for core (the source this page is built on).
- [Programming guidelines](wiki:Programming_guidelines), [UI style](wiki:UI_style) — the upstream wiki pages this page restates for contributors.

<!--wiki:{{stub}}-->
