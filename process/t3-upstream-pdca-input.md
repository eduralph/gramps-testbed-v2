# PDCA planning input — T3 upstream fixes

Feed this to the **Plan** beat as the batch input — it has the Plan session pull the
items apart into one bundle each:

```bash
pdca flow --from-csv process/t3-upstream-pdca-input.md      # omit issue_id ⇒ batch Plan
```

**Batch Plan instructions (do this in the Plan session):** read this whole file and
create **exactly two bundles**, one per cycle, using the slug as the id —
`results/issue_glade-setattr/brief.md` and `results/issue_headless-ut-segfault/brief.md`.
**Do NOT brief Workstream C** (it's engine work, not a contribution). Each section below
maps directly to the `brief.md` template fields (`templates/brief.md.tpl`): **Slug ·
Defect · Success criterion · Repo + branch target · Test file**, plus root-cause notes +
the fix spec for the Do builder and the verification the Check gates run. Targets follow
INTEGRATION §2 (core fixes → `maintenance/gramps61`, cherry-picked forward).

> **No Mantis tracking — `#0000` stand-in.** We are not assigning Mantis bug numbers;
> the bundle id is the slug above (`results/issue_<slug>/`, branch `fix/bug-<slug>`).
> The T4 contribution gate (and `pdca publish`) require a `Keyword #NNNN` trailer, so
> use **`Fixes #0000`** in the commit message and **`#0000`** in the PR body as a
> documented **STAND-IN**. Add a remark beside it — e.g. `Fixes #0000  (STAND-IN —
> replace with the real tracker number before marking the PR ready)` — so it satisfies
> T4 yet is unmistakably a placeholder. Reference **testbed issue #1** (Glade) /
> **upstream PR #2354** (segfault) / the `f8c1fc0f50` regression in the PR body for real
> context. Swapping `#0000` for the real number is the human's pre-ready step.

---

## Cycle A — Glade `__setattr__` rejects the class's own attribute writes

- **Slug:** glade-setattr-name-mangling
- **Defect:** `gramps/gui/glade.py` `Glade(Gtk.Builder).__setattr__` (~L62–69) raises
  `AttributeError: Ad-hoc attribute _Glade__dirname is not permitted` whenever a
  `Glade()` is constructed, blocking GUI startup (reds `T3-interface`; testbed #1). Two
  bugs introduced by `f8c1fc0f50` ("Don't use slots on GObject-derived classes — Fixes
  #14153", on `maintenance/gramps61` **and** `master`): (1) the guard whitelist lists the
  **unmangled** `"__toplevel"/"__filename"/"__dirname"`, but `__init__` (L146/158/167/
  171/177) assigns `self.__dirname` etc., which Python name-mangles to `_Glade__*` →
  rejected; (2) `super().__setattr__(self, name, value)` passes `self` twice (a bound
  `super()` method already has it) → `TypeError` once the guard passes.
- **Success criterion:** constructing `Glade()` (and loading a real `.glade` file) raises
  no `AttributeError`/`TypeError`; the `T3-interface` smoke launches the GUI.
- **Repo + branch target:** `gramps @ maintenance/gramps61`
- **Test file:** `gramps/gui/test/glade_test.py` (new; `*_test.py` suffix per repo
  convention) — headless: `Glade()` constructs without raising; red pre-fix, green
  post-fix. GUI-import-light, so the headless C4 runner can execute it.
- **Fix spec (Do builder):** both changes, minimal:
  ```python
  def __setattr__(self, name, value):
      if not hasattr(self, name) and name not in [
          "_Glade__toplevel", "_Glade__filename", "_Glade__dirname",
      ]:
          raise AttributeError(f"Ad-hoc attribute {name} is not permitted.")
      super().__setattr__(name, value)
  ```
- **Verify (Check):** C4-verify proves the new test red with the production change
  reverted, green with the fix. On green-baseline, drop the `_Glade__dirname` signature
  from `engine/baselines/run-interface.json` and re-promote `T3-interface`.
- **Disposition hint:** Fixed (regression in `f8c1fc0f50`).

---

## Cycle B — Headless unit run segfaults importing a GTK-at-import-time widget

- **Slug:** headless-ut-gtk-import-segfault
- **Defect:** the whole-suite headless run (`run-unit.sh`, `xmlrunner discover` with no
  display) dies `Trace/breakpoint trap (core dumped)` (reds `T3-unit`). Root cause:
  `gramps/gui/widgets/persistenttreeview.py` evaluates `class
  PersistentTreeView(Gtk.TreeView)` at **import time**; importing it headless constructs
  a GTK widget and crashes the interpreter. Upstream **draft PR #2354** diagnosed this
  but its `gramps/gui/widgets/__init__.py` "import nothing headless" change breaks ~30
  real importers of `Photo`/`MonitoredEntry`/… (`ImportError`) — the "several tests
  failing" it flagged.
- **Success criterion:** the headless core unit suite imports and runs without
  segfaulting; `from gramps.gui.widgets import <Widget>` still works headless (no new
  `ImportError`).
- **Repo + branch target:** `gramps @ maintenance/gramps61`
- **Test file:** `gramps/gui/widgets/test/persistenttreeview_test.py` (new; `*_test.py`)
  — headless: importing `gramps.gui.widgets.persistenttreeview` and `gramps.gui.widgets`
  succeeds (no segfault / no `ImportError`). The suite-level proof is `T3-unit` going
  green.
- **Fix spec (Do builder) — "Option C", reusing PR #2354's defensible parts (credit it):**
  - **Step 0, reproduce in Docker first:** run `engine/scripts/ubuntu/run-unit.sh`,
    capture the exact crashing import chain, and confirm whether the trigger is upstream
    tests or testbed-added tests (`gramps/plugins/{test,lib/test,tool/test}/` hold
    uncommitted cycle artifacts, e.g. `libpersonview_tagrename_test.py`). Scope the fix
    to what the *unmodified* tree hits.
  - `gramps/gui/utils.py`: add `has_gtk_display()` (from #2354).
  - `gramps/gui/widgets/persistenttreeview.py`: choose the base dynamically
    (`Gtk.TreeView` when a display is present, else `object`) and early-return in
    `__init__` headless — module imports without constructing a GTK widget.
  - `gramps/gui/widgets/__init__.py`: **keep every widget import unconditional**; guard
    **only** the `persistenttreeview` import. Do NOT adopt #2354's blanket
    `else: __all__ = []`.
  - Lazy/guard the other import-time GTK from #2354 only where the repro shows it on the
    core path: `BUSY_CURSOR` in `gramps/gui/dbman.py`; `Gtk.IconTheme.get_default()` in
    `gramps/gui/clipboard.py` / `gramps/gui/pluginmanager.py`.
  - `@unittest.skipUnless(_HAS_GTK_DISPLAY, …)` on the core tests the repro shows import
    GUI (matching the existing testbed `_HAS_GTK_DISPLAY` idiom).
- **Verify (Check):** C4-verify red→green on the new import test; `T3-unit` no longer
  segfaults. On green-baseline, drop the core-dump signature from
  `engine/baselines/run-unit.json` and re-promote `T3-unit`. Reference/supersede draft
  PR #2354 in the PR description (keep its diagnosis credit).
- **Disposition hint:** Fixed (completes PR #2354 along its safer direction).

---

## Workstream C — Addon `target_version` is NOT a PDCA cycle (testbed engine)

Do **not** brief this as a gramps contribution. Finding: core 6.1 requires an exact
minor match (`gramps/gen/plug/_pluginreg.valid_plugin_version`). QuiltView/CombinedView
declare `"6.0"` on addons-source `maintenance/gramps60` and **already `"6.1"` on
`maintenance/gramps61`** — fixes are cherry-picked gramps60→gramps61. The `T3-addon-unit`
red is the testbed running gramps60-target addons against **gramps61 core** (a harness
matrix gap), not an addon defect. Bumping the gramps60 branch would break those addons on
a real 6.0 install.

**Action (engine, instance-only):** make `T3-addon-unit` (and the addon path of
`C4-verify`) a **matrix** — each addons-source branch tested against its matching core
(gramps60 addons × 6.0 core, gramps61 addons × 6.1 core), so both stay green through the
cherry-pick. Parametrize the core version / addon branch in
`engine/scripts/ubuntu/run-addon-unit.sh` (+ the addon C4 runner) and `pdca.toml`, and
split `engine/baselines/run-addon-unit.json` accordingly. **File a new testbed GitHub
issue** for the matrix gap and **correct the act-log 2026-06-06 routing** (its "bump
`target_version` on both addons" follow-up was wrong).

---

## Suggested order
1. **Cycle A** (smallest, highest-confidence; unblocks `T3-interface`).
2. **Cycle B** (repro → Option C; the largest).
3. **Workstream C** (engine + new issue; independent).

## STOP discipline
Each cycle stops at a **draft** PR to `gramps-project/gramps` (commit/PR carry the
`#0000` stand-in). Marking the PR ready, and replacing `#0000` with the real tracker
number, are the human's.
