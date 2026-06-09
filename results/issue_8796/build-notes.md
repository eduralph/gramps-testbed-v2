# Build notes — issue 8796 (iteration 4)

## What the brief asks
With **zero available views** (every view plugin hidden), Gramps must initialise
the main interface without raising. The navigation path must be **total over the
number of available views, including zero** (Invariant to restore). The brief
wants a *by-construction* fix (not a guard per consumer) plus a regression test in
`gramps/gui/test/viewmanager_test.py` that drives the **production** path, is
GUI-import-free (the C4 runner is headless), and is red→green.

## Carry-forward addressed (iter-1 → iter-3)
The **fix logic was already accepted** by sign-off (iter-3 rationale):
`views_to_show([]) -> (None, None, [])` plus the `init_interface`
`if current_cat is not None` guard. Every rejection since iter-1 was about the
**test design / validation**, not the fix:

- iter-1: test mutated global `sys.modules` at import time → leaked into the shared
  suite (7 unit + 1 smoke deltas).
- iter-2: by-construction redo of the fix (done); test still heavy.
- iter-3: fix logic accepted; the test still fabricated a `ViewManager` via
  `__new__` + ~15 hand-set attrs + ~20 stubbed `gramps.gui` modules in a subprocess
  harness. Directive: **"Keep a CLEAN unit test of the source fix as the C4 gating
  regression: call the real module-level `views_to_show([], use_last=False)` and
  assert `(None, None, [])`. No GTK stubbing, no `__new__` reconstruction."**

This iteration does exactly that.

## The seam (why a new module)
`views_to_show` lived in `gramps/gui/viewmanager.py`, which does
`from gi.repository import Gtk` (viewmanager.py:58) plus a tree of `gramps.gui.*`
widget imports. Importing it under the **headless** C4 runner core-dumps. The only
way to call the *real* `views_to_show` from a headless test — without the rejected
~20-module `sys.modules` stubbing — is to put it in a module that carries **no
`gi` / `gramps.gui` import**.

So `views_to_show` is moved verbatim into a new import-light module
`gramps/gui/viewmanagerutils.py` (imports only `gramps.gen.config`, which is
gi-free — verified: `gramps/gen/config.py:35-47` imports no `gi`). `viewmanager`
re-imports it (`viewmanager.py:80`, `from .viewmanagerutils import views_to_show`),
so **production routes through the exact function the test drives** — not a parallel
copy (principles §3.4). This is the "testable seam" the brief asks for, and it
follows the established core-test pattern (`gramps/gui/test/display_test.py` imports
the gi-free `gramps.gui.display`).

Confirmed headless: `from gramps.gui.viewmanagerutils import views_to_show; \
views_to_show([], use_last=False)` → `(None, None, [])` with plain `python3`, no
display, no `gi`.

## Source fix (by construction at the source of the empty-view state)
Target branch: `upstream/maintenance/gramps61` (worktree `gramps-6.1`).

1. **`gramps/gui/viewmanagerutils.py` (new)** — `views_to_show`, with the totality
   fix: `if not views: return None, None, default_cat_views` (was the implicit
   `default_cat_views = [0] * len(views)` collapsing to `[]` at the old
   `viewmanager.py:1832`). Returning a **None category** is the by-construction fix:
   the empty-view state can no longer masquerade as "category 0 exists", so the
   whole navigation chain is total over the empty set rather than each consumer
   guarding the symptom.
2. **`gramps/gui/viewmanager.py:638-651` (`init_interface`)** — unpack the tuple and
   `if current_cat is not None:` before `goto_page(...)` (was the unconditional
   `goto_page(defaults[0], defaults[1])` at the old `:645`). With None there is no
   navigation; the app opens with no active page. This removes the **startup** crash
   at its root.
3. **`gramps/gui/viewmanager.py:80`** — `from .viewmanagerutils import views_to_show`
   (re-export); the old definition (old `:1826-1853`) is deleted.

## C5 — the two retained downstream guards, with reachability evidence
The iter-2/iter-3 directive: prefer removing the downstream guards if unreachable
once `init_interface` no longer navigates on the empty set; otherwise keep only the
ones still reachable, **with evidence**. Both named in the brief's Scope
(`__change_page` :1049-1051, `config_view` :1497-1501) are reachable via entry
points **independent of `init_interface`'s navigation**, so both are kept:

- **`__change_page` (viewmanager.py:1053-1061, the `if not self.pages: return`).**
  Reachable from `_post_load_newdb_gui` (viewmanager.py:1221):
  `self.__change_page(self.notebook.get_current_page())`. On an **empty notebook**
  (no views ⇒ no page ever created) `Gtk.Notebook.get_current_page()` returns
  **-1**, so `self.pages[-1]` (old :1049) raises `IndexError`, and the existing
  `self.pages[0]` fallback (old :1051) raises again on the empty list. This fires
  when a family tree is (auto-)loaded at startup with zero views — *not* via
  `init_interface`'s navigation, so the `init_interface` guard alone does not cover
  it. Guard kept.
