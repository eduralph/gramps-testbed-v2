---
title: "Gramps 6.1 Wiki Manual - Core Development - Fundamentals"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

## Overview

The cross-cutting concerns every Gramps **core** contributor hits, no matter which corner of `gramps-project/gramps` they're working in: the plugin registry seen from the inside, the signal/callback system, the config manager, logging, translation setup, and the transaction discipline for writes. The other section pages assume this background; where one of them leans on a piece described here, this is the page it points back to.

These mechanisms are the *same code* used throughout the program — `Callback`, `DbTxn`, `register()`, the config manager all live in `gramps.gen.*`. A core contributor often *maintains* them, not just calls them — e.g. the scanner that executes `register()` rather than a single registration. The normative MUST/SHOULD rules are not restated here; they live in [[16-guidelines]] and are the page to cite in review. This page is the how-and-why.

## The plugin system from core's side

Core ships ~all of its reports, tools, gramplets, views, importers, exporters, and quick views as plugins — they live under `gramps/plugins/` and register through the same framework. So the registry is not a niche subsystem; it's how the whole feature surface is wired up.

### How `register()` builds the catalog

At startup the plugin scanner walks every `.gpr.py` it finds and `exec`s it in a prepared namespace. That namespace is built by `make_environment()` (`gramps/gen/plug/_pluginreg.py:1272`), which injects the names the `.gpr.py` relies on — `register`, `newplugin`, `_`, the kind and status constants — so a registration file imports almost nothing.

`register(ptype, **kwargs)` itself is small (`_pluginreg.py:1249`). It creates a fresh `PluginData` via `newplugin()`, stamps the plugin type onto it, then copies each keyword onto the object:

```python
def register(ptype, **kwargs):
    plg = newplugin()
    plg.ptype = ptype
    for prop, value in kwargs.items():
        getattr(plg, prop)      # validates the attribute exists
        setattr(plg, prop, value)
    return plg
```

The `getattr(plg, prop)` before the `setattr` is a guard, not a no-op: it raises `AttributeError` if the `.gpr.py` used a field name `PluginData` doesn't define, so a typo'd registration key fails loudly at scan time rather than silently doing nothing. When you add a new registration field, you add it to `PluginData` (the `PluginRegister` machinery, `_pluginreg.py:1346`) — otherwise every `.gpr.py` that sets it raises.

The result is a **metadata-only catalog**. The module named by `fname` is *not* imported during the scan; it loads lazily on first invocation. This split governs core diagnostics:

- A `SyntaxError` or bad import in a `.gpr.py` removes the plugin from the catalog entirely — it never appears in any menu.
- A failure inside the `fname` module only surfaces when something triggers the plugin, as a traceback in the Plugin Manager and the log.

### Plugin kinds

The kind constant is the first positional argument to `register()`. The full set is the `*_KEY`-style block at `_pluginreg.py:82-98`:

| Constant | Value | What it registers |
|----------|-------|-------------------|
| `REPORT` | 0 | A report (`reportclass` + `optionclass`) |
| `QUICKVIEW` | 1 | A quick view (`runfunc`); `QUICKREPORT` is the deprecated alias |
| `TOOL` | 2 | A tool (`toolclass` + `optionclass`) |
| `IMPORT` | 3 | An importer |
| `EXPORT` | 4 | An exporter |
| `DOCGEN` | 5 | A document generator backend |
| `GENERAL` | 6 | A general-purpose plugin |
| `MAPSERVICE` | 7 | A map service |
| `VIEW` | 8 | A view |
| `RELCALC` | 9 | A relationship calculator |
| `GRAMPLET` | 10 | A gramplet |
| `SIDEBAR` | 11 | A sidebar |
| `DATABASE` | 12 | A database backend |
| `RULE` | 13 | A custom filter rule |
| `THUMBNAILER` | 14 | A thumbnailer |
| `CITE` | 15 | A citation formatter |

Status (`UNSTABLE=0`, `EXPERIMENTAL=1`, `BETA=2`, `STABLE=3`, `_pluginreg.py:62-65`) and audience (`EVERYONE=0`, `EXPERT=1`, `DEVELOPER=2`, `_pluginreg.py:75-77`) are independent of kind. Note the audience constant is `EVERYONE`, never `ALL` — an outdated wiki page documents `ALL`, but the code has only ever defined `EVERYONE`.

The per-kind required fields are validated and expanded by the `expand_*` helpers in the same module. When you change what a kind requires, that's the code to change, and the [[07-api-reference]] page is where the supported surface is curated.

### The `gen` self-containment constraint

