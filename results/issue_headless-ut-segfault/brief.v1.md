# Brief — issue headless-ut-segfault / headless-ut-gtk-import-segfault

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** headless-ut-gtk-import-segfault
- **Defect:** the whole-suite headless unit run (`engine/scripts/ubuntu/run-unit.sh`, `xmlrunner discover` with no display) dies `Trace/breakpoint trap (core dumped)` (reds `T3-unit`). Root cause: `gramps/gui/widgets/persistenttreeview.py` evaluates `class PersistentTreeView(Gtk.TreeView)` at **import time** (it does `from gi.repository import Gtk` then defines the class against `Gtk.TreeView`), and `gramps/gui/widgets/__init__.py` imports it **unconditionally** (`from .persistenttreeview import *`). Importing the package headless constructs a GTK widget and crashes the interpreter. Confirmed via `git -C ../gramps show maintenance/gramps61:gramps/gui/widgets/persistenttreeview.py` and `…:gramps/gui/widgets/__init__.py`. Upstream **draft PR #2354** diagnosed this, but its `widgets/__init__.py` "import nothing headless" change breaks ~30 real importers of `Photo`/`MonitoredEntry`/… (`ImportError`) — the "several tests failing" it flagged.
- **Success criterion:** the headless core unit suite imports and runs without segfaulting; `from gramps.gui.widgets import <Widget>` still works headless (no new `ImportError`).
- **Repo + branch target:** `gramps @ maintenance/gramps61` (core fix per INTEGRATION §2; cherry-picked forward to `master`).
- **Scope:** make the import path headless-safe — add a display probe, build `PersistentTreeView` against a non-GTK base headless and short-circuit its `__init__`, guard **only** the `persistenttreeview` import in `widgets/__init__.py`, and lazy/guard the import-time GTK that the *unmodified*-tree repro actually hits on the core path / out of scope: adopting PR #2354's blanket `else: __all__ = []`, making any other widget import conditional, or any behaviour change when a display **is** present (the GUI path must be byte-for-byte unchanged).
- **Repro instruction:** in Docker, `engine/scripts/ubuntu/run-unit.sh` with no `$DISPLAY` → `Trace/breakpoint trap (core dumped)`. **Step 0 — reproduce first:** capture the exact crashing import chain and confirm whether the trigger is upstream tests or testbed-added tests (`gramps/plugins/{test,lib/test,tool/test}/` hold uncommitted cycle artifacts, e.g. `libpersonview_tagrename_test.py`). Scope the fix to what the *unmodified* tree hits.
- **Test file:** `gramps/gui/widgets/test/persistenttreeview_test.py` (new; `*_test.py`. The `gramps/gui/widgets/test/` directory does **not** exist yet — Do creates it with an `__init__.py`). Headless: importing `gramps.gui.widgets.persistenttreeview` and `gramps.gui.widgets` succeeds (no segfault / no `ImportError`). The suite-level proof is `T3-unit` going green.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change (`gramps/gui/utils.py`, `gramps/gui/widgets/persistenttreeview.py`, `gramps/gui/widgets/__init__.py`, plus any of `dbman.py`/`clipboard.py`/`pluginmanager.py` the repro shows, and the new test).
- **Fix spec (Do builder) — "Option C", reusing PR #2354's defensible parts (credit it):**
  - **Step 0, reproduce in Docker first** (see Repro instruction) — confirm the crashing import chain on the unmodified tree before editing.
  - `gramps/gui/utils.py`: add `has_gtk_display()` (from #2354 — confirmed absent on `maintenance/gramps61`).
  - `gramps/gui/widgets/persistenttreeview.py`: choose the base dynamically (`Gtk.TreeView` when a display is present, else `object`) and early-return in `__init__` headless — the module imports without constructing a GTK widget.
  - `gramps/gui/widgets/__init__.py`: **keep every widget import unconditional**; guard **only** the `persistenttreeview` import. Do NOT adopt #2354's blanket `else: __all__ = []`.
  - Lazy/guard the other import-time GTK from #2354 **only** where the repro shows it on the core path: `BUSY_CURSOR` in `gramps/gui/dbman.py`; `Gtk.IconTheme.get_default()` in `gramps/gui/clipboard.py` / `gramps/gui/pluginmanager.py`.
  - `@unittest.skipUnless(_HAS_GTK_DISPLAY, …)` on the core tests the repro shows import GUI (matching the existing testbed `_HAS_GTK_DISPLAY` idiom).
- **Prior-art check (triage cycles):** searched by file path. Upstream **draft PR #2354** targets these same files with a correct diagnosis but an over-broad `widgets/__init__.py` change (breaks ~30 importers). This brief reuses its defensible parts (`has_gtk_display`, the `persistenttreeview` guard) and supersedes its blanket change. Do should reference/supersede PR #2354 in the PR description and keep its diagnosis credit.
- **Verify (Check):** C4-verify proves the new import test **red→green**; `T3-unit` no longer segfaults. On a green baseline, drop the core-dump signature from `engine/baselines/run-unit.json` and re-promote `T3-unit`.
- **Disposition hint:** likely-fix (completes PR #2354 along its safer direction).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts. The commit carries `Fixes #0000  (STAND-IN —
replace with the real tracker number before marking the PR ready)`; the PR body
references/supersedes upstream draft PR #2354 (keeping its diagnosis credit).
Swapping `#0000` for the real number and marking ready are the human's pre-ready
steps.
