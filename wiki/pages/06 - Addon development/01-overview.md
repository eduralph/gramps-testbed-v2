---
title: "Gramps 6.0 Wiki Manual - Addon Development"
categories: ["Addons", "Developers", "Gramps 6.0"]
managed: true
---

[Index](wiki:Gramps 6.0 Wiki Manual - Addon Development) · [Next →](wiki:Gramps 6.0 Wiki Manual - Addon Development - Tutorials)

## Overview

A Gramps **addon** extends the application without modifying core. You add a feature, ship it on your own schedule, and users install it from the in-app Plugin Manager — no fork of Gramps, no waiting on a core release to put new functionality in front of people. An addon is just a folder of Python on the plugin path, so the barrier to entry is low; the trade-off is that you build against Gramps' API and track it across versions. This is how most of Gramps' reports, tools, and gramplets are delivered, and the same door is open to you.

Addons are discovered from the plugin directory; see [the addon list](wiki:6.0_Addons) for what ships today.

This page is the **start point** for the section: first a map to every other page, then everything a first-time author needs to go from "Gramps is installed" to "my addon shows up in the menu" — anatomy, prerequisites, and a minimal working Gramplet. The normative MUST / SHOULD rules every addon is held to live in [[16-guidelines]].

## The section at a glance

**New to addon development?** Work through this page, then read in order — from your first loaded addon to a tested, rules-compliant one:

*this page* → [[03-addon-kinds]] → [[04-fundamentals]] → [[05-data-access]] → [[07-testing]] → [[16-guidelines]]

**Looking for something specific?** Jump straight to it:

| If you want to… | Go to |
|-----------------|-------|
| Install the tooling and see your first addon load | *this page, below* |
| Follow an end-to-end walkthrough for your addon kind | [[02-tutorials]] |
| Choose which kind of addon to build | [[03-addon-kinds]] |
| Learn the cross-cutting basics — `.gpr.py`, discovery, `_()`, logging, lifecycle | [[04-fundamentals]] |
| Read from or write to the database | [[05-data-access]] |
| Look up the `gramps.gen` API an addon may import | [[06-api-reference]] |
| Write and run tests | [[07-testing]] |
| Debug an addon that isn't behaving | [[08-debug]] |
| Diagnose a common failure mode | [[09-troubleshoot]] |
| Pass the static checks (Black, ruff) | [[10-code-analysis]] |
| Translate your addon's strings | [[11-internationalization]] |
| Package and submit your addon | [[12-packaging]] |
| List, announce, and support your published addon | [[13-community]] |
| Port across Gramps versions | [[14-compatibility]] |
| See per-version changes that affect addons | [[15-whats-new]] |
| Know the rules to follow — and to cite in review | [[16-guidelines]] |
| See what's planned, or propose a change | [[17-roadmap]] |

The one page to bookmark is [[16-guidelines]] — the normative MUST / SHOULD / MAY reference every addon is held to.

## What an addon can extend (at a glance)

Almost every part of the Gramps UI is a plugin point. The common kinds:

| Kind | Adds | Shows up in |
|------|------|-------------|
| **Gramplet** | a lightweight widget over the current selection | Dashboard / sidebar |
| **View** | a full alternative way to browse the tree | main view area |
| **Report** | text or graphical output (PDF, HTML, ODF, …) | Reports menu |
| **Tool** | an operation over the database | Tools menu |
| **Importer / Exporter** | reading or writing an external format | File → Import / Export |
| **Quick View** | a one-call report on a selected object | right-click menus |

…plus filter rules, sidebars, map providers, relationship calculators, citation formatters, docgen output backends, and more. The full catalogue — with the registration fields and base class each kind needs — is [[03-addon-kinds]].

## Anatomy of an addon

An addon is a folder under Gramps' user plugin directory — one folder per addon — holding at minimum a registration file and an implementation module:

| File | Purpose |
|------|---------|
| `<Addon>.gpr.py` | Registration: id, name, version, Gramps target, kind, entry point |
| `<Addon>.py` | The implementation Gramps loads on demand |
| `po/` | Translation catalogs (optional) |
| `tests/` | Unit tests (optional, recommended) |

At startup Gramps scans every `.gpr.py` and builds a metadata catalog from the `register(...)` call(s); the implementation module named by `fname` loads **lazily**, on first use. The consequence to remember: an error in `.gpr.py` hides the addon entirely, while an error in the implementation only surfaces when the addon is invoked.

The registration declares the Gramps version it targets (`gramps_target_version`) — an addon on `maintenance/gramps60` expects the 6.0 API; see [[14-compatibility]] for cross-version concerns.