- **`config_view` (viewmanager.py:1518-1524, the `if self.active_page is None:
  return`).** Reachable from the **ConfigView** UI action (viewmanager.py:528, bound
  to `<shift><PRIMARY>c`). With no active page, `self.active_page.configure()`
  (old :1501) dereferences `None` → `AttributeError`. User-triggered, independent of
  `init_interface`. Guard kept.

Both are 3-line early-returns that restore totality at the two *other* reachable
entry points; they are not the "guard every consumer" expansion iter-2 rejected
(that was about adding a `goto_page` guard for navigation the `init_interface` fix
already prevents). The `goto_page` guard from iter-1/iter-2 is **not** reintroduced:
`init_interface` no longer calls it on the empty set.

### Out of scope (not guarded)
The next/previous-category actions (`viewmanager.py:597-633`) also index
`self.current_views`/`self.views` and would fault with zero views, but the brief's
Scope enumerates only the startup + `__change_page`/`config_view` cascade and
explicitly excludes "guard every consumer" expansions. Restoring totality at the
*source* (`views_to_show`) is the right long-term shape; broad per-action guards are
deferred as out-of-scope.

## Test (`gramps/gui/test/viewmanager_test.py`)
Two assertions on the **real production** `views_to_show`:
`views_to_show([], use_last=False) == (None, None, [])` and the `use_last=True`
case. No GTK stubbing, no `__new__`, no subprocess, no global `sys.modules`
mutation — so it cannot leak into the shared `unittest discover` run (the iter-1
cause of the 7-unit/1-smoke T3 deltas is structurally gone).

## Red→green (mirrors run-verify.sh exactly)
`run-verify.sh` runs `python3 -m unittest gramps.gui.test.viewmanager_test` twice:
green after `git apply`, red after reverting the prod files (test kept). The docker
runner needs interactive approval unavailable in this session, so I ran the
identical commands by hand against the `gramps-6.1` upstream worktree:

- **GREEN** (patch applied): both tests `ok` (`Ran 2 tests … OK`). The real
  production `views_to_show([])` returns `(None, None, [])`.
- **RED** (prod reverted, test kept): `viewmanager.py` restored and the new
  `viewmanagerutils.py` removed (run-verify `rm`s patch-added prod files), so the
  test's `from ..viewmanagerutils import views_to_show` raises
  `ModuleNotFoundError` → `FAILED (errors=1)`.

**On the nature of the red:** because the seam is a *new* file, run-verify's red
pass removes it, so the red is a `ModuleNotFoundError`, not the bug's `IndexError`.
This is structurally unavoidable for any extract-a-seam fix: no gi-free module on
the target branch contains `views_to_show` pre-fix, so there is nowhere for a
bug-demonstrating red to import from without re-entering the gi-bound code (the
rejected subprocess-stubbing route). The **green** is the load-bearing proof: it
exercises the exact production function and asserts the corrected, totality-restoring
contract. The full real-`init_interface` path is left to the advisory T3-interface
gate and the human's manual V (see below).

## Verification still owed to sign-off (not the builder's to perform)
- **V (manual GUI repro)** on `maintenance/gramps61`: hide every view plugin (or
  list all view plugins under `[plugin] hiddenplugins` in `gramps.ini`), restart →
  confirm **no `IndexError`** and the window opens with **no active page**. Iter-3
  recommended also landing a dogtail interface test (`engine/interface/`,
  `GrampsInterfaceTestCase`, `TREE_REQUIRED=False`, seed `hiddenplugins`) as
  automated V. That artifact lives in the **testbed** repo, not in this gramps
  `patch.diff`, and the T3-interface smoke gate is currently red-baseline on an
  unrelated Glade `_Glade__dirname` defect (INTEGRATION §3, issue_13636); a dogtail
  reproduction would land in that advisory gate, not C4. It is noted here for the
  human's V step rather than bundled into the core contribution.

## T3 deltas from earlier iterations
The iter-1/2/3 whole-suite deltas (7 unit + 1 smoke) traced to the iter-1 test's
global `sys.modules` stubbing leaking across `unittest discover`. This iteration's
test imports one gi-free module and mutates nothing global, so that leak path is
gone. The standing T3 baseline reds (segfault unit discovery; Glade smoke) are
environmental per INTEGRATION §3 and untouched by this patch.

## Commit-readiness
`black --check` passes on all three touched files
(`viewmanager.py`, `viewmanagerutils.py`, `test/viewmanager_test.py`).
