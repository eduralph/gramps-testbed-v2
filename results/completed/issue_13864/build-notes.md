# Build notes — issue 13864 (dashboard-column-count-crash-locks-tree)

> Withheld from the reviewer. Rationale for the human at sign-off.

## Root cause (verified on `maintenance/gramps61`)

The Dashboard "Number of Columns" control is an **unbounded** positive-integer
text entry (`add_pos_int_entry`, `gramps/gui/configure.py:490-514`); its
`changed` callback routes the typed value through the registered setter
`GrampletPane.set_columns` (`gramps/gui/widgets/grampletpane.py:1628-1633`,
`1386-1405`), which floors the value at 1 but has **no ceiling**, then builds one
`Gtk.Box` per column in `for i in range(self.column_count)`
(`grampletpane.py:1397-1402`). A value like the reporter's 1000 makes GTK
allocate/realize an enormous layout, the main loop never returns, the process is
killed, and — because it dies without releasing the BSD database lock under
`~/.gramps/grampsdb/<tree>/` — the tree is locked on the next start.

## Fix

Bound every column-count entry point to `[1, MAX_GRAMPLET_COLUMNS]` (=100) with a
single `clamp_column_count()` helper, before the value drives widget allocation,
and surface the accepted range as the entry tooltip:

- `MAX_GRAMPLET_COLUMNS` + `clamp_column_count()` defined at
  `grampletpane.py` Constants section (new lines after `:70`).
- `__init__` kwargs default — `grampletpane.py:1020`.
- `load_gramplets` `.ini` read — `grampletpane.py:1199-1200`.
- `set_columns` live setter — `grampletpane.py:1386-1388` (the `if num < 1`
  floor is subsumed by the clamp).
- `config_panel` entry now passes `helptext=_("Enter a number from 1 to %d.")`
  — `grampletpane.py:1640` — so the cap is communicated, not fully silent.

### Why all three entry points (invariant, not the single 1000 repro)

The brief's invariant is stated over *any* accepted column value → no crash/lock,
i.e. the defect category. `column_count` is assigned from external/unbounded
input in three places (kwargs, `.ini`, the live dialog); clamping only
`set_columns` would still let a hand-edited `.ini` (`column_count=100000`)
reproduce the freeze at startup. The single shared helper closes all three with
the smallest change that restores the invariant.

## Why this is `PDCA-UNVERIFIABLE` (addresses the Iteration 1 carry-forward)

Iteration 1 shipped a helper-only headless unit test
(`grampletconfig_test.py`) that imported and exercised the extracted
`clamp_column_count` **directly**. Sign-off rejected it because reverting the
production clamp calls left that test green — C4 red→green was decoupled from the
actual fix (the second occurrence of that pattern). It directed Do to (1) remove
the helper-only test, (2) flag the GUI-crash path `PDCA-UNVERIFIABLE` per
brief.md:17, and (3) ship an interface test as the reproduction vehicle.

That is the honest call here: the crash lives entirely inside live GTK widget
allocation in `GrampletPane`, a `gi`/`gramps.gui` module the **headless** C4
runner cannot import (it would core-dump) and cannot exercise without a running
main loop. There is **no** import-light production seam a headless unit test
could drive that would *also* go red when the clamp is reverted — any unit test
fast enough to run headless can only call the helper directly, which is exactly
the decoupled green the human rejected. So:

- **Removed** Iteration 1's `gramps/gui/grampletconfig.py` helper module and
  `gramps/gui/test/grampletconfig_test.py`. The clamp now lives inline in
  `grampletpane.py`, so the patch **adds no core `.py` file** → no
  `po/POTFILES.skip` registration is needed (T2-potfiles N/A), and the
  Iteration-1 POTFILES churn is gone.
- `patch.diff` modifies only `grampletpane.py` (no `*_test.py`), so
  `run-verify.sh` emits `PDCA-UNVERIFIABLE` + exit 77 (confirmed locally), which
  routes a `- [ ]` into §6 NEEDS-HUMAN and the C6 accept-guard. The red→green
  *mechanic* is waived; the fix is judged by C5/T5 + the human + the interface
  repro.

## The reproduction vehicle (interface test)

`engine/interface/test_bug_0013864_dashboard_columns.py` (subclasses
`GrampsInterfaceTestCase`; advisory tier). The brief named
`tests/interface/test_bug_13864_dashboard_columns.py`; the live interface suite
in this repo is `engine/interface/test_*.py` with the zero-padded
`test_bug_00NNNNN_*` convention (cf. `test_bug_0011786_*`, `test_bug_0014100_*`),
so it ships there. A copy is kept in the bundle dir as the recorded artifact.

