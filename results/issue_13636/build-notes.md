# Build notes — issue 13636 / uimanager-update-menu-none-toolbar-parent

> Builder rationale. Withheld from the reviewer by the driver; for the human at
> sign-off. All `path:line` citations are on the target branch
> `gramps-project/gramps @ maintenance/gramps61` (the checkout at
> `../gramps`, `.git/HEAD` → `refs/heads/maintenance/gramps61`).

## Root cause (two sentences)

`UIManager.update_menu()` reads `toolbar_parent = toolbar.get_parent()`
(`gramps/gui/uimanager.py:258`) and then unconditionally calls
`toolbar_parent.remove(toolbar)` (`gramps/gui/uimanager.py:260`). During the
shutdown race the previous toolbar has already been detached from its container,
so `get_parent()` returns `None` and `None.remove(...)` raises
`AttributeError: 'NoneType' object has no attribute 'remove'`.

## Why it fires on window-close before the addons-update window

`viewmanager.__change_page` queues the nested `page_changer` on the GLib idle
loop: `GLib.idle_add(page_changer, self, ...)` (`gramps/gui/viewmanager.py:1066`),
and `page_changer` calls `self.uimanager.update_menu()`
(`gramps/gui/viewmanager.py:1062`, defined `1061`). If the main window is closed
(top-right `X`) before that queued callback runs, the toolbar container is torn
down first; the still-queued `update_menu()` then iterates a toolbar whose parent
is already gone. The in-tree comment at `gramps/gui/viewmanager.py:1057-1060`
(bug 12048) already documents that Gtk can delete the toolbar object "too soon"
during view changes — the same widget-lifetime hazard, here triggered by
teardown. This corroborates the Mantis 13636 trace (5.1.6 line numbers
`viewmanager.py:905` / `uimanager.py:245`; the equivalent sites on
`maintenance/gramps61` are `viewmanager.py:1062` and `uimanager.py:258-260`).

## The fix (in scope, one call site)

`patch.diff` inserts a `None`-guard immediately after
`toolbar_parent = toolbar.get_parent()` (between `gramps/gui/uimanager.py:258`
and `:259`): when `toolbar_parent is None`, log via the module logger
(`LOG`, defined `gramps/gui/uimanager.py:34`) and `return` early, skipping the
toolbar remove/repack block (`:259-273`).

Early `return` (rather than only guarding line 260) is required because the
*same* `toolbar_parent` is dereferenced again at
`gramps/gui/uimanager.py:269` (`toolbar_parent.pack_start(...)`); guarding only
the `.remove()` would merely move the identical `AttributeError` four lines down.
The menubar has already been rebuilt (`:253-255`) before this point, which is
harmless on a window that is being destroyed, so skipping just the toolbar work
is the correct minimal behaviour.

Scope adherence (per brief): no change to `viewmanager.page_changer`, no shutdown
reordering, no audit of other `get_parent()` callers, nothing touching the
unrelated "Top Surnames" `_gramplet.py` warning.

## The test — `gramps/gui/tests/uimanager_test.py`

Unit-layer substitute for the GUI race (the interface runner
`engine/scripts/ubuntu/run-interface.sh` is not yet ported — INTEGRATION §3). It
constructs a real `UIManager` (its `__init__`, `gramps/gui/uimanager.py:99-138`,
touches no Gtk), installs a mocked "previous" builder whose
`get_object("ToolBar")` returns a toolbar mock, and patches the module-level
`Gtk` and `config` so `update_menu()` rebuilds its inner `Gtk.Builder()`
(`gramps/gui/uimanager.py:242`) against mocks — no display, no real widgets.

- `test_detached_toolbar_does_not_raise`: `toolbar.get_parent()` returns `None`;
  asserts `update_menu(init=False)` raises no `AttributeError`. This is the
  regression: **red** on the unpatched branch (the `:260` `.remove()` on `None`),
  **green** with the guard.
