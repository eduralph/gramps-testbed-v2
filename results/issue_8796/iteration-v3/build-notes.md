# Build notes — issue 8796 / viewmanager-empty-views-indexerror (iteration 3)

## Root cause (target branch: upstream/maintenance/gramps61)

`views_to_show([])` returns `(0, 0, [])` — `default_cat_views = [0] * len(views)`
collapses to `[]` while `current_cat`/`current_cat_view` stay `0`
(`gramps/gui/viewmanager.py:1830-1832,1853`). It claims "select category 0" when
there is no category 0. `init_interface` feeds that to navigation:
`self.current_views = defaults[2]` (== `[]`) then `goto_page(defaults[0],
defaults[1])` (`:641,645`). `goto_page` does `self.current_views[cat_num] =
view_num` on the empty list (`:927`) → `IndexError: list assignment index out of
range` at startup. The same empty-view state cascades into `__change_page` via
`post_load` (`:1221` calls `self.__change_page(self.notebook.get_current_page())`;
an empty notebook gives `page_num == -1`, so `self.pages[-1]` and the
`self.pages[0]` fallback both raise on the empty list — `:1048-1051`) and into
`config_view` (`:1501`, dereferences a `None` active page).

## What changed (and why this shape)

**The reported crash is fixed at the source, by construction** — not by guarding
the `goto_page` symptom (the iter-2 reject):

1. `views_to_show` (`:1832`, new lines after it): when `views` is empty, return
   `(None, None, [])` instead of `(0, 0, [])`. The function is now honest — "no
   views → no category to select". It is called from exactly one place
   (`init_interface`, `:640`; confirmed by `grep views_to_show` across `gramps/`),
   so changing the empty-case contract is safe.
2. `init_interface` (`:639-645`): unpack the named tuple and only navigate when a
   category exists — `if current_cat is not None: self.goto_page(...)`. With zero
   views the navigation chain is **never entered**, so `goto_page` (and every
   caller routed through it — `__next_view`/`__prev_view`/`__view_category`) is
   total over the empty set by construction. This is exactly the remedy the iter-2
   sign-off asked for ("have init_interface not navigate with zero available views
   / stop views_to_show([]) collapsing").

**The two genuinely-separate entry points** that also touch the empty-view state
are made total too, because there is no upstream source to remove for them — they
are reached independently of startup navigation, so the brief's invariant ("an
empty view set must resolve to a no-active-page state") has to hold at each:

3. `__change_page` (`:1050`, after `__disconnect_previous_page`): `if not
   self.pages: return`. Reached via `post_load` (`:1221`) when a tree is opened
   with no views — `page_num == -1` and the existing `self.pages[0]` fallback
   would itself raise. This is *not* the rejected goto_page guard; it is a
   distinct caller (the notebook signal path never fires because no page is ever
   created, but `post_load` calls `__change_page` directly).
4. `config_view` (`:1501`): `if self.active_page is None: return`. Reached by the
   "Configure the active view" menu action (`:528`) when there is no active page.

Why 3 and 4 are not "the rejected three-guard approach unchanged": iter-2 guarded
`goto_page` itself with `if not self.views: return`. That guard is **gone** —
replaced by the source fix (1+2). 3 and 4 cover entry points (`post_load`, a menu
action) that the source fix provably cannot reach, so leaving them unguarded would
just relocate the same crash. The brief's *Scope* explicitly puts both in scope
("instead of the follow-on `__change_page` / `config_view` failures rooted in the
same empty-view state"), and iter-1's C5 demanded `__change_page` be handled or
shown unreachable — it is reachable via `post_load`, so it is handled.

### Alternatives weighed
- **A single `goto_page` guard (iter-1/iter-2 shape).** Rejected by the human:
  symptom-guarding the central primitive leaves `views_to_show` still lying
  `(0,0,[])` and `init_interface` still navigating into the empty set; an
  `init_interface` rewrite later could re-expose it. The source fix removes the
  lie at its origin.
- **Force "at least one view always loaded" / a placeholder page.** Explicitly
  out of scope (brief *Scope*), and it changes plugin-hiding semantics.
- **Extract the crash logic into a brand-new import-light module and test that.**
  Rejected: a new module is removed by `run-verify`'s red pass, so the red would
  be an `ImportError` ("seam absent"), not the genuine `IndexError` — it would not
  prove the test catches the *bug*. Driving the real, unchanged-name production
  methods (below) keeps the red a true `IndexError` at `viewmanager.py:927`.

## Test — `gramps/gui/test/viewmanager_test.py`

Drives the **real** production code (`ViewManager.init_interface`,
`__change_page`, `config_view`, module-level `views_to_show`), red pre-fix / green
post-fix. C4-verify confirms it: green-with-fix=PASS, and the red pass (production
reverted) fails with the genuine `IndexError: list assignment index out of range`
at `gramps/gui/viewmanager.py:927` — the exact reported bug.

**Subprocess isolation — this is the fix for the iter-1/iter-2 T3 leak.** The two
earlier attempts stubbed ~20 `gi`/`gramps.gui` modules in the live interpreter to
import `viewmanager` headless; even with `patch.dict` the import left real
`gramps.*` modules half-initialised under a mock `gi`, leaking 7 unit failures
(e.g. `imports_test::test_imp_3_4`) into the shared `unittest discover` run. Here
each scenario runs in a **fresh child interpreter** (`subprocess.run([sys.executable,
"-c", _CHILD, scenario])`): the stubs and the `viewmanager` import live and die
with the child, so nothing touches this process or the suite. The test module
itself imports only `os, subprocess, sys, unittest` — fully import-light, so it is
safe in the headless C4 runner and in the whole-suite T3 run (no `gi`/`gramps.gui`
at load → no core dump, no leak). The iter-2 reviewer's §6.1 named exactly this
remedy ("sandbox the import in a subprocess … rather than relying on patch.dict").

**Real entry point, not a hand-copy (principles §3.4; the issue-8653 trap).** The
child imports the real `gramps.gui.viewmanager` and calls the real
`init_interface` (the reported startup path) on a `ViewManager.__new__` built into
the exact post-`__init__`/pre-`init_interface` state (`viewmanager.py:208-219`).
GUI collaborators are mocks; the menu-building tail (`__build_tools_menu` /
`__build_report_menu`, which pull in `ActionGroup` + the plugin registry and are
orthogonal to the view-navigation bug) is stubbed to no-ops so the real
`init_interface` can run to completion headless. The bug and the fix sit in the
view-navigation logic, which is the real shipped code — no parallel
re-implementation to drift. This also answers iter-2's T5 note ("move the test
toward the real `init_interface` entry point").

## Verification
- `run-verify.sh` (C4): EXIT=0 — green-with-fix=PASS / red-without-fix=PASS
  against clean `upstream/maintenance/gramps61` (`gramps-6.1` worktree).
- `black --check gramps/gui/viewmanager.py` and the test file: clean
  (commit-ready for the gramps pre-commit hook).
- T3 leak risk: eliminated by design (import-light test + subprocess isolation);
  no in-process `gi`/`gramps.gui` stubbing remains.

## Still needs the human (carry-forward V, unchanged by Do)
- **Manual GUI repro on `maintenance/gramps61`**: hide every view plugin (or list
  all view plugins under `[plugin] hiddenplugins` in `gramps.ini`), restart Gramps,
  confirm it opens with no active page and no `IndexError`. This end-to-end
  confirmation is the human's at sign-off; the unit test stands in for the
  automatable part.
