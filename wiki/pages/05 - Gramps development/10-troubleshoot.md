---
title: "Gramps 6.1 Wiki Manual - Core Development - Triage & troubleshooting"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

## Overview

Two halves, both written for a contributor working on
[`gramps-project/gramps`](https://github.com/gramps-project/gramps). The first
half is the bug tracker from a developer's vantage: the MantisBT status workflow,
and how to reproduce a report against `example.gramps` *before* you touch code —
because "couldn't reproduce" is the most common reason a fix stalls in triage.
The second half is a symptom-first table of the failure modes that bite core
contributors: read it sideways, jump to the symptom that matches what you're
seeing, follow the link out for the fix in depth.

For technique-level coverage (pdb, gdb, `python -m trace`, profiling) see
[[09-debug]]. For the test conventions that catch most of these before a user
ever sees them, see [[08-testing]]. For the normative MUST/SHOULD rules this page
defers to throughout, see [[16-guidelines]] — that page is the reference to cite
in code review; this page is the how-to.

## Part A — Triage and the bug tracker

The Gramps issue tracker is MantisBT at <https://gramps-project.org/bugs>. Filing
mechanics — login, choosing a project, the report form — are covered upstream in
[Using the bug tracker](wiki:Using_the_bug_tracker) and
[How to create a good bug report](wiki:How_to_create_a_good_bug_report). This
section is the developer's read of the same tracker: what the status states mean
when you pick up a report, and what to do before you write a line of code.

### Reproduce against `example.gramps` first

Fixing a bug always starts with reproducing it, and most of the time the
developer does not succeed at that — which is precisely what triage exists to
fix. The single most useful thing you can do with a fresh report is reproduce it
against the canonical fixture, [`example.gramps`](wiki:example.gramps), and write
down the exact steps.

`example.gramps` is the fixture the whole project shares (it ships in the
checkout at `example/gramps/example.gramps`, and the test copy lives at
`data/tests/example.gramps`). Reproducing against it removes the reporter's tree,
their OS, and their installed plugins from the equation, leaving only Gramps. A report
that says "reproduced on `example.gramps`, steps 1–4 below" is one a developer
can pick up immediately; a report that needs the reporter's private tree to
reproduce can sit in *feedback* for months.

```bash
# Run from a source checkout so you can edit + retest in one loop.
# GRAMPS_RESOURCES must point at the checkout (see Part B) or Gramps exits.
GRAMPS_RESOURCES=. python3 Gramps.py --debug=.
```

Create a new family tree, import `example.gramps`, and walk the report's steps.
If it reproduces, note the steps in the ticket. If it does **not**, say so —
spell out the steps you took and the version you used; that is itself a triage
result, and it moves the ticket toward *feedback* rather than leaving it stale.
If you hit a *different* bug along the way, file a separate report (one problem
per report — [[16-guidelines]] §Contributor workflow).

Reproduce against the branch the fix will target — **`maintenance/gramps61`**,
the current production branch — and, where a bug may be master-only, also against
`master`. Branch-target rules are normative in [[16-guidelines]] §Contributor
workflow and in [docs/INTEGRATION.md §2].

### The MantisBT status workflow

![[_media/Mantisbt-valid-status-states.png|MantisBT status transitions]]

A ticket moves through a small set of statuses. As a developer or triager you
will mostly be the one *advancing* them:

| Status | What it means | When you set it |
|---|---|---|
| **new** | Filed, not yet looked at. | Default on submission. Don't leave a ticket here once it's been examined. |
| **acknowledged** | Not spam, has enough to start an investigation — even if it may turn out to be the submitter's environment. | You've read it and it's a real, actionable report. |
| **confirmed** | Someone other than the reporter reproduced it (or reasoned about its validity). For a feature request, that it's a legitimate possibility — not a promise to build it. | You reproduced it, ideally against `example.gramps`. |
| **assigned** | Someone is actively working on it. Remove the assignment if you stop. | You (or a dev) picks it up; pair with a PR that references the bug. |
| **feedback** | Blocked waiting on the reporter (too little information, needs a repro, needs their tree). | You can't proceed without input. |
| **resolved** | Fixed; the change is committed to the corresponding branch. | Only after the fix is committed — see below. |
| **closed** | Won't-fix, duplicate, no-longer-applies, EOL version, or several-issues-in-one. | Duplicates, stale tickets, multi-issue reports (ask for one ticket per issue). |

A few rules that trip up new triagers:

- **Don't mark a maintenance-branch bug *resolved* until the change is actually
  committed to that maintenance branch.** It is then the developer's
  responsibility to make sure the change is also merged forward to `master`. (For
  core, that forward-merge is the maintainer's standing flow from
  `maintenance/gramps61` → `master`.)
- **Set "Fixed in version"** to the next release that branch will produce, so the
  ticket appears correctly on that project's roadmap.
- If you fix a bug scheduled for a later milestone before an earlier one ships,
  adjust the target-release field *before* marking it resolved, or the roadmap
  display goes wrong.
- **Link the fix.** When resolving, add a note with the full Git commit hash. In
  a Git commit message / GitHub PR body the `Fixes #NNNN` trailer wires the
  ticket up automatically (see below); inside a Mantis note, `#NNNN` refers to
  another Mantis ticket, and a core PR is linked with the `p:gramps:nnnn:`
  shorthand. (Trailer mechanics: [[16-guidelines]] §Commit messages.)

If you lack MantisBT permissions to change a status, ask in the developers
section of the [Gramps forum](https://forum.gramps-project.org/) for someone to
set it; once you've done enough triage, ask there for the permission yourself.

### What makes a report a developer can act on

The qualities the tracker asks reporters for are the same ones that decide
whether *you* can pick a ticket up:

- **Precise and clear** — step-by-step reproduction, so someone else can follow
  it.
- **One problem per report** — multi-issue tickets get closed with a request to
  split them.
- **Reproducible against `example.gramps`** where at all possible (see above).
- **The Gramps version**, and the project area it was filed under — that area
  ("Gramps 6.1", "Gramps 5.2", master-only) is what drives the branch a fix must
  target ([docs/INTEGRATION.md §1–2]).

The contributor pre-flight before you start coding — *check upstream isn't
already ahead, search by affected file path not bug number, don't duplicate an
in-flight or rejected PR* — is normative in [[16-guidelines]] §Contributor
workflow; reproduce-first is the SHOULD that opens it.

## Part B — Common core-dev failure modes

Symptom → cause → fix. Each entry links out to the chapter with the fix in depth.

### Plugins and discovery

#### "My new plugin doesn't appear in any menu."

Plugin discovery executes every `.gpr.py` it finds at startup; if registration
fails the plugin is silently dropped from the catalog. Three usual causes:

| Cause | Signal | Fix |
|---|---|---|
| `.gpr.py` raised during `exec`. | `ERROR: Failed reading plugin registration <file>` printed at startup, followed by the traceback. (`gramps/gen/plug/_pluginreg.py:1438-1452`, `maintenance/gramps61`.) | Launch from a terminal and read the traceback; fix the `SyntaxError` / import error in the `.gpr.py`. |
| `gramps_target_version` invalid for this Gramps. | `ERROR: Plugin file <file> has a version of "X" which is invalid for Gramps "6.1.0".` (`_pluginreg.py:1463-1476`.) | Set the target version to match the branch you're building against. |
| Missing dependency declared in the registration. | The entry is filtered out by the requirements check (`_pluginreg.py:1477` onward). | Provide the dependency, or guard the feature. |

For a built-in core plugin (under `gramps/plugins/`) the registration file lives
beside the module; for the in-tree mechanics see the plugin chapters. The fastest
isolation check is to run Gramps from a terminal — registration errors go to the
console, not a dialog.

#### "I edited the installed copy and nothing changed."

For core, **edit the checkout and run from source** — never an installed copy.
This is a MUST in [[16-guidelines]] §Source structure. Running from source
(`GRAMPS_RESOURCES=. python3 Gramps.py`) means your edits take effect on the next
launch with no copy step.

### Imports and the gen boundary

#### "A `gramps.gen.*` change pulls in GUI and breaks headless / tests."

`gramps.gen.*` is the headless, GUI-free core that the rest of the program and the
test suite build on. It **must not import from any other Gramps
submodule** (`gramps.gui.*`, `gramps.plugins.*`, …). Adding such an import makes
`gen` un-importable wherever GTK isn't present — CI's unit run, a headless
server, Gramps Web — often as an `ImportError` deep in an unrelated test.

This rule is a MUST in [[16-guidelines]] §Source structure, sourced to
`gramps/AGENTS.md` §Submodule Import Rules. There is no automated import-rule
test in the suite, so it is enforced by review and by the failure it causes;
keep new `gen` code dependency-free and push the GUI-needing part up into
`gramps.gui.*`.

```python
# In gramps/gen/... — WRONG: drags GTK into the headless core
from gramps.gui.dialog import ErrorDialog

# RIGHT: raise/return from gen; let the gui layer present it
from gramps.gen.errors import HandleError
raise HandleError(_("…"))
```

See also [[08-testing]] — the unit suite runs headless, so a stray GUI import in
`gen` surfaces there first.

#### "`from <Pkg> import <Pkg>` binds the submodule, not the class."

The namespace-package trap: importing a package gives you the package, not the
like-named module inside it. Where it bites in core: a **`tests/`** (plural)
package placed under the core `gramps/` tree can trip exactly this — Mantis
[12691](https://gramps-project.org/bugs/view.php?id=12691) is the canonical case
— which is one reason core uses `test/` (singular), never `tests/`. Use the
explicit submodule form:

```python
from MyPkg.MyPkg import MyClass   # binds the class, not the package
```

### Database access

#### "Iterating the DB raises `KeyError` halfway through."

The tree holds a reference to a handle that no longer resolves — real data has
dangling references that a fixed test set doesn't. Guard every dereference:

```python
event = db.get_event_from_handle(handle)
if event is None:
    continue   # skip the dangling reference
```

[[16-guidelines]] §Runtime: raise/expect `HandleError` for invalid or missing
handles, and use handles (not Gramps IDs) for internal traversal.

#### "`isinstance` against a backlink never matches."

`db.find_backlink_handles(handle)` yields `(class_name, handle)` tuples whose
first element is the class **name as a string** (`"Person"`, `"Family"`, …), not
the Python class. `if cls is Person:` is always `False`. Compare the string:

```python
for type_name, h in db.find_backlink_handles(handle):
    if type_name == "Person":
        ...
```

This is a SHOULD in [[16-guidelines]] §Runtime.

### CI: static checks (mypy, Black)

#### "Black CI is red on my PR."

Core enforces **Black** in CI (`.github/workflows/black.yml`, `maintenance/gramps61`).
Every changed `.py` file MUST be Black-formatted before commit
([[16-guidelines]] §Coding style):

```bash
git diff --name-only --diff-filter=ACMR origin/master...HEAD \
  | grep '\.py$' | xargs --no-run-if-empty black
```

#### "mypy CI is red on my PR."

Core enforces **mypy**. CI runs it
(`.github/workflows/gramps-ci.yml:71-74`) using `mypy.ini`, which sets
`files = ./gramps, ./test` and excludes `*.gpr.py`
(`mypy.ini:1-3`, `maintenance/gramps61`). Run it locally before pushing:

```bash
mypy
```

Type-hint all new functions with Python 3.10+ syntax (`X | None`, `list[X]`),
per [[16-guidelines]] §Coding style.

### Tests

#### "`Resource Path … is invalid` / Gramps exits on import in a test."

The test environment can't find the Gramps resources, so resource
initialization calls `sys.exit(1)` after logging
`Resource Path %s is invalid` (`gramps/gen/utils/resourcepath.py:104-106`,
`maintenance/gramps61`). The fix is to point `GRAMPS_RESOURCES` at the checkout
root before running anything — it's the first thing `ResourcePath` consults
(`resourcepath.py:79-81`), and without it a source checkout falls back to
`build/share`, which usually doesn't exist:

```bash
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

This is the canonical suite invocation in [[16-guidelines]] §Testing.

#### "My test isn't discovered / I created a `tests/` folder."

Core test layout is **`test/` (singular) + `<module>_test.py` (suffix)** beside
the module — e.g. `gramps/gen/lib/test/`. CI discovers with `-p "*_test.py"`.
There are 30 such `test/` packages under `gramps/` on `maintenance/gramps61` and
**zero** `tests/` packages. A `tests/` (plural) directory with `test_*.py`
(prefix) files puts your test where the runner won't find it, and can trip the
Mantis 12691 trap above.

> **Core = `test/` package (singular) + `<module>_test.py` (suffix).**

Normative in [[16-guidelines]] §Testing (MUST / MUST NOT) and
[docs/INTEGRATION.md §3]. Ship a regression test that fails pre-fix and passes
post-fix; see [[08-testing]].

#### "Local pre-commit passed but CI is red."

Pre-commit / local static checks catch formatting and types, not behaviour. A
test failure — an import that breaks at module load, a `gen`→gui leak, a
resource-path issue — surfaces only in CI's actual `unittest` run. After pushing,
watch the checks finish:

```bash
gh pr checks <PR#> --watch
```

A green mechanical check verifies *that narrow check*, not correctness
([[16-guidelines]] §Verification before commit).

### Translation (i18n) failures in CI

#### "I added/removed a `.py` file and the po check fails."

Core maintains `po/POTFILES.in` (files with translatable strings) and
`po/POTFILES.skip` (files deliberately excluded) **by hand**. Adding a `.py`
file means adding it to one of the two; deleting one means removing it from
**both**. Check locally:

```bash
PYTHONPATH=../../gramps python po/test/po_test.py
```

MUST in [[16-guidelines]] §Adding and removing Python files.

#### "`xgettext` can't extract my string."

Don't wrap a dynamically built string in `_()` — `xgettext` extracts the literal,
not the runtime value:

```python
_(f"User {name}")            # WRONG — nothing to extract
_("User %s") % name          # RIGHT
```

Wrap user-visible strings with `_()`; use `ngettext` for plurals and the
`_(string, context)` alias over `pgettext`. [[16-guidelines]] §Translation.

### Pull-request shape

#### "My PR sits without review / was retargeted."

Core PRs target **`maintenance/gramps61`**, not `master` (`master` is
feature-only; fixes ride the maintenance branch and forward-merge from there).
Branch from `upstream/<base>`, not your fork's tracking copy, which drifts.
Structure the body as **Root cause / Fix / Verified against / Test**, cite
`path:lines` on the target branch, and end **both** the PR body and the commit
message with `Fixes #NNNN`. All normative in [[16-guidelines]] §Contributor
workflow and §Commit messages; branch map in [docs/INTEGRATION.md §2].

#### "My PR was rejected as a duplicate."

Someone — possibly the maintainer, in a previously *closed* PR — already had a
fix for that area. Before writing one, check merged history on
`maintenance/gramps61` **and** `master`, plus closed/rejected PRs, searching by
**affected file path** rather than bug number or keyword. A closed-unmerged PR of
the same shape is the maintainer's "no." [[16-guidelines]] §Contributor workflow;
[docs/INTEGRATION.md §5].

## See also

- [[09-debug]] — pdb / gdb / `python -m trace` / profiling: the techniques for
  reproducing what the symptoms above describe.
- [[08-testing]] — the test conventions (`test/` + `*_test.py`, `GRAMPS_RESOURCES`)
  that catch most of these before they reach a user.
- [[16-guidelines]] — the normative MUST/SHOULD reference this page defers to;
  this page is how-to, that page is the rule to cite in review.
- [Bug triage](wiki:Bug_triage) and
  [Using the bug tracker](wiki:Using_the_bug_tracker) — upstream tracker
  documentation.
- [How to create a good bug report](wiki:How_to_create_a_good_bug_report) — the
  reporter-side companion to Part A.

<!--wiki:{{stub}}-->