It opens `example.gramps` (TestTree) → Dashboard → "Configure the active view"
→ "Gramplet Layout" → types a pathological count into "Number of Columns", then
asserts Gramps stays **alive** (`_proc.poll()` stays `None`) and **responsive**
(an AT-SPI round-trip completes within a bounded timeout, run in a watchdog
thread so a frozen app blocks the thread, not the test). Pre-fix the process
crashes / the main loop freezes → assertion fails; post-fix the value is clamped
to 100 → survivable. Every navigation step `skipTest`s on an infra miss, so a
*failure* only fires once the entry has actually been driven — the real #13864
symptom.

The test uses `PATHOLOGICAL_COLUMNS = "100000"` rather than the reporter's 1000:
it is the same "accepted by the control" class (the entry accepts any positive
int), chosen large enough that the unbounded-allocation symptom manifests within
the headless harness's time budget. The fix clamps *any* such value identically,
so this does not narrow the invariant.

> Note: the interface suite is advisory in this repo (per-fix interface-level C4
> is staged, not a clean gate; AT-SPI under Xvfb can be flaky), so this test is
> the load-bearing *characterisation* the human weighs at sign-off, not a hard
> gate. I could not execute it in the Do beat (the C4 runner is headless — no
> D-Bus/AT-SPI); it is syntactically valid (`py_compile`, `black`) and follows
> the established harness API.

## Alternatives considered (with cost)

1. **Helper-only headless unit test (Iteration 1's approach).** Rejected — and
   not re-attempted — because it is decoupled from the production path: reverting
   the three clamp calls leaves it green. That is precisely the C4-decoupling the
   human flagged twice.

2. **Bound the control instead of the data — swap `add_pos_int_entry` for
   `add_spinner((1, MAX))`.** A `Gtk.SpinButton` with a bounded `Gtk.Adjustment`
   (`configure.py:618-654`) would reject out-of-range input at the widget. I did
   *not* choose this as the sole fix: it guards only the **live dialog** path and
   leaves the `.ini` (`grampletpane.py:1200`) and kwargs (`:1020`) paths
   unbounded — so a hand-edited `column_count=100000` still freezes at startup,
   failing the invariant. It is also a larger, riskier diff (a new widget type +
   a `(min, max)` range argument threaded through `config_panel`, changing the
   visible control from a free entry to a spinner — a UX change the brief puts
   **out of scope**: "redesigning the Gramplet-Layout UX … is a UX-direction
   call"). The data-side clamp is 1 helper + 4 one-line touch points and covers
   all three entry points. A spinner *and* the clamp could co-exist later as a UX
   nicety; the clamp is the correctness fix.

3. **Reject the input (raise/ignore on > MAX).** The brief allows "applies a sane
   count **or** rejects the input". Silent clamp + a tooltip stating the range is
   less surprising than discarding a keystroke mid-typing (the `changed` callback
   fires per character, so "1000" passes through "1","10","100" first — rejecting
   would need debounce/commit logic, more code for no invariant benefit).

## Open item for the maintainer (T5/V — raise in the PR)

`MAX_GRAMPLET_COLUMNS = 100` and the *silent* clamp are a product-level ceiling.
100 is far above any practical Dashboard layout but is a chosen value; the PR
should ask the maintainer whether they prefer a different ceiling, a hard
validation error, or the bounded-spinner UX (alternative 2). The brief lists a
hard max-columns policy as a UX-direction call to flag — flagging it here.

## Citations (target branch `maintenance/gramps61`)

- `gramps/gui/widgets/grampletpane.py:70` — constant/helper insertion point.
- `gramps/gui/widgets/grampletpane.py:1020` — `__init__` kwargs clamp.
- `gramps/gui/widgets/grampletpane.py:1199-1200` — `.ini` load clamp.
- `gramps/gui/widgets/grampletpane.py:1386-1405` — `set_columns` clamp + the
  `range(column_count)` allocation loop.
- `gramps/gui/widgets/grampletpane.py:1628-1642` — `config_panel` register +
  `add_pos_int_entry` (helptext added).
- `gramps/gui/configure.py:490-514` — unbounded `add_pos_int_entry` (the entry
  control); `:618-654` — `add_spinner` (alternative 2).
- `gramps/plugins/view/view.gpr.py:67-79` — Dashboard view category
  (`("Dashboard", _("Dashboard"))`) the interface test navigates to.