- `test_attached_toolbar_is_still_updated` (positive control): a toolbar *with* a
  parent is still `remove()`d and `pack_start()`ed, proving the guard does not
  short-circuit the normal path. Green both before and after the fix.

Module-level C4 contract (`engine/scripts/ubuntu/run-verify.sh:84-94`,
`python3 -m unittest gramps.gui.tests.uimanager_test`): the detached test fails
without the production change → module **red**; both pass with it → module
**green**.

## Verified against (no execution — see limitation below)

- `gramps/gui/uimanager.py:258,260,269` — the `get_parent()` / `.remove()` /
  `pack_start()` call site that the guard protects.
- `gramps/gui/viewmanager.py:1061,1062,1066` — `page_changer` → `update_menu`
  via `GLib.idle_add`, the teardown trigger.
- `gramps/gui/uimanager.py:34` — `LOG` exists for the skip message.
- `gramps/gui/uimanager.py:99-138` — `__init__` is Gtk-free, so the test can
  build a real `UIManager` and only mock the builder/app/Gtk/config.

## Caused by (lead, not a verified SHA)

`git blame` could not be run in this session (see limitation). The unguarded
`toolbar_parent.remove(toolbar)` has been present since the custom-UIManager
rewrite — file authored 2018 by Paul Culley (`gramps/gui/uimanager.py:4`). I am
**not** asserting a SHA; per INTEGRATION §8 a "Caused by" line must carry its SHA,
and I will not fabricate one. If the human/Check wants the blame SHA, run
`git -C ../gramps blame -L 258,260 maintenance/gramps61 -- gramps/gui/uimanager.py`
once the environment is fixed.

## Decisions / things ruled out

- **No `gramps/gui/tests/__init__.py` shipped.** `run-verify.sh:41-51` classifies
  every non-`*_test.py` file in `patch.diff` as "production" and reverts it with
  `git checkout -- $PROD` for the red phase (`run-verify.sh:89`). A brand-new,
  untracked `__init__.py` would make that `git checkout` fail under `set -e` and
  break the gate. It is also unnecessary: `python3 -m unittest
  gramps.gui.tests.uimanager_test` (`run-verify.sh:86`) imports `gramps.gui.tests`
  as a Python-3 namespace sub-package of the regular `gramps.gui` package
  (`gramps/gui/__init__.py`) without one. **Flag for the human:** an eventual
  upstream PR may still want a `tests/__init__.py` for `unittest discover`
  coverage; it is deliberately excluded here only because the C4 revert mechanism
  cannot tolerate it in the patch.
- **Test path `gramps/gui/tests/` (plural).** I used the path the brief's
  *Test file* field names verbatim. Note Gramps elsewhere uses the singular
  `test/` (e.g. `gramps/gen/merge/test/`); the prior bundle draft of this test
  had chosen `gramps/gui/test/`. The brief is authoritative for the path, so I
  followed it (plural). If Check prefers matching the repo convention, this is a
  one-word path change.
- **Guard returns early** rather than wrapping in try/except — the condition is a
  precise, expected state (detached toolbar), not an exceptional one; an explicit
  `is None` check is clearer and narrower than swallowing `AttributeError`.

## Limitation — environment blocked all Bash this session

The `builder` PreToolUse hook (`.claude/agents/builder.md:10-18`) runs
`python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/builder_guard.py"`, but in this
session `$CLAUDE_PROJECT_DIR` resolved to the **bundle** dir
(`results/issue_13636/`), where the hook file does not exist — exactly the
relative-path failure mode the agent file's own comment warns about. Every `Bash`
call therefore exited non-zero and was blocked, so I could **not** run the test,
`git blame`, `git apply --check`, or the C4 gate locally. All artifacts were
produced with `Read`/`Write`/`Edit`, and red→green was established by tracing the
`update_menu` code path (above), not by execution. The deterministic
`run-verify.sh` C4 gate is the mechanical red→green verification and should be run
by the driver/human. (Restoring the guard at the bundle-relative path was
declined as a sensitive-file edit, so I left the environment untouched.)
