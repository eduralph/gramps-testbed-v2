# Build notes — issue 8796 (viewmanager-empty-views-indexerror)

## Root cause (verified on target branch `gramps-6.1` = upstream/maintenance/gramps61)

Hiding **every** view plugin leaves `ViewManager.get_available_views()` returning
`[]`. The startup chain in `init_interface` (`gramps/gui/viewmanager.py:639-645`) then:

1. `self.views = self.get_available_views()` → `[]` (`:639`)
2. `defaults = views_to_show(self.views, …)` → `views_to_show([])` returns
   `(0, 0, [])` because `default_cat_views = [0] * len(views)` collapses to `[]`
   (`:1832`, verified by probe: `views_to_show([], use_last=False) == (0, 0, [])`).
3. `self.current_views = defaults[2]` → `[]` (`:641`)
4. `self.goto_page(defaults[0], defaults[1])` → `goto_page(0, 0)` (`:645`)

`goto_page` (`:920-927`) with a non-`None` `view_num` executes
`self.current_views[cat_num] = view_num` (`:927`) on the empty list →
`IndexError: list assignment index out of range`. Reproduced directly via probe
against the unpatched target tree (real `ViewManager.goto_page`).

The same empty-view state also leaves `self.active_page = None` (`:214`), so the
follow-on `config_view` (`:1501`, `self.active_page.configure()`) would raise
`AttributeError` if invoked — the cascade the brief names.

## The fix (minimal, restores the named invariant — totality over zero views)

Two guards, both expressing "no available views ⇒ no active page, no exception":

- `goto_page` (`gramps/gui/viewmanager.py:920`, after the patch): early
  `if not self.views: return None`. This is the startup-crash fix — the
  navigation entry point becomes total over `len(self.views) == 0`. `self.views`
  is the correct discriminator (it is `[]` exactly when `current_views` is `[]`,
  and is the semantic "available views" set).
- `config_view` (`:1497`, after the patch): `if self.active_page is None: return`
  before dereferencing it — the follow-on cascade the brief lists in scope.

`__change_page` (`:1040-1051`) is **not** touched: it already carries a
`try/except IndexError` (bugs 12304/12429/12623/12695) and, with `goto_page`
guarded, is unreachable in the all-views-hidden scenario (no view ⇒ no
navigable entry to trigger a page change). Touching it would be speculative —
no reachable path, nothing to test. Minimalism (`docs/principles.md` §1.1) says
leave it.

## Why a guard, not a deeper restructure

The invariant to restore is degenerate-input totality of the navigation path, and
the cause *is* the unguarded index/deref on the empty set. The guard removes the
cause at the exact site (`:927` / `:1501`), it is not a probe placed away from the
fault. An alternative — forcing "at least one view always loaded" or warning before
hiding the last view — is explicitly out of scope (Plugin-Manager UX / plugin-hiding
semantics) and would touch plugin registration rather than restore startup totality.

## Test design — drives the **real** production path, headless

`gramps/gui/test/viewmanager_test.py` exercises the real
`gramps.gui.viewmanager.views_to_show` and `ViewManager.goto_page` / `config_view`
— the same functions `init_interface` chains — not a parallel re-implementation
(`docs/principles.md` §3.4; avoids the issue-8653 mirror trap).

The C4 runner is **headless** and `viewmanager.py` does `from gi.repository import
Gtk` plus a tree of `gramps.gui.*` widget imports; importing it for real would need
a GTK typelib + display and crash the runner. Following the issue-13636 pattern, the
test stubs `gi` and the `gramps.gui` widget submodules in `sys.modules` **before**
import (base classes `CLIManager` / `ManagedWindow` are given real-type stand-ins so
the `class ViewManager(CLIManager)` / `class QuickBackup(ManagedWindow)` statements
execute). The module body then runs and defines the **real** `ViewManager`
and `views_to_show`; the test builds a `ViewManager` via `__new__` (bypassing the
GTK `__init__`) and sets exactly the attributes `init_interface` establishes before
calling `goto_page`.

Because the test drives the real reverted production code in the red pass, the red
failure is the **genuine** `IndexError: list assignment index out of range` at
`viewmanager.py:927` (and `AttributeError` at `:1501`), not a weaker ImportError —
confirmed in the C4 red-check output. An extracted-new-module seam was rejected
precisely because its red pass would surface only an ImportError (the new module is
removed when prod is reverted), proving nothing about the actual bug.

## Verification

`run-verify.sh` (core, gramps 6.1.0 upstream worktree): EXIT=0 —
`green-with-fix=PASS` (3 tests OK) / `red-without-fix=PASS` (genuine IndexError +
AttributeError with the production guards reverted).

`black 26.5.0` clean on both touched files (test reformatted by black before the
patch was cut; `viewmanager.py` left unchanged by black) — commit-ready for gramps'
pre-commit hook.

## Scope / target

- Target: `gramps-project/gramps @ maintenance/gramps61` (core fix), per brief +
  INTEGRATION §2. Patch cut from the clean upstream worktree `gramps-6.1`.
- Out of scope (untouched): Plugin-Manager UX, "always keep one view", plugin-hiding
  semantics, view registration.
