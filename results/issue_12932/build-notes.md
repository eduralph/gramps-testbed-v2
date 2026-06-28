# Build notes — issue 12932 / verify-fanchart2way-startup-crash-fixed

**Disposition: VERIFY-FIRST (POSSIBLY-FIXED → already fixed).** No production
patch. Deliverables are (1) a committed AT-SPI repro in the testbed mount,
(2) a `close-disposition` of `manual-verification` routing the final call to the
human at sign-off, and (3) these notes. There is **no** `patch.diff` /
`commit-msg` / `pr-description` — an empty `patch.diff` would otherwise trip
`pdca publish` (it `git apply`s a no-op then `git commit` → "nothing to commit";
publish.py:121-124 now treats a missing/empty patch as a close, but the cleanest
record ships no patch at all). The `close-disposition` marker stands in for
`patch.diff` in the state machine (state.py:52-54).

## Success criterion (brief) and how it is met

> On `maintenance/gramps61`, the 12932 repro no longer raises — the 2-way fan
> chart restores at startup (time-period gradient enabled) without the
> AttributeError.

Met by **confirming the already-merged fix is present on the target branch** and
shipping a repro that exercises the exact reported path and passes green on it.

## What the bug was

Mantis 12932 (Gramps 5.x/6.x): with "Remember last view displayed" enabled, the
last view set to the **2-Way Fan** chart, and that view's background =
**Time period based gradient**, Gramps fails to start. From the reporter's trace
(notes.json ~0066737):

```
fanchart2way.py main → self.fan.reset()
fanchart2way.py reset → self.prepare_background_box(...)
fanchart.py prepare_background_box → self.set_userdata_timeperiod(person, userdata)
fanchart.py set_userdata_timeperiod → userdata.append(period)
AttributeError: 'NoneType' object has no attribute 'append'
```

codefarmer's triage (notes.json ~0067827) nailed it: "Essentially this is a
variant of 0013395 with a different configuration setting" — the
**Time period based gradient** selects `BACKGROUND_GRAD_PERIOD`, which routes to
`set_userdata_timeperiod`, the same `userdata.append(...)`-on-`None` family of
paths as 13395's age gradient.

## Root cause and the invariant (the brief's "Invariant to restore")

`set_generations` initialised each `self.data[i]` slot with the **userdata
element left as `None`**. At startup there is no active/root person yet, so
`_fill_data_structures` short-circuits and never replaces those placeholder
slots:

- `gramps/gui/widgets/fanchart2way.py:248` — `if not self.rootpersonh: return`.

`prepare_background_box`'s gradient paths then iterate the slots and call
`set_userdata_timeperiod(person, userdata)` → `userdata.append(period)` on the
`None`:

- `gramps/gui/widgets/fanchart.py:405-417` — `BACKGROUND_GRAD_PERIOD` branch
  iterating `(person, userdata)` and calling `set_userdata_timeperiod`.
- `gramps/gui/widgets/fanchart.py:340-352` — `set_userdata_timeperiod`, ending
  `userdata.append(period)` (line 352).

The invariant to restore: **every fan-chart `self.data` slot carries its own
userdata list**, so the append paths never hit `None` regardless of the
`_fill_data_structures` short-circuit.

## Evidence the fix is already on `maintenance/gramps61`

Merged commit (cited by the brief):

- `0f3830a6e8` "Fix fan chart crash at startup with age-gradient background",
  "Fixes #13395" — verified an **ancestor of HEAD** on the
  `upstream/maintenance/gramps61` worktree (`git merge-base --is-ancestor
  0f3830a6e8 HEAD` → yes). It touches `fanchart.py`, `fanchart2way.py`,
  adds `gramps/gui/widgets/test/fanchart_test.py`, and registers it in
  `po/POTFILES.skip`.

Current slot initialisation on the target branch (the evidence the path is
fixed) — each slot gets its **own empty userdata list `[]`**:

- `gramps/gui/widgets/fanchart.py:1515-1521` — `set_generations`:
  `self.data[i] = [(None, None, None, []) for _ in range(2**i)]`, with the
  comment at 1517-1520 calling out "so that prepare_background_box can safely
  call userdata.append() even when _fill_data_structures short-circuits (e.g.
  on startup before rootpersonh is set). See bug 0013395."
- `gramps/gui/widgets/fanchart2way.py:226-232` — `set_generations`: the same
  `[(None, None, None, []) for _ in range(2**i)]` slot init with the matching
  comment.

So the `BACKGROUND_GRAD_PERIOD` (=7, `gramps/gen/const.py:380`) startup path the
12932 reporter hit now appends to an empty list, never `None`. The 2-way +
time-period case is covered by the same one-object-per-slot init the 13395 fix
introduced; nothing 2-way- or period-specific was left out.

