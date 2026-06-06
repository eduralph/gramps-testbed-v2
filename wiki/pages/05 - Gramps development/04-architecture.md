---
title: "Gramps 6.1 Wiki Manual - Core Development - Architecture & subsystems"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

A core contributor's first question on any change is **which *subsystem* does it belong in?** Gramps core is not one flat package; it is five top-level submodules under `gramps/`, layered so that the headless data core knows nothing about the GUI, the GUI builds on the core, and the shipped plugins sit on top of both. Getting the layer right is half the work — a database fix belongs in `gramps.gen.db`, not in a view; a widget belongs in `gramps.gui`, never in `gramps.gen`.

This page is the map of those submodules: where each lives, what it owns, what it may import, and how data flows from a transaction through signals to the views. The directory list below is verified against the checkout (`ls /home/eddie/workspace/gramps/gramps`).

The single hard rule that shapes everything: **`gramps.gen.*` imports no other Gramps submodule.** It is stated normatively in [[16-guidelines]] (Source structure) and in the in-repo standard (`gramps/AGENTS.md:107-109`, §Submodule Import Rules). The rest of this page explains the layering that rule produces.

## Submodules at a glance

| Submodule         | Path             | Owns                                                                 | May import                          |
|-------------------|------------------|---------------------------------------------------------------------|-------------------------------------|
| `gramps.gen`      | `gramps/gen/`    | Headless model: data objects, db, plugin registry, config, utils    | **No other Gramps submodule**       |
| `gramps.plug`     | `gramps/gen/plug/` | The plugin framework the rest of core builds on (registry, report/docgen) | `gramps.gen` only (it *is* gen)     |
| `gramps.gui`      | `gramps/gui/`    | GTK3 views, editors, widgets, dialogs, the running UI               | `gramps.gen`                        |
| `gramps.cli`      | `gramps/cli/`    | Headless command-line front end                                     | `gramps.gen`                        |
| `gramps.plugins`  | `gramps/plugins/`| The plugins **shipped with** core (reports, tools, views, …)        | `gramps.gen`, `gramps.gui`          |

Note `gramps.plug` is not a top-level sibling of the others — it lives *inside* gen at `gramps/gen/plug/`. It is called out separately here because it is the framework boundary the whole plugin system rests on, but as code it is bound by the same self-containment rule as the rest of gen.

## Layering and dependency direction

The dependency arrows all point **down**, toward gen — each layer imports only the layers beneath it:

![[_media/core-architecture.svg|Fig. 1 — Gramps core, logical architecture. The `gramps.gui` and `gramps.cli` front ends and the bundled `gramps.plugins` all import downward into the headless `gramps.gen` core; nothing in `gen` imports upward. The DBAPI/SQLite backend implements the `gen.db` interface.]]

- **gen depends on nothing gramps.** It is the headless, GUI-free core that the CLI, the GUI, and every shipped plugin build on. A `from gramps.gui…` or `from gramps.plugins…` import anywhere under `gramps/gen/` is a defect, not a style nit (`gramps/AGENTS.md:107-109`).
- **gui depends on gen**, never the reverse. GTK3 widgets, editors, and views import data objects and the db from gen; gen must stay importable in a process with no display.
- **cli also depends only on gen** — it is the other front end, used by report/tool CLI modes and by headless automation. The existence of cli is *why* gen must be GUI-free: a CLI run must never pull in GTK.
- **plugins (shipped) may depend on both gen and gui** — a report's CLI path uses gen, its GUI dialog uses gui.

The discipline is one-directional: upper layers import downward only, never the reverse.

![[_media/API.svg|The Gramps database API surface — the read/write interface every front end and plugin goes through.]]

## `gramps.gen` — the headless core

`gramps/gen/` is where most data-level fixes land. Verified subdirectories and key modules:

| Path                | Contents                                                                 |
|---------------------|--------------------------------------------------------------------------|
| `gen/lib/`          | The data objects — `Person`, `Family`, `Event`, `Place`, `Source`, `Citation`, `Repository`, `Media`, `Note`, `Tag`, plus the `*ref`/`*base` mixins and type enums |
| `gen/db/`           | The database layer — `DbReadBase` / `DbWriteBase` (`gen/db/base.py:57`, `:1489`), the generic SQLite backend (`generic.py`), `DbTxn` (`gen/db/txn.py:52`), undo/redo, upgrade |
| `gen/plug/`         | The plugin framework — registry (`_pluginreg.py`), manager (`_manager.py`), report/docgen/menu infrastructure (covered below) |
| `gen/utils/`        | Cross-cutting helpers — including `callback.py`, the signal base class (see Data flow) |
| `gen/config.py`     | The `ConfigManager` and the global `config` object; also emits signals on setting changes |
| `gen/const.py`      | Build-time constants and paths |
| `gen/dbstate.py`    | `DbState` (`gen/dbstate.py:55`) — the live-database holder that emits `database-changed` |
| `gen/filters/`, `gen/proxy/`, `gen/merge/`, `gen/datehandler/`, `gen/relationship/`, `gen/simple/` | Filtering, database proxies, merge logic, date parsing/display, relationship calculators, the `SimpleAccess` convenience API |

**The MUST:** nothing under `gen/` imports `gramps.gui`, `gramps.plugins`, or `gramps.cli`. When a gen module needs something that lives higher up, the dependency is inverted — the upper layer registers a callback or passes an object in, rather than gen reaching upward. This is what keeps gen runnable headless.

Type and handle aliases live in `gen/types.py` (`PersonHandle`, `PersonGrampsID`, …); [[16-guidelines]] (Coding style) requires using them over bare `str`.

## `gramps.gen.plug` — the plugin framework

The plugin framework that the rest of core and the bundled plugins build on. It is the boundary where the core meets the plugin layer, and it sits inside gen so the registry can be loaded headless.

| Module / dir          | Role                                                                 |
|-----------------------|---------------------------------------------------------------------|
| `_pluginreg.py`       | The registry — `register(KIND, …)` and the `PTYPE_STR` constants every plugin kind keys off |
| `_manager.py`         | The plugin manager that discovers, imports, and reloads plugins; emits `plugins-reloaded` |
| `_gramplet.py`        | The `Gramplet` base class (re-exported as `gramps.gen.plug.Gramplet`, `gen/plug/__init__.py:68`) |
| `_import.py` / `_export.py` | Importer / exporter plugin wrappers |
| `report/`, `docgen/`, `docbackend/`, `menu/` | The report abstraction, document-generation primitives, and menu-option machinery reports build on |

When you change registration semantics or a plugin base class here, you are changing the contract every plugin depends on — treat the surface as public API before altering a constant or signature.

## `gramps.gui` — the GTK3 front end

`gramps/gui/` is the running desktop application: GTK3 widgets, the view manager, editors, dialogs. It imports gen freely and is imported by shipped plugins that have a GUI surface.