`_pluginreg` lives in `gramps.gen` because the headless core (CLI, tests, the DB-API) needs to enumerate plugins without a GUI. That places it under the hard rule that **`gramps.gen.*` imports no other Gramps submodule** ([[16-guidelines]] §Source structure; `gramps/AGENTS.md` §Submodule Import Rules). If a registry change reaches for something in `gramps.gui`, it's in the wrong layer — the GUI-side plugin handling belongs in `gramps.gui.plug`.

## Signals and callbacks

Gramps' internal event system lets one part of the program react when another changes state — the DB tells views a person was committed, `dbstate` tells everyone the active database swapped, the config manager tells listeners a setting changed. This is the **strong source** for the section: get it wrong and you leak callbacks into freed objects, or you read a half-updated database mid-transaction.

It is a distinct system from GTK's own signals. GTK widgets use GLib/GObject signals; the objects below use Gramps' own `Callback` base class. They look similar (`connect`/`disconnect`/`emit`) but do not interoperate.

### The `Callback` base class

The machinery is the `Callback` class in `gramps/gen/utils/callback.py:51`. It's a **mix-in**: a class that wants to emit signals subclasses it and declares the signals it offers in a class-level `__signals__` dict. The generic DB (`DbGeneric`), the view `History`, `dbstate`, `uistate` and others all inherit it, which is why they share an identical signalling API.

| Method | Signature | Role |
|--------|-----------|------|
| `connect` | `connect(signal_name, callback)` → key | Register `callback` for `signal_name`; returns an opaque key (`callback.py:268`) |
| `disconnect` | `disconnect(key)` | Remove the one callback registered under `key` (`callback.py:296`) |
| `disconnect_all` | `disconnect_all()` | Drop every callback on this object (`callback.py:313`) |
| `emit` | `emit(signal_name, args=tuple())` | Fire `signal_name`; `args` is a **tuple** matching the signal's declared signature (`callback.py:321`) |

Two behaviours are worth knowing because they hide bugs:

- **`connect` to an unknown signal does not raise.** It logs a warning and returns `None` (`callback.py:277-281`). So a typo in a signal name silently never fires, and the `None` you stored is a useless disconnect key. Spell the signal name exactly.
- **`emit` to an unknown signal also does not raise** — it warns with the caller's file/line (`callback.py:335-341`). A green run is not proof your `emit` reached anyone.

### connect / disconnect / emit in practice

The canonical pattern: connect on setup, store the key, disconnect on teardown.

```python
# in setup / db_changed
self.cb_key = self.dbstate.db.connect("person-update", self.cb_person_changed)

def cb_person_changed(self, handle_list):
    for handle in handle_list:
        ...  # the DB is fully committed here; re-reading is safe

# in close / cleanup
self.dbstate.db.disconnect(self.cb_key)
```

`emit` carries arguments as a tuple — note the trailing comma for a single argument:

```python
self.emit("person-update", (handle_list,))
```

Callback method names take the `cb_` prefix by convention ([[16-guidelines]] §Coding style; `gramps/AGENTS.md` §Callbacks); it also suppresses pylint's unused-argument warning when a signal hands you arguments you don't use.

Failing to `disconnect` is the classic core leak: the emitting object keeps a reference to your bound method, your object never dies, and once the database it pointed into is gone the next `emit` calls into stale state. Disconnect on teardown, and disconnect-then-reconnect on `db_changed` — the signals are bound to a *specific* database object, not to "the database" abstractly.

### CallbackManager — bulk subscriptions with handle filtering

When a single consumer needs many object types' signals, or only cares about a known set of handles, `CallbackManager` in `gramps/gen/utils/callman.py:111` is the higher-level tool. It wraps `Callback.connect`, tracks every key it opened so one `disconnect_all()` tears the whole thing down, and — crucially — *filters by handle* so a listener isn't woken for objects it doesn't care about.

It is instantiated against a specific database; when the database changes, throw the manager away and build a new one.

```python
from gramps.gen.utils.callman import CallbackManager

self.callman = CallbackManager(self.dbstate.db)

# register handlers — a full signal name, or a bare object type
# (which fans out to add/delete/update/rebuild for that type)
self.callman.register_callbacks({
    "person-delete": self.cb_person_deleted,
    "family":        self.cb_family_changed,   # all family-* transaction signals
})

# only now are the DB connects actually made:
self.callman.connect_all(keys=["person", "family"])

# optionally narrow to specific handles:
self.callman.register_handles({"person": [handle1, handle2]})

# teardown — one call disconnects everything it opened:
self.callman.disconnect_all()
```

The valid object-type keys are the module-level `KEYS` list (`callman.py:55`); pass `keys=callman.KEYS` to connect for all of them. `register_callbacks` must run *before* `connect_all` — the registration only records intent; `connect_all` is what touches the DB (`callman.py:226`, `callman.py:247`). For a one-off connect outside the managed object types, `add_db_signal(name, callback)` (`callman.py:312`) routes a custom DB connect through the same `disconnect_all` bookkeeping so you don't hand-track its key.

