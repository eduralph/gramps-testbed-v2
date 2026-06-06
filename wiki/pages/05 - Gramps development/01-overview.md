---
title: "Gramps 6.1 Wiki Manual - Core Development - Overview"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

**Gramps** is a desktop genealogy application — a GTK3 / PyGObject front end on a Python 3.10+ core (`pyproject.toml:41`, `requires-python = ">= 3.10"`; the GUI requires `Gtk 3.0`, `gramps/grampsapp.py:264`). This section is for contributors working on **Gramps core** — the [`gramps-project/gramps`](https://github.com/gramps-project/gramps) repository itself.

Core is released under the **GNU General Public License, version 2 or later** (GPL-2.0-or-later; `gramps/COPYING`). Every new source file carries the canonical GPL header — see [[16-guidelines]].

The normative MUST/SHOULD rules — branch target, test layout, translation tooling, commit format — live in [[16-guidelines]]. This page is orientation; that page is the reference to cite in review.

## Architecture at a glance

Gramps separates a headless data core from the GTK layer, so the model can run without a display (CLI, tests, the Web API) and the GUI builds on top of it.

| Layer | Submodule | Role |
|-------|-----------|------|
| Model / database | `gramps.gen` | Headless, GUI-free core: the object model, database backends, filters, plugin framework, i18n. Imports no other Gramps submodule. |
| GTK layer | `gramps.gui` | The GTK3 / PyGObject desktop UI — editors, views, dialogs, the plugin manager. |
| Command line | `gramps.cli` | Headless front end for scripted / batch operation. |
| Bundled plugins | `gramps.plugins` | Reports, gramplets, importers/exporters, views shipped in-tree. |

The **`gen` self-containment rule** is the load-bearing invariant: code in `gramps.gen.*` MUST NOT import from `gramps.gui.*`, `gramps.plugins.*`, or any other Gramps submodule. `gen` is the foundation the GUI, the CLI, and the bundled plugins build on (`gramps/AGENTS.md` §Submodule Import Rules; see [[16-guidelines]]).

## Anatomy of the codebase

The source tree lives under `gramps/` in the checkout (`/home/eddie/workspace/gramps/gramps/`).

| Path | Contents |
|------|----------|
| `gramps/gen/` | Headless core — `lib/` (object model), `db/` (database backends + `DbTxn`), `filters/`, `plug/` (plugin framework), `proxy/`, `datehandler/`, `merge/`, `errors.py`, `types.py` |
| `gramps/gui/` | GTK3 desktop UI — `editors/`, `views`, `plug/`, `glade/`, `pluginmanager.py`, `dialog.py` |
| `gramps/cli/` | Command-line front end |
| `gramps/plugins/` | Bundled plugins — `gramplet/`, `report/`-family (`drawreport/`, `graph/`, …), `importer/`, `export/`, `db/`, `view/` |
| `gramps/test/` | Cross-cutting integration tests (per-module tests live in a `test/` package beside their module) |
| `gramps/grampsapp.py` | Application bootstrap (sets `Gtk 3.0`, builds the app) |
| `po/` | Translation catalogs + the hand-maintained `POTFILES.in` / `POTFILES.skip` |
| `gramps/AGENTS.md` | The in-repo coding standard for core (the authoritative source [[16-guidelines]] restates) |

Run from the checkout for development — never edit an installed copy ([[16-guidelines]] §Source structure).

## The object model

The data is built from **primary objects** — the genealogical entities a user creates and edits. Each is a class in `gramps/gen/lib/`:

| Object | Module | Class |
|--------|--------|-------|
| Person | `gramps/gen/lib/person.py:61` | `Person` |
| Family | `gramps/gen/lib/family.py:63` | `Family` |
| Event | `gramps/gen/lib/event.py:60` | `Event` |
| Place | `gramps/gen/lib/place.py:60` | `Place` |
| Source | `gramps/gen/lib/src.py:51` | `Source` |
| Citation | `gramps/gen/lib/citation.py:58` | `Citation` |
| Repository | `gramps/gen/lib/repo.py:49` | `Repository` |
| Media | `gramps/gen/lib/media.py:59` | `Media` |
| Note | `gramps/gen/lib/note.py:48` | `Note` |

Objects reference one another by **handle** — an opaque, stable internal identifier, typed in `gramps/gen/types.py` (`PersonHandle`, `FamilyHandle`, …, all `NewType(..., str)`, `gramps/gen/types.py:41`). Handles are for internal traversal; the user-facing **Gramps IDs** (`I0001`, `F0001`, …) are user-editable and rewritten in bulk by the Reorder tool, so never key logic on them. Every database write goes through a transaction:

```python
with DbTxn(_("Adding a person"), db) as trans:
    db.add_person(person, trans)
```

See [[06-data-access]] for the database API, and [[16-guidelines]] §Runtime for the handle/ID and transaction rules.

## Building and running

```bash
git clone https://github.com/gramps-project/gramps.git
cd gramps
python3 -m gramps          # run from source
```

Tests are stdlib `unittest` (never pytest), named `<module>_test.py` in a `test/` package beside the module:

```bash
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

`mypy` and `black` are enforced in CI. The full getting-started walkthrough — environment setup, dependencies, IDE — is [[02-get-started]].

## Community

| Channel | Where |
|---------|-------|
| Forum (primary support) | <https://gramps.discourse.group/> |
| Bug tracker (Mantis) | <https://gramps-project.org/bugs/> |
| Developer mailing list | [gramps-devel](https://lists.sourceforge.net/lists/listinfo/gramps-devel) |
| Matrix | [`#gramps:matrix.org`](https://app.element.io/#/room/#gramps:matrix.org) |
| IRC | [`#gramps`](irc://irc.libera.chat/#gramps) on irc.libera.chat |

Gramps was originally written by **Donald N. Allingham**. Today a core team maintains it — Nick Hall (architect), John Ralls (macOS packaging), Paul Culley (Windows), David Straub (Gramps Web), among others; see the [Team](wiki:Team) page for the full roster. Bugs go to the tracker, not the mailing list ([Contact](wiki:Contact)).

## See also

- [[02-get-started]] — set up a development environment and run Gramps from source.
- [[04-architecture]] — how `gen` / `gui` / `cli` / `plugins` fit together in depth.
- [[16-guidelines]] — the normative MUST/SHOULD reference for core contributions.
- [Portal:Developers](https://gramps-project.org/wiki/index.php?title=Portal:Developers) — upstream developer portal.
- [Team](wiki:Team) · [Contact](wiki:Contact) — who maintains Gramps and how to reach the community.

<!--wiki:{{stub}}-->
