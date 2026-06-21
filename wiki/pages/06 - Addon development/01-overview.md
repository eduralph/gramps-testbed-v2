---
title: "Gramps 6.0 Wiki Manual - Addon Development"
categories: ["Addons", "Developers", "Gramps 6.0"]
managed: true
---

[Index](wiki:Gramps 6.0 Wiki Manual - Addon Development) · [Next →](wiki:Gramps 6.0 Wiki Manual - Addon Development - Getting Started)

## Overview

A Gramps **addon** extends the application without modifying core. You add a feature, ship it on your own schedule, and users install it from the in-app Plugin Manager — no fork of Gramps, no waiting on a core release to put new functionality in front of people. An addon is just a folder of Python on the plugin path, so the barrier to entry is low; the trade-off is that you build against Gramps' API and track it across versions. This is how most of Gramps' reports, tools, and gramplets are delivered, and the same door is open to you.

Addons are discovered from the plugin directory; see [the addon list](wiki:6.0_Addons) for what ships today.

**New with 6.1**: plugin discovery follows symlinks (with realpath-based dedup to prevent infinite recursion on symlink loops), so a symlinked addon folder loads correctly.

This page is the **start point** for the section: a map to every other page, then the anatomy and minimal shape of an addon. The normative MUST / SHOULD rules every addon is held to live in [[16-guidelines]].

## Start here

**New to addon development?** Read these in order — from your first loaded addon to a tested, rules-compliant one:

[[02-get-started]] → [[04-addon-kinds]] → [[05-fundamentals]] → [[06-data-access]] → [[08-testing]] → [[16-guidelines]]

**Looking for something specific?** Jump straight to it:

| If you want to… | Go to |
|-----------------|-------|
| Install the tooling and see your first addon load | [[02-get-started]] |
| Follow an end-to-end walkthrough for your addon kind | [[03-tutorials]] |
| Choose which kind of addon to build | [[04-addon-kinds]] |
| Learn the cross-cutting basics — `.gpr.py`, discovery, `_()`, logging, lifecycle | [[05-fundamentals]] |
| Read from or write to the database | [[06-data-access]] |
| Look up the `gramps.gen` API an addon may import | [[07-api-reference]] |
| Write and run tests | [[08-testing]] |
| Debug an addon that isn't behaving | [[09-debug]] |
| Diagnose a common failure mode | [[10-troubleshoot]] |
| Pass the static checks (Black, ruff) | [[11-code-analysis]] |
| Translate your addon's strings | [[12-internationalization]] |
| Package and submit your addon | [[13-packaging]] |
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

…plus filter rules, sidebars, map providers, relationship calculators, citation formatters, docgen output backends, and more. The full catalogue — with the registration fields and base class each kind needs — is [[04-addon-kinds]].

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

What you build next depends on the **kind** — Gramplet, View, Report, Tool, Importer/Exporter, Quick View, and more — each adding its own registration fields and base class. Choose one in [[04-addon-kinds]]; the full `.gpr.py` field reference and the discovery model are in [[05-fundamentals]].

## Minimal registration

A Gramplet — the lightest kind — needs only this in its `.gpr.py`:

```python
register(
    GRAMPLET,
    id="Example",
    name=_("Example"),
    version="1.0.0",
    gramps_target_version="6.0",
    fname="example.py",
    gramplet="Example",
)
```

[[02-get-started]] turns this into a running addon in a few minutes; [[05-fundamentals]] explains every field and the lifecycle hooks the implementation overrides.

<!--wiki:{{stub}}-->