### The db-change signals

The signals you'll consume most are emitted by the database on commit. They follow `<objecttype>-<change>`, where the object type is one of person, family, event, place, media, source, citation, repository, note, tag, and the change is `add`, `update`, `delete`, or `rebuild`.

| Source | Signal | When / argument |
|--------|--------|-----------------|
| `dbstate.db` | `person-add`, `family-add`, … | One or more added. Arg: list of handles. |
| `dbstate.db` | `person-update`, `family-update`, … | One or more updated. Arg: list of handles. |
| `dbstate.db` | `person-delete`, `family-delete`, … | One or more deleted. Arg: list of handles. |
| `dbstate.db` | `person-rebuild`, `family-rebuild`, … | Mass change (import, repair). No args. |
| `dbstate.db` | `home-person-changed` | Home person changed. No args. |
| `dbstate.db` | `person-groupname-rebuild` | Args: name, group. |
| `dbstate` | `database-changed` | Active DB swapped. Arg: the new db. |
| `dbstate` | `no-database` | No DB is open. |
| `uistate` | `nameformat-changed`, `filter-name-changed`, `filters-changed`, … | UI preference changes. |
| view history | `active-changed` | Selected object changed. Arg: the new handle. |

The authoritative inventory is the `__signals__` block at the head of `gramps/gen/db/generic.py` plus the `dbstate`/`uistate` classes; [Signals and callbacks](wiki:Signals_and_Callbacks) is the prose reference. `request_rebuild()` on the DB is how a tool that made mass changes asks the UI to refresh via the `*-rebuild` signals.

### Deferred-until-commit ordering

This is the subtle part, and it's the reason `cb_*` handlers may re-read the database safely. **The DB does not emit per-object signals as the transaction runs.** It accumulates them and emits them only *after* the transaction commits — so a transaction that fails emits nothing, and a handler never sees a half-applied change.

The emission order is deterministic, set in `TransactionImpl.undo_sigs` (`gramps/gen/db/generic.py:290`):

1. **By change type:** deletes first, then adds, then updates — the literal `for trans_type in [TXNDEL, TXNADD, TXNUPD]` (`generic.py:296`).
2. **Within each type, by object key:** `for obj_type in range(11)` (`generic.py:297`), which is the `*_KEY` order from `gramps/gen/db/dbconst.py:86-96` — person (0), family (1), source (2), event (3), media (4), place (5), repository (6), note (8), tag (9), citation (10).
3. Updates skip any handle also deleted in the same transaction (`generic.py:311-315`), so you never get an `-update` for an object that's gone.
4. The **same ordering is replayed on undo and redo** (the `undo` flag swaps add/delete emits; `generic.py:300-318`), so a handler sees identical signal sequences whether the user is doing or undoing.

The practical consequence is the family-merge trap documented in the strong source: a handler that re-reads a *family* the moment a `person-delete` arrives can hit an object already deleted later in the same commit. The fix is to connect to the signals that describe the surviving state — `family-update` and `person-update` — rather than trying to react cleverly to a `delete`. Because deletes lead and updates trail, by the time the `-update` fires the DB is in its final, consistent post-commit state.

## The config manager

Persistent settings live in `gramps.gen.config`, which exposes a singleton `config` (`gramps/gen/config.py:465`, the module-level `CONFIGMAN`) plus thin module functions over it. The class itself is `ConfigManager` in `gramps/gen/utils/configmanager.py:71`.

The core idiom is register-then-use. A setting must be registered with a key and a default before it can be read or written:

```python
from gramps.gen.config import config

config.register("interface.foo-width", 800)   # key + default
config.load()                                  # read the stored file
width = config.get("interface.foo-width")
config.set("interface.foo-width", 1000)
config.save()
```

`register(key, value)` / `get(key)` / `set(key, value)` / `load()` / `save()` are the module-level wrappers (`config.py:70`, `:75`, `:100`, `:133`, `:110`). For a *separate* settings namespace with its own file, `config.register_manager(name)` (`configmanager.py:125`) returns an independent manager — core uses it for plugin-local settings.

The config manager is **itself a signal source.** Its `connect`/`disconnect`/`emit` (`configmanager.py:507`, `:523`, `:534`) use the config key *as the signal name*, so code can react to a setting changing:

```python
config.connect("interface.foo-width", self.cb_width_changed)
```

When adding a new core setting, register it where the rest of that subsystem's keys are registered (so the default exists before any read), and remember a key that's read before it's registered raises rather than returning the default.

## Logging

Use a module-level logger; **never `print()` for diagnostics** ([[16-guidelines]] §Runtime; `gramps/AGENTS.md` §Logging). The idiom at the top of a core file:

