# Brief — issue headless-ut-segfault / headless-unit-discovery-segfault

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.
>
> Supersedes `brief.v1.md`, whose root cause was **falsified** during this Plan
> session (see Defect). Do must **isolate the real cause first**; if the captured
> backtrace warrants re-scoping, iterate back to Plan rather than forcing a fix.

- **Slug:** headless-unit-discovery-segfault
- **Defect:** the whole-suite headless core unit run (`engine/scripts/ubuntu/run-unit.sh` → `GRAMPS_RESOURCES=. python3 -m xmlrunner discover`, no `$DISPLAY`) dies `Trace/breakpoint trap (core dumped)` during test discovery, reddening `T3-unit`. **The underlying defect is not yet isolated** (so states the baseline manifest, `engine/baselines/run-unit.json`). The prior draft's theory — that `class PersistentTreeView(Gtk.TreeView)` subclassing at import (via `gramps/gui/widgets/__init__.py:45`) crashes the interpreter — is **falsified**: (1) subclassing `Gtk.TreeView`/`Gtk.EventBox` with `DISPLAY` unset defines cleanly, exit 0 — a GType registration needs no display; (2) `gramps/gui/widgets/photo.py:45` `class Photo(Gtk.EventBox)` does the same subclass-at-import *earlier* in the import order (`widgets/__init__.py:30`, before `:45`), so it would crash first if that were the trigger. The real faulting frame is unknown and must be captured before any fix.
- **Success criterion:** the headless core unit suite completes discovery and runs without segfaulting (`run-unit.sh` no longer emits `Trace/breakpoint trap (core dumped)`), and the new subprocess regression test that reproduces the crashing import/call chain exits 0 headless.
- **Repo + branch target**: gramps-project/gramps @ maintenance/gramps61
- **Target note:** core fix per INTEGRATION §2, forward-merged to `master`. If isolation pins the cause outside core gramps, iterate to Plan to re-resolve the target.
- **Scope:** (1) **isolate** the discovery-time segfault on an *unmodified* `maintenance/gramps61` checkout in Docker — capture the actual faulting frame; (2) apply the **minimal** headless-safe fix for that captured cause; (3) ship a subprocess regression test. / **out of scope:** the persistenttreeview-subclass theory (falsified); PR #2354's blanket `widgets/__init__.py` `else: __all__ = []` change (breaks ~30 importers); **adding a new `has_gtk_display()` helper** — `gramps.gen.constfunc.has_display()` already exists (proper `Gtk.init_check()` + `Gdk.Display.get_default()` probe) and `gui/utils.py:61` already imports it, so reuse it; any behaviour change when a display **is** present; fixing other unrelated `T3-unit` baseline reds.
- **Repro instruction:** in Docker, `engine/scripts/ubuntu/run-unit.sh` with no `$DISPLAY` → `Trace/breakpoint trap (core dumped)`. **Step 0 (isolate, do this first):** rerun discovery under `python3 -X faulthandler` (and/or `gdb --batch -ex run -ex bt`) to capture the segfaulting frame and the exact module import / C-level call that triggers it. Confirm the crash is hit by the *unmodified* upstream tree, not by uncommitted testbed test artifacts under `gramps/plugins/{test,lib/test,tool/test}/`. **Record the captured backtrace in `build-notes.md`.**
- **Test file:** `gramps/gui/test/headless_import_test.py` (new — core convention: `gramps/gui/test/` package with `__init__.py`, `*_test.py` suffix; create the dir if absent). A segfault cannot be caught in-process, so the test **spawns a subprocess** (`subprocess.run([...], env without DISPLAY)`) that imports/exercises the chain Step 0 pins as the trigger, and asserts the child exits 0 (no `Trace/breakpoint trap`, no `ImportError`). Do finalizes the exact import/call list from the captured backtrace. Must be **red pre-fix** (child segfaults → non-zero) and **green post-fix**. Suite-level proof is `T3-unit` no longer segfaulting.
- **Citations expected:** Do must cite `path:line` on `maintenance/gramps61` for every change, **including the faulting frame** from the Step-0 backtrace that justifies the fix location.
- **Prior-art check (triage cycles):** searched by file path. Upstream **draft PR #2354** targets `gramps/gui/widgets/__init__.py` / `persistenttreeview.py` / `utils.py` for a related headless-import concern, but it (and `brief.v1.md`) attribute the crash to persistenttreeview subclassing — falsified here, and its blanket `__init__.py` change breaks real importers. Do should reference #2354 in the PR description **only if** Step-0 isolation confirms the same frame, and must not adopt its over-broad change. No merged fix on `upstream/maintenance/gramps61` or `master` for this segfault.
- **Disposition hint:** likely-fix → **VERIFY/ISOLATE FIRST.** If the Step-0 backtrace shows the cause is materially different from anything a minimal core patch can safely address (e.g. a third-party/C library crash, or a cause outside core gramps), stop and **iterate to Plan** with the captured evidence rather than forcing a fix. Once green-baseline, drop the core-dump signature from `engine/baselines/run-unit.json` and re-promote `T3-unit` to gating.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts. This is a testbed-tracked defect with no real
Mantis number; the commit carries `Fixes #0000  (STAND-IN — replace with the real
tracker number before marking the PR ready)`. Swapping `#0000` for the real number
and marking ready are the human's pre-ready steps.
