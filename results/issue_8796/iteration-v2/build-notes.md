# Build notes — issue 8796 (viewmanager-empty-views-indexerror)

Iteration 2. The previous attempt's **fix logic was accepted** by sign-off
("goto_page `if not self.views: return None`; config_view `if self.active_page is
None: return` … accepted as minimal and correct — keep it"). It was rejected for
two reasons, both addressed here:

1. **The regression test leaked `sys.modules` into the shared suite.** v1 mutated
   global `sys.modules` at module-import time via `setdefault` with no restore
   (`iteration-v1/patch.diff:58-117`); under `unittest discover` (one process)
   the mocks leaked into later tests → T3 delta of 7 unit failures
   (`gramps.plugins.test.imports_test::test_imp_3_4`, …) + 1 GUI-smoke failure.
2. **C5 — the `__change_page` cascade was unguarded.** The brief puts
   `__change_page` (`:1049-1051`) in scope; v1 guarded only goto_page/config_view.

## Root cause (verified on target branch = `upstream/maintenance/gramps61`, worktree `gramps-6.1`)

Hiding **every** view plugin leaves `ViewManager.get_available_views()` returning
`[]`. The startup chain in `init_interface`
(`gramps/gui/viewmanager.py:639-645`):

1. `self.views = self.get_available_views()` → `[]` (`:639`)
2. `defaults = views_to_show(self.views, …)` → `views_to_show([])` returns
   `(0, 0, [])` because `default_cat_views = [0] * len(views)` collapses to `[]`
   (`:1832`).
3. `self.current_views = defaults[2]` → `[]` (`:641`)
4. `self.goto_page(defaults[0], defaults[1])` → `goto_page(0, 0)` (`:645`)

`goto_page` (`:920-927`) with non-`None` `view_num` runs
`self.current_views[cat_num] = view_num` (`:927`) on the empty list →
`IndexError: list assignment index out of range`. Confirmed in the C4 red pass.

## The cascade is real, not just at startup (C5)

`__change_page` is reachable in the empty-view state **after** goto_page is
guarded — via `post_load` (`:1221`): once a tree is opened,
`self.__change_page(self.notebook.get_current_page())` is called with an empty
notebook, i.e. `page_num == -1`. In `__change_page` (`:1048-1051`) **both**
`self.pages[-1]` and the existing `self.pages[0]` IndexError fallback index the
empty `self.pages` list → a fresh, **uncaught** `IndexError`. So the existing
`try/except IndexError` (bugs 12304/12429/12623/12695) does *not* cover the
empty-`pages` case. The other caller of `__change_page`, `view_changed` (`:1037`),
is the `switch-page` signal handler and *is* unreachable once goto_page returns
early (no page is ever created → no `set_current_page` → no `switch-page` signal),
but the `post_load` path is not. Hence a guard, not an unreachability argument.

## The fix — three guards restoring totality over zero available views

The brief names an **Invariant to restore**: the view-navigation path must be
total over the number of available views, *including zero* — so the target is the
smallest change that restores the invariant (principles §1.2/§2), not the smallest
diff. Each guard expresses "no available views ⇒ no active page, no exception":

- `goto_page` (`gramps/gui/viewmanager.py:924-931` after patch): early
  `if not self.views: return None`. `self.views` is the right discriminator — it
  is `[]` exactly when `current_views` is `[]`, and is the semantic
  "available views" set. (Startup crash — the original report.)
- `__change_page` (`:1054-1061` after patch): after `__disconnect_previous_page()`
  (which already handles `active_page is None`), `if not self.pages: return`,
  before indexing the empty `self.pages`. (The `post_load` cascade — C5.)
- `config_view` (`:1517-1521` after patch): `if self.active_page is None: return`
  before dereferencing it. (The configure cascade.)

### Why guards, not the rejected alternatives — with cost

The cause *is* the unguarded index/deref on the empty set; the guards remove it at
the exact fault sites (`:927`, `:1051`, `:1501`), so this is removing the cause,
not probing a symptom. The thread's alternatives are explicitly **out of scope**
in the brief and are larger, not smaller:
- "Force at least one view always loaded" — touches plugin registration / the
  `hiddenplugins` honoring in `GuiPluginManager`, changing plugin-hiding semantics
  for every reader of the loaded-plugin set; it does not restore navigation
  totality, it side-steps it.
- "Warn before hiding the last view" — a Plugin-Manager UX change in a different
  module, and it still leaves `goto_page`/`__change_page` non-total if a user
  edits `gramps.ini [plugin] hiddenplugins` by hand (the brief's repro path).

Both are design changes the brief rules out; the 3-line-each guards are the
minimal restoration of the stated invariant.

## Test design — drives the real production path, headless, and **confined**

`gramps/gui/test/viewmanager_test.py` exercises the real
`gramps.gui.viewmanager.views_to_show`, `ViewManager.goto_page`,
`ViewManager.__change_page` and `config_view` — the same functions
`init_interface` and `post_load` chain — not a parallel re-implementation
(`docs/principles.md` §3.4; avoids the issue-8653 mirror trap). Because the test
drives the reverted production code in the red pass, the red failures are the
**genuine** `IndexError`/`AttributeError` at `:927`/`:1051`/`:1501`, not a weaker
ImportError (an extracted-new-module seam was rejected for exactly that reason —
its red pass would surface only an ImportError once prod is reverted, proving
nothing about the bug).

The C4 runner is headless and `viewmanager.py` does `from gi.repository import
Gtk` plus a tree of `gramps.gui.*` widget imports, which would crash the runner.
So `gi` and the `gramps.gui` widget submodules are stubbed in `sys.modules` —
but, unlike v1, **the stubbing is confined to the test class**:
`setUpClass` starts `mock.patch.dict(sys.modules, _build_stub_modules())` and
imports the real module under it; `tearDownClass` calls `.stop()`, which restores
`sys.modules` to the snapshot taken at `start()` — removing every stub *and* the
`viewmanager` module imported under them, and restoring any real module the stub
shadowed. Nothing leaks into the shared `unittest discover` process, so the v1 T3
delta cannot recur. (Pure `gramps.gen.*` imports are import-light and left alone.)

## Verification

- **C4-verify** (`run-verify.sh`, core, gramps-6.1.0 upstream worktree): **EXIT 0**
  — `green-with-fix=PASS` (4 tests OK) / `red-without-fix=PASS` (genuine
  `IndexError` at goto_page + `IndexError` at `__change_page` + `AttributeError`
  at config_view with the production guards reverted; `test_views_to_show_empty`
  stays green as it is not the reverted code).
- **No-leak proof** (`/tmp/mech_check.py`, replicating the setUpClass/tearDownClass
  `patch.dict` lifecycle on a real importable module): after teardown the shadowed
  module identity is restored, added stub keys are gone, the module imported under
  the stubs is gone, and `set(sys.modules)` equals the pre-test snapshot. This is
  the mechanism that fixes the v1 whole-suite regression.
- **black 26.5.0**: clean on both touched files (test reformatted before the patch
  was cut; `viewmanager.py` left unchanged) — commit-ready for gramps' pre-commit.

## Not done by Do (human Check items)

- **V — manual GUI repro** on `maintenance/gramps61` (hide every view plugin,
  restart, confirm no IndexError and the window opens with no active page) remains
  the human-facing confirmation per the brief Surfaces note; it cannot run on the
  headless C4 runner.
- Whole-suite T3-baseline re-run is Check's gate; the no-leak mechanism proof above
  is the evidence that it will not delta.

## Scope / target

- Target: `gramps-project/gramps @ maintenance/gramps61` (core fix), per brief +
  INTEGRATION §2; patch cut from clean upstream worktree `gramps-6.1`.
- Out of scope (untouched): Plugin-Manager UX, "always keep one view",
  plugin-hiding semantics, view registration.