```python
import logging

LOG = logging.getLogger(__name__)

LOG.debug("Reached the interesting branch with n=%d", n)
LOG.warning("Skipping malformed event %s", event.gramps_id)
```

`gramps/AGENTS.md` §Logging shows exactly `LOG = logging.getLogger(__name__)`; that's the canonical core form for a new module. Some older core code instead uses the dotted root-logger convention (`logging.getLogger(".")` and named children like `logging.getLogger(".locale")`) so the whole tree descends from the root logger Gramps configures at startup; [[09-debug]] covers that style and how to target a single logger. Use `%`-style lazy arguments (`LOG.debug("...%d", n)`, not an f-string) so the message isn't formatted when the level is disabled, and so it stays out of the translation pipeline. Output reaches the Gramps log window and stderr; [[09-debug]] covers enabling per-logger levels and reading the log.

## Translation setup in core modules

Every user-visible string is wrapped with `_()` ([[16-guidelines]] §Translation; `gramps/AGENTS.md` §Internationalization). A core module binds `_` once at the top from the global Gramps locale:

```python
from gramps.gen.const import GRAMPS_LOCALE as glocale

_ = glocale.translation.gettext
```

This is the verified pattern across core — e.g. `gramps/gen/lib/person.py:33,53` and `gramps/gen/db/generic.py:48,121`. Some modules instead bind `glocale.translation.sgettext` (the "stripped" variant that handles the `_("Source", "context")` disambiguation form) — `gramps/gen/lib/eventtype.py` is one. Pick `sgettext` when the module uses context-qualified strings.

The rules these calls must satisfy (all in [[16-guidelines]] §Translation, restated only as reminders):

- Use `ngettext(singular, plural, n)` for anything with a count.
- Prefer the `_(string, context)` alias over `pgettext(context, message)` (`gramps/AGENTS.md` §Internationalization).
- Use `N_("…")` to *mark* a module-level constant for extraction without translating it at definition time; translate it with `_()` where it's displayed.
- **Never** wrap a dynamically built string — `_(f"...")` or `_("...".format(...))` — because `xgettext` can't extract it. Build with `_("...%s") % value`.

And the file-bookkeeping rule: when you add or remove a `.py` file, hand-edit `po/POTFILES.in` (has translatable strings) or `po/POTFILES.skip` (doesn't), and check with `PYTHONPATH=../../gramps python po/test/po_test.py` ([[16-guidelines]] §Adding and removing Python files).

## Transactions: the write discipline

Reading the database is unrestricted; **every write goes through a `DbTxn`** ([[16-guidelines]] §Runtime). `DbTxn` (`gramps/gen/db/txn.py:52`) is a context manager that groups commits into one unit so the undo system can roll them back atomically and so the deferred signals fire exactly once, after the whole group lands.

```python
with DbTxn(_("Set privacy"), db) as trans:
    person = db.get_person_from_handle(handle)
    person.set_privacy(True)
    db.commit_person(person, trans)
```

Three things core contributors must get right:

- **The description is user-visible** in the Undo history (`_after_commit` formats it as `_("_Undo %s") % transaction.get_description()`, `gramps/gen/db/generic.py:2313`). Wrap it in `_()`.
- **Group related writes in one transaction.** A change that touches a family and both spouses is *one* `DbTxn`, not three — otherwise undo can leave the database inconsistent, and listeners see three commits' worth of signals instead of one coherent batch. (See the marriage example in [Using database API](wiki:Using_database_API#Transactions_and_Commits).)
- **Use `batch=True` only for true mass operations** (imports, bulk tools). A batch transaction takes a faster path and, per `_after_commit`, **does not run the normal post-commit callbacks** (`generic.py:2310`) — so the UI won't auto-refresh; you signal it explicitly with `request_rebuild()`.

`commit_person` / `commit_family` / `add_*` / `remove_*` all take the open `trans` as their last argument; that's how their changes get recorded for undo and queued for the deferred emit. The full write surface, handle-vs-ID rules, and traversal helpers are in [[06-data-access]].

## See also

- [[06-data-access]] — the DB API surface: handles vs Gramps IDs, cursors, backlinks, the full transaction API.
- [[07-api-reference]] — the curated `gramps.gen.*` surface, including the plugin-registration fields per kind.
- [[09-debug]] — enabling per-logger debug levels and reading the log window.
- [[16-guidelines]] — the normative MUST/SHOULD rules these mechanisms must satisfy; the page to cite in review.
- [Signals and Callbacks](wiki:Signals_and_Callbacks) — the standalone wiki reference for the signal inventory and `CallbackManager`.
- `gramps/AGENTS.md` — the in-repo coding standard (logging, i18n, callbacks).

<!--wiki:{{stub}}-->
