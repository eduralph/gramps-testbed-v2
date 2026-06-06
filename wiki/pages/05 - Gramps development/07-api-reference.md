---
title: "Gramps 6.1 Wiki Manual - Core Development - API Reference"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

## Overview

A curated map of the API surface a *core* contributor touches, organised by
module. This is a navigator, not a generated dump: for exhaustive signatures,
read the source of the module referenced or the
[upstream Sphinx docs](https://gramps-project.org/docs/). Listing every signature
here would only have us chasing version drift.

Two facts shape everything below.

1. **`gramps.gen.*` is the stable contract.** `gen` is self-contained — it imports
   no other gramps submodule (`gramps/gen/__init__.py` documents it as "common to
   all gramps interfaces"). The public object model, DB interface, plugin registry,
   and docgen API all live here and change rarely; when they do, the change is a
   deliberate, documented break. Treat `gen` as the surface you can rely on.
2. **`gramps.gui.*` and `gramps.plugins.*` are *in scope* for core, but unstable.**
   A core contributor edits editors, views, widgets, and shipped plugins directly. The
   trade-off is that these modules move freely between minor releases — there is no
   compatibility promise across them. Factor reusable logic down into `gen` so it
   stays testable without a display and stable across versions.

The normative MUST/SHOULD rules — import direction, `mypy`, `black`, i18n, test
placement, commit format — live in [[16-guidelines]]. This page is the how-to map;
[[16-guidelines]] is the rule reference. Don't duplicate it; defer to it.

## gramps.gen.lib — the object model

The primary classes and the value classes that compose them. Every primary class
has matching `get_*` / `set_*` accessors; relationships are exposed as handle lists
(`get_family_handle_list`) or ref lists (`get_event_ref_list`,
`get_child_ref_list`). The full field inventory per object is catalogued in
[[06-data-access]].

| Class | Module | Notes |
|-------|--------|-------|
| `Person`     | `gramps.gen.lib.person`   | Gender constants are class attributes: `Person.MALE`, `Person.FEMALE`, `Person.UNKNOWN` |
| `Family`     | `gramps.gen.lib.family`   | `father_handle`, `mother_handle`, `child_ref_list` |
| `Event`      | `gramps.gen.lib.event`    | Typed by `EventType` |
| `Place`      | `gramps.gen.lib.place`    | Hierarchical via `placeref_list` |
| `Source`     | `gramps.gen.lib.src`      | Note the module is `src`, the class `Source` |
| `Citation`   | `gramps.gen.lib.citation` | Points at a `Source` via `source_handle` |
| `Repository` | `gramps.gen.lib.repo`     | Module is `repo` |
| `Media`      | `gramps.gen.lib.media`    | |
| `Note`       | `gramps.gen.lib.note`     | |
| `Tag`        | `gramps.gen.lib.tag`      | Not referenced by handle in the way primaries are |

All ten are re-exported from the package root, so `from gramps.gen.lib import
Person, Family` is the idiomatic import (`gramps/gen/lib/__init__.py:45-57`).

Value (secondary) classes live alongside them: `Name`, `Surname`, `Date`,
`Address`, `Attribute`, `Url`, `EventRef`, `ChildRef`, `MediaRef`, `RepoRef`,
`PersonRef`, `LdsOrd`, and the researcher record `Researcher`. Type enums
(`EventType`, `NameType`, `AttributeType`, `PlaceType`, …) all subclass
`GrampsType` (`gramps/gen/lib/grampstype.py:90`) — an int-backed enum with a
display string, so comparisons use the class constants, not raw strings.

## gramps.gen.db — the database interface

At the root of every database interface is `DbReadBase` and/or `DbWriteBase`;
mutation always happens inside a `DbTxn` context manager. `DbState` carries the
live database around the application.

| Symbol | Module | Role |
|--------|--------|------|
| `DbReadBase`  | `gramps.gen.db.base` (`base.py:57`)   | Read-only interface: `get_person_from_handle`, `get_person_cursor`, `find_backlink_handles`, `iter_people`, … |
| `DbWriteBase` | `gramps.gen.db.base` (`base.py:1489`) | Subclasses `DbReadBase`; adds `add_*` / `commit_*` / `remove_*` |
| `DbTxn`       | `gramps.gen.db.txn` (`txn.py:52`)     | Transaction context manager — required for every write; a `defaultdict` subclass tracking the undo log |
| `DbState`     | `gramps.gen.dbstate` (`dbstate.py:55`) | Holds the open db; emits `database-changed` / `no-database`. Subclasses `Callback` |
| `DbGeneric`   | `gramps.gen.db.generic`               | The generic implementation backing the shipped backends |
| `open_database` | `gramps.gen.db.utils`               | Open a tree by path — used in repro scripts and tests |
| (exceptions)  | `gramps.gen.db.exceptions`            | DB-layer exception hierarchy |

The concrete SQL backend (`gramps.plugins.db.dbapi.dbapi`) lives under
`plugins`, not `gen` — it implements the `DbGeneric` details. Core code that wants
to stay backend-agnostic talks to `DbReadBase` / `DbWriteBase`, never the concrete
class.

```python
from gramps.gen.db import DbTxn
from gramps.gen.lib import Family

with DbTxn(_("Add family"), db) as trans:
    family = Family()
    db.add_family(family, trans)          # add_* assigns the handle
    db.commit_family(family, trans)       # commit_* writes the change
```

Signals (`person-add`, `family-update`, `note-delete`, the `*-rebuild` family) are
emitted at the *end* of a transaction, in a fixed delete→add→update order. The
mechanics and ordering caveats are covered in [[06-data-access]]; the cross-cutting
explanation is the upstream [Signals and Callbacks](wiki:Signals_and_Callbacks)
page.

## gramps.gen.plug — plugin registry and report base

The plugin machinery: registration constants, the report base class, options
forms, and the menu-widget catalogue.

| Symbol | Module | Role |
|--------|--------|------|
| `Report`            | `gramps.gen.plug.report` (`_reportbase.py:39`) | Base class for every report |
| `MenuReportOptions` | `gramps.gen.plug.report` (`_options.py`)       | Options form a report subclasses |
| `ReportOptions`, `DocOptions` | `gramps.gen.plug.report`             | Lower-level options bases |
| `stdoptions`        | `gramps.gen.plug.report.stdoptions`            | Pre-built options (locale chooser, name-format, private/living filters) |
| `endnotes`, `utils` | `gramps.gen.plug.report`                       | Citation endnotes; shared report helpers |
| (category consts)   | `gramps.gen.plug._pluginreg`                   | `CATEGORY_TEXT`, `CATEGORY_DRAW`, `CATEGORY_GRAPHVIZ`, `CATEGORY_WEB`, `CATEGORY_BOOK`, `CATEGORY_TREE`, `CATEGORY_CODE` |
| (menu widgets)      | `gramps.gen.plug.menu`                         | `BooleanOption`, `EnumeratedListOption`, `PersonOption`, `FilterOption`, `StringOption`, … |

`Report` and `MenuReportOptions` are re-exported from
`gramps.gen.plug.report` (`gramps/gen/plug/report/__init__.py:29,33`). Register a
report under one of the category constants; the chosen category fixes which docgen
interface the report drives (see the next section).

| Category | Docgen interface | Notes |
|----------|------------------|-------|
| `CATEGORY_TEXT`     | `TextDoc`             | Text reports — PDF, HTML, ODF, plain text |
| `CATEGORY_DRAW`     | `DrawDoc`             | Graphical reports drawn at exact coordinates |
| `CATEGORY_GRAPHVIZ` | `GVDoc`               | Graphviz / DOT input — laid out by `dot` |
| `CATEGORY_WEB`      | (direct file I/O)     | Narrative website — writes HTML/CSS directly |
| `CATEGORY_BOOK`     | `TextDoc` + `DrawDoc` | A composition of Text and Draw reports |
| `CATEGORY_TREE`     | `DrawDoc`             | Genealogical tree-chart layouts |
| `CATEGORY_CODE`     | (none)               | Catch-all for reports that fit nowhere else |

## Report docgen API — TextDoc / DrawDoc / GVDoc

The document-generation interfaces live under `gramps.gen.plug.docgen`, all
re-exported from the package root (`gramps/gen/plug/docgen/__init__.py:27-50`).
`BaseDoc` holds the common part (open/close, stylesheet handling, the
`PaperStyle`); the three interfaces below diverge.

| Symbol | Module | Role |
|--------|--------|------|
| `BaseDoc`        | `gramps.gen.plug.docgen.basedoc`     | Common base: open/close, stylesheet, `paper_style` |
| `TextDoc`        | `gramps.gen.plug.docgen.textdoc`     | Sequential text layout, backend-paginated |
| `DrawDoc`        | `gramps.gen.plug.docgen.drawdoc`     | Exact-coordinate graphics on a frame |
| `GVDoc`          | `gramps.gen.plug.docgen.graphdoc`    | Graphviz model; layout delegated to `dot` |
| `IndexMark`      | `gramps.gen.plug.docgen.textdoc`     | Attaches an index entry to text within a paragraph |
| `FontStyle`      | `gramps.gen.plug.docgen.fontstyle`   | With `FONT_SANS_SERIF`, `FONT_SERIF`, `FONT_MONOSPACE` |
| `ParagraphStyle` | `gramps.gen.plug.docgen.paragraphstyle` | Drives titles, body, list entries |
| `PaperStyle`, `PaperSize` | `gramps.gen.plug.docgen.paperstyle` | Page geometry; `PAPER_PORTRAIT` / `PAPER_LANDSCAPE` |

The three interfaces have distinct hierarchies. Knowing which container nests what
saves a long trip through the source.

**`TextDoc` — sequential text, paginated by the backend.**

```
Document
├── Paragraph
├── Pagebreak
├── Table
│   └── Row
│       └── Cell
│           ├── Paragraph
│           └── Image
└── Image
```

Images are only allowed as children of `Document` or `Cell`. `IndexMark` attaches
to text within a paragraph, feeding the table of contents in Book reports.

**`DrawDoc` — exact-coordinate graphics on a frame.**

```
Document
└── Frame
    ├── Line
    ├── Polygon
    ├── Box
    └── Text
```

The frame is the drawing surface; elements are placed by coordinates the report
supplies, origin at the top-left of the usable area. Graphical reports must honour
`PaperStyle.get_usable_width()` / `…_height()` — drawing into the margins is a
contract violation. Text reports never read these; the backend paginates around
them.

**`GVDoc` — graphviz model.**

```
Document
└── Subgraph
    ├── Node
    ├── Link
    └── Comment
```

The report defines nodes, links, comments; the external `dot` binary does layout
(hence `requires_exe=["dot"]` on Graphviz reports).

The full source-scraped notes on the docgen tree are in the upstream
[Report API](wiki:Report_API) page.

## gramps.gen.utils — shared utilities

Cross-cutting helpers. The most relevant to core work touching the GUI is the
callback machinery (`callback.py`, `callman.py`); the rest are file, image, id,
and locale helpers.

| Symbol | Module | Role |
|--------|--------|------|
| `Callback`         | `gramps.gen.utils.callback` (`callback.py:51`) | Base class giving `connect` / `disconnect` / `emit`; mixed into `DbState`, `History`, the db backends |
| `CallbackManager`  | `gramps.gen.utils.callman` (`callman.py:111`)  | A signal *filter* for GUI elements — register callbacks and handles, connect once, `disconnect_all()` on close |
| `create_id`        | `gramps.gen.utils.id`                          | Generate object handles |
| `GrampsLocale`     | `gramps.gen.utils.grampslocale`                | The locale class; the live instance is `glocale` (below) |
| (file helpers)     | `gramps.gen.utils.file`                        | `media_path`, `expand_media_path`, path normalisation |
| (image helpers)    | `gramps.gen.utils.image`                       | Thumbnailing, crop, resize |
| `string`, `cast`, `lru`, `alive`, `place`, `location` | `gramps.gen.utils.*` | String formatting, type casts, LRU cache, alive-status, place/location formatting |

`CallbackManager` is the right tool when a view or gramplet must react only to
changes affecting handles it cares about — it suppresses the firehose of db
signals down to the registered set. The registration/connect/disconnect lifecycle
is documented in the upstream
[Signals and Callbacks](wiki:Signals_and_Callbacks) page.

## gramps.gen.config / const / errors / types

The small, foundational modules.

| Module | Role |
|--------|------|
| `gramps.gen.config`  | The config manager. Module-level shortcuts `register(key, value)`, `get(key)`, `set(key, value)` over the singleton `CONFIGMAN` (`config.py:70-100`). The manager emits the changed setting name as its own signal. |
| `gramps.gen.const`   | Build-time constants. `GRAMPS_LOCALE` (the live `GrampsLocale`, aliased `glocale`) and the bound `_` are defined here (`const.py:252-253`); also `VERSION_TUPLE`, paths, app metadata. |
| `gramps.gen.errors`  | The exception hierarchy. Raise an existing class before inventing one: `HandleError`, `DbError`, `DatabaseError`, `ReportError`, `PluginError`, `FilterError`, `WindowActiveError`, `MergeError`, `ValidationError`, … (`errors.py`). |
| `gramps.gen.types`   | `NewType` aliases for handles and IDs: `PersonHandle`, `FamilyHandle`, …, `PersonGrampsID`, … (`types.py:41-50`). Prefer these over bare `str`; `mypy` then catches handle-vs-ID mix-ups. `mypy` is enforced in CI — see [[16-guidelines]]. |

```python
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext        # bind the translator
ngettext = glocale.translation.ngettext
```

## gramps.gui.* — editors, views, widgets, dialogs

In scope for core, unstable across minors. These pull in GTK and cannot be
imported by `gen` (the import rule is one-way; see [[16-guidelines]]).

| Area | Module | Key symbols |
|------|--------|-------------|
| Editors  | `gramps.gui.editors`        | `EditPerson`, `EditFamily`, `EditEvent`, `EditPlace`, `EditSource`, `EditCitation`, `EditRepository`, `EditMedia`, `EditNote`, plus ref/secondary editors (`EditEventRef`, `EditName`, `EditDate`, …) — all re-exported (`editors/__init__.py:22-41`) |
| Views    | `gramps.gui.views`          | `PageView`, `NavigationView`, `ListView` — base classes shipped views subclass |
| Widgets  | `gramps.gui.widgets`        | `MonitoredEntry`, `DateEntry`, `BasicLabel`, `LinkBox`, fan-chart widgets, the gramplet bar/pane, … |
| Dialogs  | `gramps.gui.dialog`         | `OkDialog`, `ErrorDialog`, `WarningDialog`, `QuestionDialog`/`QuestionDialog2`, `OptionDialog`, `SaveDialog` (`dialog.py:62-355`) |
| Windows  | `gramps.gui.managedwindow`  | `ManagedWindow` — base for every modal Gramps window (`managedwindow.py:357`) |
| Plug GUI | `gramps.gui.plug`           | `tool.Tool` / `BatchTool` / `ActivePersonTool` (`tool.py:80-143`); `quick.QuickTable`; report/export dialog drivers |
| App state| `gramps.gui.displaystate`   | `DisplayState`, the `History` (emits `active-changed`, `mru-changed`) |

Editing an existing view or editor is normal core work. When you add logic that
isn't intrinsically about GTK display, push it into a `gen`-only module so it can
be unit-tested without a display and survives the next minor.

## gramps.plugins.* — shipped plugins

The bundled reports, tools, gramplets, views, importers/exporters, and the
concrete db backend. Also in scope for core, also unstable.

| Subpackage | Contents |
|------------|----------|
| `gramps.plugins.db.dbapi`     | The SQLite/DB-API backend implementing `DbGeneric` |
| `gramps.plugins.textreport`   | Built-in text reports |
| `gramps.plugins.drawreport`   | Built-in graphical reports |
| `gramps.plugins.graph`        | Graphviz reports |
| `gramps.plugins.webreport`    | Narrative website |
| `gramps.plugins.gramplet`     | Shipped gramplets |
| `gramps.plugins.tool`         | Shipped tools |
| `gramps.plugins.view`         | Shipped views |
| `gramps.plugins.importer` / `gramps.plugins.export` | GEDCOM, CSV, XML, … |
| `gramps.plugins.lib`          | Shared plugin helpers (e.g. `libnarrate`, `libgedcom`) |
| `gramps.plugins.rel`          | Per-language relationship calculators |

A shipped plugin is registered through a `.gpr.py` file using the registry
grammar in `gramps.gen.plug`. Note `.gpr.py` files are excluded from
`mypy` (`mypy.ini`), so type annotations there are not checked.

## Simple Access — SimpleAccess / SimpleDoc

A high-level convenience layer that hides handles and refs, used by Quick Views.

| Symbol | Module | Role |
|--------|--------|------|
| `SimpleAccess` | `gramps.gen.simple` (`_simpleaccess.py`) | Read interface that resolves handles/refs for you |
| `SimpleDoc`    | `gramps.gen.simple` (`_simpledoc.py`)    | Matching write interface — `title`, `paragraph`, `header1`, … |
| `SimpleTable`  | `gramps.gen.simple` (`_simpletable.py`)  | Result table model |

The clickable Quick View result table, `QuickTable`, lives under
`gramps.gui.plug.quick` and is GUI-coupled. See the upstream
[Simple Access API](wiki:Simple_Access_API) page.

## Stability summary

| Surface | Promise | Implication |
|---------|---------|-------------|
| `gramps.gen.*` | Stable contract; deliberate, documented breaks only | Build on it; this is what `gen`'s self-containment buys you |
| `gramps.gui.*` | Moves between minors, no compatibility promise | Edit freely as core, but factor stable logic down into `gen` |
| `gramps.plugins.*` | Moves between minors, no compatibility promise | Same — keep shared logic in `gramps.plugins.lib` or `gen` |

What actually changes across releases — renames, removed accessors, signal
churn — is tracked in [[14-compatibility]].

## See also

- [[05-fundamentals]] — the cross-cutting concepts (logging, translation, signals) backed by this surface.
- [[06-data-access]] — patterns over the DB API and the per-object field inventory.
- [[14-compatibility]] — what changes across Gramps versions in this surface.
- [[16-guidelines]] — the normative rules (imports, `mypy`, `black`, i18n, tests, commits).
- [Report API](wiki:Report_API), [Report Generation](wiki:Report_Generation) — standalone wiki references for the docgen subsystem.
- [Signals and Callbacks](wiki:Signals_and_Callbacks), [Simple Access API](wiki:Simple_Access_API) — standalone wiki pages.
- [Gramps Developer Reference](https://gramps-project.org/docs/) — upstream Sphinx-generated API docs.

<!--wiki:{{stub}}-->
