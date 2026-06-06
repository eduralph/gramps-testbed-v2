---
title: "Gramps 6.1 Wiki Manual - Core Development - Rules"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

Normative reference for **Gramps core** contributors. Conceptual / how-to material lives in the other section pages; this page enumerates the guidelines and is the one to cite in code review.

## Repository scope

- **This page applies to the core repository — [`gramps-project/gramps`](https://github.com/gramps-project/gramps).**
- The authoritative, in-repo coding standard for core is `gramps/AGENTS.md`. This page restates the parts code review enforces and adds the contributor-workflow rules that live outside that file.
- **When in doubt, the authoritative source wins and is what to check.** This page is a convenience restatement. Where it is silent, ambiguous, or disagrees with the in-repo sources on the *target branch* — `gramps/AGENTS.md`, `CONTRIBUTING`, the `po/`, `mypy.ini`, and CI config, plus a maintainer's ruling on the PR — those sources win. Verify against them rather than relying on this page from memory.

## Conventions

RFC 2119 keywords, with our short forms:

| Keyword | Meaning |
|---------|---------|
| **MUST** / **MUST NOT** | Required; a violation is a defect |
| **SHOULD** / **SHOULD NOT** | Strongly recommended; deviate only with a stated reason |
| **MAY** | Allowed |

Where a rule has a known origin — an upstream PR, a maintainer ruling, a Mantis bug, an in-repo standard — it's cited inline so the rule is auditable.

## Source structure

- **MUST**: code in `gramps.gen.*` does not import from any other Gramps submodule (`gramps.gui.*`, `gramps.plugins.*`, …). The `gen` submodule must remain self-contained — it is the headless, GUI-free core the rest of the program builds on. (`gramps/AGENTS.md` §Submodule Import Rules.)
- **MUST**: every new `.py` file carries a GPL-2.0-or-later license header with copyright, in the canonical block form. (`gramps/AGENTS.md` §File Headers.)
- **MUST**: edit core source on the checkout, never in an installed copy — run from source for development.
- **SHOULD**: prepend a class-header navigation comment to every class (including `unittest.TestCase` subclasses), in the boxed `#---` form. This is for navigation when several classes share a file, not documentation. (`gramps/AGENTS.md` §Class Headers; PR 2326 round 2.)

## Translation

The rules below are what code review enforces; the keyword/tooling details are in `gramps/AGENTS.md` §Internationalization and `po/`.

- **MUST**: wrap every user-visible string with `_()`. (`gramps/AGENTS.md` §Internationalization.)
- **MUST NOT**: wrap an f-string or `.format()` result in a translation function. `xgettext` cannot extract dynamically built strings.
  - **Bad:** `_(f"User {name}")`, `_("User {}".format(name))`
  - **Good:** `_("User %s") % name`
- **SHOULD**: use `ngettext(singular, plural, n)` for plural forms.
- **SHOULD**: use the alias `_(string, context)` rather than calling `pgettext(context, message)` directly. (`gramps/AGENTS.md` §Internationalization.)
- **SHOULD**: use `N_("…")` to mark a string for extraction without translating it at call time (e.g. module-level constants translated later when displayed).

## Runtime

- **MUST**: perform every database write inside a `DbTxn`:
  ```python
  with DbTxn(_("Adding example"), db) as trans:
      db.add_person(person, trans)
  ```
- **SHOULD**: prefer existing exceptions from `gramps.gen.errors` and `gramps.gen.db.exceptions` before inventing a new class. (`gramps/AGENTS.md` §Error Handling.)
- **SHOULD**: raise `HandleError` for invalid or missing handles. (`gramps/AGENTS.md` §Error Handling.)
- **SHOULD**: use handles (`PersonHandle`, etc.) for internal traversal; reserve Gramps IDs (`I0001`, …) for user-facing display. Handles are internal and stable; Gramps IDs are user-editable and rewritten in bulk by the Reorder Gramps IDs tool.
- **SHOULD**: compare backlink class names by string. `db.find_backlink_handles(handle)` yields `(class_name, handle)` tuples where `class_name` is `"Person"` / `"Family"` / … as a `str`, not the Python class — `if cls is Person:` always evaluates `False`.
- **SHOULD**: use a module-level logger (`LOG = logging.getLogger(__name__)`); **MUST NOT** use `print()` for diagnostic output. (`gramps/AGENTS.md` §Logging.)
- **MAY**: introduce a new exception class only when none of the existing ones accurately represent the error condition. (`gramps/AGENTS.md` §Error Handling.)

## Testing

- **MUST**: use stdlib `unittest` — never `pytest`. (`gramps/AGENTS.md` §Testing.)
- **MUST**: name test files with the **`_test.py` suffix** (e.g. `mymodule_test.py`) and place them in a **`test/` package (singular)** alongside the module being tested — e.g. `gramps/gui/test/`, `gramps/gen/lib/test/`. CI discovers tests with `-p "*_test.py"`. (`gramps/AGENTS.md` §Testing.)
- **MUST NOT**: create a `tests/` directory (plural) anywhere under the core `gramps/` package. It puts the test where the core runner (`-p "*_test.py"`) won't find it, and a `tests/` package under core can trip the [Mantis 12691](https://gramps-project.org/bugs/view.php?id=12691) submodule-binding trap. **Core uses `test/` (singular) + `<module>_test.py`.** (gramps-testbed `docs/INTEGRATION.md` §3; recorded from issue 13636 until carried upstream.)
- **MUST**: changes pass `mypy` static analysis (`mypy` reads `mypy.ini`: `files = ./gramps, ./test`, `*.gpr.py` excluded). (`gramps/AGENTS.md` §Type Checking.)
- **SHOULD**: write a test for each distinct flow of logic — happy path, error cases, edge cases. (`gramps/AGENTS.md` §Testing.)
- **SHOULD**: ship a regression test with every bug fix that **fails pre-fix and passes post-fix**. Doc-only PRs are the only exception.

Running the suite:

```bash
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

## Coding style

The full standard — Black, Python 3.10+ type hints, Sphinx docstrings, import grouping with comment headers, class-header navigation comments, `cb_` callback prefix — is `gramps/AGENTS.md`, the native in-repo coding standard for core. The rules below are what code review enforces.

- **MUST**: format every changed `.py` file with **Black** before committing; CI enforces it on every PR. (`gramps/AGENTS.md` §Black.)
  ```bash
  git diff --name-only --diff-filter=ACMR origin/master...HEAD | grep '\.py$' | xargs --no-run-if-empty black
  ```
- **MUST**: type-hint all functions and methods, using Python 3.10+ syntax — `X | None` over `Optional[X]`, `X | Y` over `Union[X, Y]`, `list[X]` / `dict[K, V]` / `tuple[X, ...]` over the `typing` equivalents. (`gramps/AGENTS.md` §Type Hints.)
- **SHOULD**: use handle / ID types from `gramps/gen/types.py` (`PersonHandle`, `PersonGrampsID`, …) rather than bare `str`. (`gramps/AGENTS.md` §Type Hints.)
- **SHOULD**: docstring all functions and methods in Sphinx format (`:param:` / `:type:` / `:returns:` / `:rtype:`). (`gramps/AGENTS.md` §Docstrings.)
- **SHOULD**: organise imports into three comment-headed sections — *Python modules*, *Gramps modules*, *Gramps specific* — each separated by a blank line. (`gramps/AGENTS.md` §Import Grouping.)
- **SHOULD**: prefix callback names `cb_*`. (`gramps/AGENTS.md` §Callbacks.)
- **SHOULD**: keep code PEP 8 compatible except where it conflicts with Black — Black wins. 4-space indentation, never TABs. (`gramps/AGENTS.md` §PEP 8 and Indentation.)
- **SHOULD**: run pylint on new code — aim for ≥ 9 and don't reduce the overall score — but never at the expense of clarity or any other rule here. (`gramps/AGENTS.md` §Pylint.)

## Adding and removing Python files

When a core PR adds or removes a `.py` file:

- **MUST**: update `po/POTFILES.in` (file contains translatable strings) or `po/POTFILES.skip` (no translatable strings; deliberately excluded). (`gramps/AGENTS.md` §Translation Files.)
- **MUST**: remove the reference from **both** `po/POTFILES.in` and `po/POTFILES.skip` when a file is deleted.

Local check:

```bash
PYTHONPATH=../../gramps python po/test/po_test.py
```

(Core maintains these lists by hand.)

## Contributor workflow

- **MUST**: one logical fix per PR. Bundling hides mistakes.
- **MUST**: target **`maintenance/gramps61`** — the current production branch — which the maintainer forward-merges to `master`. Do **not** PR `master` directly; `master` is feature-only, and routing fixes through the maintenance branch gets them to users sooner. Only genuinely new-feature work targets `master`. (`doc16:113`; jralls on gramps#2298; gramps-testbed `docs/INTEGRATION.md` §2.)
- **MUST**: branch from `upstream/<base>`, not the fork's tracking copy — fork bases drift (e.g. gramps PRs 2315/2316 carried a stray `AGENTS.md` from the fork). (`docs/INTEGRATION.md` §2.)
- **MUST**: a bug-fix PR includes a regression test, or an explicit "no test because X" rationale plus a manual repro. "Add the test later" is not an option.
- **MUST**: structure the PR body as **Root cause / Fix / Verified against / Test**, citing `path:lines` on the branch the PR targets (`maintenance/gramps61`).
- **MUST**: reference the Mantis bug — gramps core PRs end **both** the PR body **and** the commit message with `Fixes #NNNN` (no URL, no padding; PR 2322 is the canonical example). The older URL-at-top form on PR 2317 is the outdated pattern.
- **MUST NOT**: merge across branches. Rebase rather than merge — PRs with merge commits are rejected upstream. (`gramps/AGENTS.md` §Branch merges.)
- **MUST NOT**: cosmetically update in-flight upstream PRs. Parity, "rebase is clean," and "branch is behind" are not reasons to force-push. Push only when a specific correctness issue needs fixing.
- **SHOULD**: before writing any fix, check upstream isn't ahead — merged history on `maintenance/gramps61` **and** `master`, *plus* closed and rejected PRs on the *affected file path* (not just the bug number). A closed-unmerged PR with the same fix shape is the maintainer's "no." Search by file path, not bug-ID or keyword. (`docs/INTEGRATION.md` §5.)
- **SHOULD**: if a PR already exists for the bug, verify it instead of duplicating. Merged → confirm-and-close; open → review and defer to the maintainer; closed → treat as the maintainer's "no."
- **SHOULD**: reproduce against `example.gramps` first — it's the canonical fixture and "couldn't reproduce" is the most common reason a fix stalls in triage.
- **MAY**: a maintainer's explicit base-branch request on a specific PR overrides the default targeting. (`doc16:114`; e.g. Nick-Hall on gramps#2299.)
- **MAY**: open as a draft PR for early review or to publish work-in-progress; mark ready when the change is complete and you've re-read the diff with fresh eyes.

## Verification before commit

- **MUST**: find a test procedure before committing — local run, dry-run, snippet check. Never commit untested changes.
- **MUST**: treat a green mechanical check (Black clean, `mypy` exits 0, `git cherry-pick` applies, build green, `py_compile` exits 0) as evidence of *that narrow check*, not of correctness. Name what the check verified and what it left unverified. "Cherry-pickable" means *remains correct on the target branch*, not *applies without conflict*.
- **MUST**: after pushing a PR branch, watch the PR's CI checks until they finish (e.g. `gh pr checks <PR#> --watch`). Local pre-commit catches static checks only; test failures surface in CI's actual unit-test run.

## Commit messages

Commit messages are parsed by scripts that update Mantis BT and generate the ChangeLog / News files for releases. Formatting must be followed precisely. (`gramps/AGENTS.md` §Commit Messages.)

- **MUST**: the first line is a short summary, **≤ 70 characters**.
- **MUST**: the description is separated from the summary by a single blank line, and wrapped at **80 characters**.
- **MUST**: describe the change from the user's perspective. Don't recap the diff — `git diff` exists.
- **SHOULD**: use complete sentences in the description.
- **MUST**: reference another commit by its **full hash**, not a short hash. GitHub auto-hyperlinks full hashes; short hashes do not link.
- **MUST**: the Mantis trailer is on the **last** line of the commit message, separated from the description by a single blank line.

Example:

```
Fix crash when opening event editor with empty date field.

When a date field was left blank, the event editor raised an unhandled
AttributeError. This change adds a guard so the field is treated as an
empty string instead.

Fixes #12345.
```

### Mantis trailer keywords

To **resolve** a bug (closes it on commit):

```
Fixes #12345
Fixed #12345
Resolves #12345
Resolved #12345
Fixes #12345, #12346
```

To **link** to a bug (cross-reference without closing):

```
Bug #12345
Issue #12345
Report #12345
Bugs #12345, #12346
```

Use the `#NNNN` form (no leading zeros). Bare numbers and URLs both miss the auto-link. Note this is the opposite of the convention *inside* MantisBT itself, where bare numbers are preferred; here, in Git commit messages and GitHub PR bodies, `#NNNN` is what hooks the MantisBT scripts.

For the trailer to wire up on Mantis, the Git **author** or **committer** must be a developer on the Mantis bug tracker — the Git name must match the Mantis username or real name, or the Git email must match the Mantis email.

## See also

- `gramps/AGENTS.md` — the native, in-repo coding standard for core (the source this page restates).
- [gramps-project/gramps `CONTRIBUTING`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/CONTRIBUTING) — pointers into the upstream developer documentation.
- [Portal:Developers](https://gramps-project.org/wiki/index.php?title=Portal:Developers) — upstream developer portal.
- [Committing policies](https://www.gramps-project.org/wiki/index.php/Committing_policies) — upstream's commit-message + Mantis-trailer rules.

<!--wiki:{{stub}}-->