| Path              | Contents                                                                |
|-------------------|-------------------------------------------------------------------------|
| `gui/views/`      | The view base classes — `ListView` (`listview.py`), `NavigationView`, `PageView` — that VIEW-kind plugins subclass |
| `gui/editors/`    | The object editors — `editperson.py`, `editfamily.py`, `editevent.py`, … and the `displaytabs/` shared tab widgets |
| `gui/widgets/`    | Reusable GTK widgets (date entry, monitored widgets, the place/person selectors' building blocks) |
| `gui/plug/`       | The GUI side of the plugin framework — `tool.py` (the `Tool` base TOOL plugins subclass), report dialogs, `_guioptions.py` |
| `gui/viewmanager.py`, `gui/displaystate.py`, `gui/uistate.py` | The UI state holders that emit `active-changed`, `mru-changed`, `filter-name-changed`, … |
| `gui/dbman.py`, `gui/dbloader.py` | Tree management and loading |
| `gui/filters/`, `gui/merge/`, `gui/selectors/`, `gui/sidebar/` | GUI counterparts of the gen subsystems |

A change here must not leak into gen. If an editor needs a new data operation, the operation goes in gen and the editor calls it.

## `gramps.cli` — the headless front end

`gramps/cli/` is the command-line application: argument parsing (`argparser.py`, `arghandler.py`), the headless `User` (`cli/user.py`), tree management (`clidbman.py`), and `cli/plug/` for running report/tool plugins in CLI mode. It depends on gen only — it is the concrete reason gen must stay GUI-free, since a `gramps -O tree -a report …` invocation must run with no display attached.

## `gramps.plugins` — the plugins shipped with core

`gramps/plugins/` holds the plugins that ship *inside* the core repository. They are written to the plugin framework described above — `register(...)` and the report / tool / view / gramplet base classes.

| Dir                  | Kind shipped here                                                     |
|----------------------|----------------------------------------------------------------------|
| `plugins/textreport/`, `plugins/drawreport/`, `plugins/graph/`, `plugins/webreport/` | REPORT plugins (text, draw, graphviz, narrative web) |
| `plugins/tool/`      | TOOL plugins (the built-in tools)                                     |
| `plugins/view/`      | VIEW plugins (the built-in views beyond the core sidebar set)         |
| `plugins/gramplet/`  | GRAMPLET plugins (Dashboard widgets)                                  |
| `plugins/importer/`, `plugins/export/` | IMPORT / EXPORT plugins (GEDCOM, JSON, …)           |
| `plugins/quickview/`, `plugins/rel/`, `plugins/mapservices/`, `plugins/cite/`, `plugins/thumbnailer/`, `plugins/sidebar/`, `plugins/docgen/`, `plugins/db/`, `plugins/lib/`, `plugins/webstuff/` | The remaining kinds, one dir per kind |

**A shipped plugin is core code.** It lives in `gramps-project/gramps`, ships with the application, and a change to it is a **core** contribution — the core test layout (`test/` package + `<module>_test.py`), the core branch (`maintenance/gramps61`), and the core CI gates (Black + `mypy`) all apply, exactly as for any other core change ([[16-guidelines]]). The `.gpr.py` / `register(...)` mechanism does not change that: the repository the code lives in does. A widget or report under `gramps/plugins/` is reviewed by the same rules as one under `gramps/gui/`.

## Data flow: DbTxn → signals → views

The runtime spine ties the layers together. A change made in gen propagates upward to the GUI entirely through signals — gen never calls into gui directly (it can't; see the import rule).

1. **Write inside a transaction.** Every database mutation runs inside a `DbTxn` (`gen/db/txn.py:52`); this is a **MUST** in [[16-guidelines]] (Runtime):

   ```python
   from gramps.gen.db import DbTxn

   with DbTxn(_("Adding example"), db) as trans:
       db.add_person(person, trans)
   ```

2. **Signals fire at commit, not per-write.** When the transaction commits, the db emits one signal per affected primary object — `person-add`, `media-update`, `citation-delete`, `note-rebuild`, each carrying a list of handles. Signals are *delayed until the transaction succeeds*, so a failed transaction emits nothing. The emit order is fixed (deletes, then adds, then updates) to keep listeners consistent — the detail and rationale are in [Signals and callbacks](wiki:Signals_and_callbacks).

3. **`DbState` brokers the live database.** `DbState` (`gen/dbstate.py:55`) holds the currently open db and emits `database-changed` (`gen/dbstate.py:60-61`, `:137`) when a tree is opened or closed. A view connects to it to know *which* db to listen to:

   ```python
   self.dbstate.connect("database-changed", self.db_changed)
   self.db.connect("person-update", self.update)
   ```

4. **Views and gramplets react.** GUI elements connect to the db signals (often via the `CallbackManager` in `gen/utils/callman.py`, which filters by the handles an element cares about) and refresh. The signal base class that makes `connect` / `emit` / `disconnect` work lives in `gen/utils/callback.py` — headless, in gen, so the CLI participates in exactly the same mechanism.

The upshot for a contributor: to make a data change show up in the UI, you do **not** call the UI. You commit inside a `DbTxn` and let the signal reach whatever is listening. The full signal catalogue (db signals, `dbstate`, `uistate`, `displaystate`, config, plugin manager) is in [Signals and callbacks](wiki:Signals_and_callbacks); the db API itself is covered in [[06-data-access]].

## See also

- [[05-fundamentals]] — the cross-cutting concepts every core change relies on.
- [[06-data-access]] — working with the database API (`DbReadBase` / `DbWriteBase`, `DbTxn`, handles).
- [[07-api-reference]] — the per-module API surface in detail.
- [[16-guidelines]] — the normative MUST/SHOULD rules this page's layering enforces (Source structure, Runtime).
- `gramps/AGENTS.md` §Submodule Import Rules — the in-repo statement of gen self-containment.
- [Signals and callbacks](wiki:Signals_and_callbacks) — the full signal catalogue and emit-order semantics.

<!--wiki:{{stub}}-->