What you build next depends on the **kind** — Gramplet, View, Report, Tool, Importer/Exporter, Quick View, and more — each adding its own registration fields and base class. Choose one in [[03-addon-kinds]]; the full `.gpr.py` field reference and the discovery model are in [[04-fundamentals]].

## Prerequisites

| Requirement | Why |
|-------------|-----|
| Gramps 6.0 installed and runnable | The target you're developing against |
| Python 3.10+ | Matches Gramps 6.0's minimum |
| A text editor or IDE | Any will do; Gramps doesn't impose one |
| Familiarity with Python imports and packages | Addons are Python modules |

You do **not** need to build Gramps from source for addon work. Addons load from the user plugin directory and are picked up at next start.

## Where addons live

Each addon is a folder under Gramps' user plugin directory, one folder per addon. The exact path is platform-specific; see [the Addons page](wiki:6.0_Addons) for the canonical locations. The folder name must be a valid Python import name (no spaces — addons share code via `import <FolderName>`); it need **not** match the registration `id`, which is an independent plugin key ([[16-guidelines]] → Structure).

On Gramps 6.0, plugin discovery does **not** follow symlinks — the addon must be physically present under the plugin path, so the development loop is copying (or `rsync`ing) from your working tree on save.

**Changed in 6.1**: plugin discovery follows symlinks (with realpath-based dedup against symlink loops), so you can `ln -s <working-tree>/<Addon>` into the user plugin directory and edit in place. Windows users: the 6.1 symlink test is skipped on Windows because the platform's symlink behavior is inconsistent without elevated privileges; the `rsync`/copy loop remains the safe default there. (gramps commit `9443dcbb30` on `maintenance/gramps61`.)

## Your first addon: a minimal Gramplet

A *Gramplet* is the lightest-weight addon kind — a sidebar widget. Two files are enough.

### 1. Create the addon folder

Make a folder named `HelloGramplet` under the user plugin directory.

### 2. Add the registration file

Save this as `HelloGramplet/HelloGramplet.gpr.py`:

```python
register(
    GRAMPLET,
    id="HelloGramplet",
    name=_("Hello Gramplet"),
    description=_("A minimal example Gramplet"),
    version="1.0.0",
    gramps_target_version="6.0",
    status=STABLE,
    fname="hellogramplet.py",
    gramplet="HelloGramplet",
    gramplet_title=_("Hello"),
)
```

The `id` is the addon's stable identifier. `fname` is the implementation module. `gramplet` is the class inside it that Gramps will instantiate.

### 3. Add the implementation

Save this as `HelloGramplet/hellogramplet.py`:

```python
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.plug import Gramplet

_ = glocale.get_addon_translator(__file__).gettext


class HelloGramplet(Gramplet):
    def init(self):
        self.set_text(_("Hello from your first Gramplet!"))
```

`init()` is the construction hook — Gramps calls it once when the Gramplet is first shown. The `_ = glocale...` line binds the translation function for this module — see [Translation](#translation) below.

### 4. Restart Gramps

Plugin discovery happens at startup. After the restart, the new Gramplet appears under *View → Sidebar* (or the Dashboard, depending on view).

## Reload / test cycle

There is no hot-reload for addons. The development loop is:

1. Edit the source.
2. Sync the change into the plugin directory (or work directly there).
3. Restart Gramps.
4. Observe.

For faster iteration on non-GUI logic, write a `unittest`-based test alongside the addon and run it without launching Gramps — see [[07-testing]] for the conventions.

## Translation

Wrap every user-visible string in `_()` so it can be translated:

```python
self.set_text(_("Hello from your first Gramplet!"))
```

`_` is set up differently in the two files. In `.gpr.py` it is injected by the plugin loader — just use it, never import it. In the implementation module nothing is injected: bind it explicitly at the top of the file, as the walkthrough's `hellogramplet.py` does:

```python
from gramps.gen.const import GRAMPS_LOCALE as glocale

_ = glocale.get_addon_translator(__file__).gettext
```

Translation catalogues live in a per-addon `po/` directory — optional for a first experiment, required for an addon you intend to share; [[11-internationalization]] covers the workflow.

## Next steps

- [[02-tutorials]] — end-to-end walkthroughs per addon kind; read a similar addon's source as your second tutorial ([6.0 Addons](wiki:6.0_Addons) lists what exists).
- [[03-addon-kinds]] — choose the kind of addon to build; registration fields and base class per kind.
- [[04-fundamentals]] — every `.gpr.py` field, the discovery model, and the lifecycle hooks the implementation overrides.
- [[07-testing]] — unit-test conventions and the `tests/` package layout.
- [Addons development](wiki:Addons_development) — cross-version porting notes and the wider development reference.

<!--wiki:{{stub}}-->
