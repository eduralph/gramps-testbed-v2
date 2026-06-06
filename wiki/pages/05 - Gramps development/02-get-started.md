---
title: "Gramps 6.1 Wiki Manual - Core Development - Getting Started"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

This page walks a first-time **core** contributor from "I want to fix a Gramps bug" to "my change runs and its test passes". The target repository is [`gramps-project/gramps`](https://github.com/gramps-project/gramps) — the application itself.

The normative MUST/SHOULD rules this page only gestures at live in [[16-guidelines]] — cite that page in review, treat this one as the how-to. Deep interactive debugging is in [[09-debug]]; the database API you will most often touch is in [[06-data-access]].

## Prerequisites

Core development **runs Gramps from the source tree**, so you need the same runtime libraries an end user has, plus the build/dev toolchain.

| Requirement | Why | Notes |
|-------------|-----|-------|
| Python 3.10+ | Gramps 6.1's minimum | `requires-python = ">= 3.10"` (`gramps/pyproject.toml:41`) |
| GTK 3.24+ | The GUI toolkit | `gramps/README.md:18` |
| PyGObject 3.12+ | Python ↔ GTK/GLib bindings | `gramps/README.md:19` |
| Pycairo / pangocairo / librsvg2 | 2D rendering, text, SVG icons | full list in `gramps/README.md` |
| `orjson` | Fast JSON, a hard runtime dependency | `gramps/pyproject.toml` `dependencies` |
| Git | Clone, branch, submit | see [Brief introduction to Git](wiki:Brief_introduction_to_Git) for the full reference |
| gettext / translation tools | i18n strings build correctly | needed for `_()` to resolve at runtime |

On Debian/Ubuntu the runtime libraries come in fastest via `apt-get build-dep gramps` (pulls the GTK/PyGObject/cairo stack); on Fedora install the `python3-gobject`, `gtk3`, and `gettext` packages. You do **not** need to *install* Gramps to develop it — you run the checkout in place.

## Get the source: fork, clone, add upstream

Core contributions go through your own GitHub fork, with the canonical repository wired in as a second remote called `upstream`. This is the arrangement the rest of the workflow assumes.

1. Fork [`gramps-project/gramps`](https://github.com/gramps-project/gramps) on GitHub.
2. Clone **your fork** as `origin`:

   ```bash
   git clone git@github.com:<your-name>/gramps.git
   cd gramps
   ```

3. Add the canonical repository as `upstream` (fetch-only):

   ```bash
   git remote add upstream https://github.com/gramps-project/gramps.git
   git remote set-url --push upstream cannot_push   # belt-and-braces: never push to upstream
   git fetch upstream
   ```

   `git remote -v` should now show `origin` pointing at your fork and `upstream` at `gramps-project/gramps`.

## Branch from `upstream`, not your fork's copy

This is the single most common first-timer mistake, and [[16-guidelines]] makes it a **MUST**: branch from `upstream/<base>`, **not** from your fork's tracking copy of that branch. A fork's branches drift the moment upstream moves, and basing on a stale copy drags unrelated commits into your PR (upstream PRs 2315/2316 carried a stray `AGENTS.md` from the fork exactly this way — INTEGRATION §2).

The base for an ordinary bug fix is **`maintenance/gramps61`**, the current production branch — *not* `master`. `master` is feature-only; fixes ride the maintenance branch and the maintainer forward-merges them to `master`, which gets them to users sooner (`doc16:113`; jralls on gramps#2298; INTEGRATION §2). Only genuinely new-feature work targets `master`.

```bash
git fetch upstream
git switch -c fix-12345 upstream/maintenance/gramps61
```

A maintainer's explicit base-branch request on a specific PR overrides this default (`doc16:114`; Nick-Hall on gramps#2299) — but absent that, `maintenance/gramps61` is where a fix belongs. See [[16-guidelines]] §Contributor workflow for the full rule and [Brief introduction to Git](wiki:Brief_introduction_to_Git) for the branching reference.

## Run Gramps from the source

Gramps 6.1 runs straight from the checkout — there is **no build step** for a from-source run (`Gramps.py` adds the source dir to the import path itself, `gramps/Gramps.py:22-28`):

```bash
python3 Gramps.py
```

If a module is missing at startup, install its GObject-Introspection package, e.g.:

```bash
sudo apt install gir1.2-gexiv2-0.10      # GExiv2 (image metadata)
sudo apt install gir1.2-osmgpsmap-1.0    # OsmGpsMap (Geography view)
```

### Protect your real family trees first

A development build run as your normal user opens your **real** Gramps database — and a bug in code you are editing can corrupt productive data. Before running an unfamiliar branch (especially `master`), take the backup precaution from [Getting started with Gramps master](wiki:Getting_started_with_Gramps_master):

1. Start your **installed** stable Gramps.
2. Export your data as a *Gramps Package* (`.gpkg`).
3. Quit it. Run the development build, create a **new** Family Tree, and import the package into that.

To keep development data wholly separate from your real `~/.gramps`, point Gramps at a throwaway home directory with the `GRAMPSHOME` environment variable (`gramps/gen/const.py:105`):

```bash
GRAMPSHOME=/tmp/gramps-dev python3 Gramps.py
```

### Running parallel versions safely

You can keep your installed stable Gramps and the from-source build side by side — run the source build from its directory and never `install` it over the system copy. Each version reads the family trees under its own `GRAMPSHOME`, so a separate `GRAMPSHOME` per branch keeps their databases from colliding. For juggling several branches at once without re-cloning, `git worktree` gives each branch its own working directory off one repository — see [Brief introduction to Git](wiki:Brief_introduction_to_Git).

## The edit → run → test loop

Core has no hot-reload; the loop is:

1. **Edit** the source in the checkout. (Edit the checkout, never an installed copy — [[16-guidelines]] makes this a MUST.)
2. **Run** `python3 Gramps.py` to exercise the change in the GUI.
3. **Test** the affected module headlessly — far faster than launching the GUI, and the regression test you ship runs the same way.

### The test command

Core uses the Python standard-library `unittest` only (never `pytest`). Test files use the **`_test.py` suffix** and live in a **`test/` package (singular)** beside the module under test — e.g. `gramps/gen/lib/test/date_test.py`. The checkout has 30 such `test/` packages; the discovery pattern is `*_test.py`, so a file named any other way is not picked up ([[16-guidelines]] §Testing).

Run the whole suite from the repository root:

```bash
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

`GRAMPS_RESOURCES=.` tells Gramps to find its data files in the checkout; the `-p` pattern is what selects the `_test.py` suffix. To run a single module's tests during the loop, give its dotted path, e.g. `python3 -m unittest gramps.gen.lib.test.date_test`.

Your fix ships with a regression test that **fails before the fix and passes after it** — this is a MUST in [[16-guidelines]], the only exception being doc-only changes. Reproduce against `example/gramps/example.gramps`, the canonical fixture, before you start (INTEGRATION §5).

### Static checks before you commit

Core enforces more than the suite. Run these locally so CI doesn't bounce the PR:

```bash
# Black — formats every changed .py; CI enforces it
git diff --name-only --diff-filter=ACMR origin/master...HEAD \
  | grep '\.py$' | xargs --no-run-if-empty black

# mypy — core enforces it (mypy.ini: files = ./gramps, ./test)
mypy
```

If your change adds or removes a `.py` file, you must also update `po/POTFILES.in` or `po/POTFILES.skip` by hand and verify with `PYTHONPATH=. python po/test/po_test.py` ([[16-guidelines]] §Adding and removing Python files).

## A minimal Git workflow

The full reference — remotes, rebasing, worktrees, conflict resolution — is [Brief introduction to Git](wiki:Brief_introduction_to_Git). The short version for one fix:

```bash
# 1. Branch from upstream's production branch (not your fork's copy)
git fetch upstream
git switch -c fix-12345 upstream/maintenance/gramps61

# 2. Edit, then test
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"

# 3. Stage and commit (see the commit-message rules below)
git add <files>
git commit

# 4. Push the branch to your fork
git push -u origin fix-12345

# 5. Open a DRAFT PR against maintenance/gramps61 on GitHub
```

Open it as a **draft** for early feedback or CI; mark it ready only once the change is complete and you have re-read the diff with fresh eyes ([[16-guidelines]] §Contributor workflow). One logical fix per PR — bundling hides mistakes.

### Commit message essentials

Commit messages are parsed by scripts that update the tracker and generate release notes, so the shape matters ([[16-guidelines]] §Commit messages):

- Subject ≤ 70 characters; blank line; body wrapped at 80 describing the change from the user's perspective.
- The Mantis trailer is the **last** line — `Fixes #NNNN` (the `#NNNN` form, no URL) closes the bug; `Bug #NNNN` only cross-references it.
- Reference other commits by **full** hash so GitHub auto-links them.

```
Fix crash when opening event editor with empty date field.

When a date field was left blank, the event editor raised an unhandled
AttributeError. This change adds a guard so the field is treated as an
empty string instead.

Fixes #12345.
```

Structure the PR body as **Root cause / Fix / Verified against / Test**, citing `path:lines` on `maintenance/gramps61`, and end it with the same `Fixes #NNNN` ([[16-guidelines]] §Contributor workflow).

## See also

- [[16-guidelines]] — the normative MUST/SHOULD/MAY rules; the page to cite in review.
- [Brief introduction to Git](wiki:Brief_introduction_to_Git) — the full Git reference (remotes, rebasing, worktrees, PRs).
- [[09-debug]] — interactive debugging, logging, and tracing a defect.
- [[06-data-access]] — the database API (`DbTxn`, handles vs Gramps IDs) you will touch most.
- `gramps/AGENTS.md` — the in-repo coding standard for core (the source [[16-guidelines]] restates).
- [gramps-project/gramps `CONTRIBUTING`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/CONTRIBUTING) — upstream contributor pointers.
- [Portal:Developers](https://gramps-project.org/wiki/index.php?title=Portal:Developers) — upstream developer portal.

<!--wiki:{{stub}}-->