## The repro (engine/interface/test_bug_12932_fanchart2way-startup.py)

A GUI E2E (`Surfaces: gui` → `C4-verify-interface`) that restores the reported
startup scenario faithfully on the canonical `TestTree` (example.gramps):

- **Last-view restore** via the launcher's `-c` flags
  (`preferences.use-last-view:True`, `preferences.last-view:fanchart2wayview`) —
  both keys are in the global gramps config (`gramps/gen/config.py:332-333`), so
  `-c` reaches them. `views_to_show` (`gramps/gui/viewmanager.py:1996-2023`)
  then opens Gramps on the 2-Way Fan view, the same effect as "Remember last
  view displayed" + last-view = 2-Way Fan.
- **Time-period gradient background** by seeding the view's per-view config
  file. The catch: `interface.fanview-background` is *not* a global config key —
  it is registered in the 2-Way Fan view's own ConfigManager
  (`FanChart2WayView.CONFIGSETTINGS`, `plugins/view/fanchart2wayview.py:60-63`),
  created lazily at `PageView.init_config` as
  `<config_dir>/Ancestry_fanchart2wayview.ini`
  (`gramps/gui/views/pageview.py:566`, ident `category + "_" + pdata.id`).
  Because that key has no registered default at CLI-parse time, `-c
  interface.fanview-background:7` would print "no such config setting" and quit
  Gramps (`gramps/cli/argparser.py:369,398-403`). So the test instead writes
  `[interface] fanview-background = 7` into that per-view `.ini` **before
  launch**; `init()` loads an existing file (`configmanager.py:204-206`,
  `_load_section` → `safe_eval`), so the view starts with
  `BACKGROUND_GRAD_PERIOD`. The config dir is asked of Gramps itself
  (`VERSION_DIR`) in a subprocess, mirroring how the interface runner resolves
  `USER_PLUGINS`, rather than guessing the XDG path.
- **Assertion** (red↔green axis): the bug's uncaught-exception handler logs the
  traceback to stderr (the reporter's "Unhandled exception" log) and surfaces an
  "Error Report" window. The test reads Gramps' captured stderr (base.py's
  `_stderr_file`) and asserts the `'NoneType' object has no attribute 'append'`
  + `fanchart` signature is absent and no Error Report window is up. A positive
  guard — a showing "drawing area" (`FanChartBaseWidget(Gtk.DrawingArea)`,
  `fanchart.py:114`) — keeps a green result honest: if the fan view failed to
  restore, Gramps would sit on the People tree-table view with no drawing area
  and the test fails rather than passing vacuously.

### Why this is recorded as a verify-first close (not a red→green within the bundle)

The fix is *already* in `upstream/maintenance/gramps61`, so there is no patch in
this bundle to revert. `run-verify-interface.sh`'s red leg (run the repro on the
"unpatched" worktree and expect it to FAIL) would instead see it PASS — the
worktree already carries the fix — which the runner classes as
`PDCA-UNVERIFIABLE` and routes to §6 NEEDS-HUMAN under the C6 accept-guard
(INTEGRATION.md §3). The committed repro passing green on the current target
branch IS the verification evidence; the human confirms the GUI at sign-off
(brief: "If the GUI repro cannot be driven, record the verification as performed
by hand at sign-off"). The `close-disposition = manual-verification` makes the
driver seed `MANUAL-VERIFICATION.md` for exactly that human step
(driver.py:118,130).

## Alternatives considered / ruled out

- **Ship a new fix to `fanchart.py` / `fanchart2way.py`.** Ruled out and
  explicitly out of scope (brief): the invariant is already restored upstream by
  `0f3830a6e8`. Re-implementing it would duplicate a merged fix — the most
  expensive form of prior-art rediscovery (quality-cycle §guidelines). Zero
  production lines change here.
- **Drive the background via `-c interface.fanview-background:7`.** Ruled out on
  a verified mechanism, not a guess: that key isn't a global-config default, so
  the launcher rejects it and quits Gramps
  (`gramps/cli/argparser.py:369,398-403`). Seeding the per-view `.ini` is the
  only path that reaches a view-scoped ConfigManager setting before the view
  loads.
- **Assert on the GUI Error Report window only.** Ruled out as fragile: base.py
  auto-dismisses dialogs/alerts during startup, and the crash is logged to
  stderr regardless, so stderr is the durable signal (window presence is kept as
  a secondary check).

## Files

- Added: `engine/interface/test_bug_12932_fanchart2way-startup.py` (testbed
  mount; committed repro, not in any `patch.diff`). No gramps-core `.py` added
  or removed, so no `po/POTFILES.*` change applies (that rule is for core
  translatable/translatable-free modules, not the testbed's interface suite).
- `results/issue_12932/close-disposition` = `manual-verification`.
- No `patch.diff`.
