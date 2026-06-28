# Build notes — issue 12110 / call-name-revalidate-on-given-change

Target branch: `gramps-project/gramps @ maintenance/gramps61`
(verified in the pinned worktree `../gramps-6.1`, HEAD `cbe5699b2e`,
`upstream/maintenance/gramps61`).

## Root cause (two sentences)

`EditName._validate_call` (the predicate that reds the Call field when the call
name is not part of the given name) is wired only to the **Call** field's
`validate` signal — `self.call_field.connect("validate", self._validate_call)`
plus a one-shot `validate(force=True)` at setup
(`gramps/gui/editors/editname.py:236-238` on the target). The **Given** field
(`given_field`, `editname.py:223-228`) has no hook that re-fires that
validation, so once the given name changes the red/black indicator is never
recomputed and goes stale.

## Fix — restore the invariant (smallest change that restores it)

The invariant the brief names: *the call-name validity indicator is a function
of the current given name; whenever the given name changes it is recomputed.*
The minimal change that restores it is to re-fire the existing call-name
validation when the given field changes:

1. `editname.py:223-228` — pass `changed=self._revalidate_call` to the
   `given_field` `MonitoredEntry`. `MonitoredEntry._on_change` already invokes
   its `changed` callback on every entry edit
   (`gramps/gui/widgets/monitoredwidgets.py:154-157`), so this is the editor's
   own established seam for "field changed" (the same `changed=` mechanism the
   surname field used for `update_group_as`, see the commented block at
   `editname.py:268-274`). No new signal machinery.
2. New method `_revalidate_call(self, obj)` — calls
   `self.call_field.obj.validate(force=True)`, the exact same force-validate the
   setup already performs at `editname.py:238`. Re-running it re-evaluates
   `_validate_call` against the **current** given name, flipping the red state.
   Guarded by `hasattr(self, "call_field")` because `given_field` is constructed
   before `call_field`; in practice the callback cannot fire during construction
   (`MonitoredEntry.__init__` sets the initial text *before* connecting the
   `changed` signal — `monitoredwidgets.py:123-125`), so the guard is purely
   defensive against any future reordering/reentrancy.

This is a *behavioural-consistency* invariant restore, so per principles §1.2/§2
the axis is "smallest change that restores the invariant", not smallest diff —
and the wiring above is exactly that.

## Why the predicate was extracted (and why it is not "manufactured scaffolding")

The C4 runner is headless; `editname.py` imports `gi.repository` (Gtk) at load,
so a unit test importing it core-dumps the runner (this is the documented
`T3-unit` headless segfault — `editreference_test.py` already triggers it).
To drive the **production** predicate headlessly without a parallel copy
(principles §3.4), I extracted the unchanged predicate into a new import-light
module `gramps/gen/utils/callname.py::call_name_is_valid(call_name,
given_name)`, and `_validate_call` now delegates to it
(`editname.py:173-178` post-patch). The semantics are byte-for-byte the
original (`split()` on whitespace, then split each token on `-`, then membership
test; `list(valid)` snapshots the same way `copy(validcall)` did) — the brief
puts "the validation rule itself" out of scope, and this preserves it. The now
-unused `from copy import copy` (`editname.py:30`) is removed.

This is **not** a non-`test_` module manufactured just to give `run-verify` a
file to revert (the INTEGRATION §4 / 820-pluginloading-gate anti-pattern):
production genuinely routes through `call_name_is_valid` — it is the live code
path `_validate_call` executes. The test drives that same function, not a copy.

## Test — `gramps/gui/editors/test/editname_test.py`

Import-light (`gramps.gen.utils.callname` + stdlib `unittest`; no `gi`, no
`gramps.gui`), so it runs under the plain headless `python3 -m unittest` C4
runner. It exercises the production predicate against **changing given-name
input**, which is exactly the demonstration the brief's Success criterion
names ("red→black and black→red transitions"):

- `test_red_to_black_when_given_filled_to_match` — bug case 1: Call="Jon",
  given "" (invalid/red) → given "Jon" (valid/black).
- `test_black_to_red_when_given_changed_away` — bug case 2: given "Marc",
  Call="Marc" (black) → given "Paul" (red).
- plus valid/invalid/empty/hyphenated coverage of the predicate.

red→green proven via the engine runner (not a hand-rolled `docker run`):
`PDCA_BUNDLE=… PDCA_LANE=0 ./engine/scripts/ubuntu/run-verify.sh` →
`green-with-fix=PASS / red-without-fix=PASS` on the **clean**
`upstream/maintenance/gramps61` lane worktree (the runner also cleared a stale
`essential-dependency.json` that a first run wrote only because the shared base
worktree was dirty from a concurrent bundle — the fix has **no** essential
dependency; it is pure `gen` + stdlib).

## What the unit test does and does not cover (honest scope)

The unit test proves the predicate is a correct function of the given name
(the invariant's *content*) and that, re-run on a changed given name, it yields
the right red/black transition. It does **not** by itself exercise the GTK
signal wiring (`changed=` → `_revalidate_call` → `validate(force=True)` →
`validate` signal → `_validate_call`), which is GTK-bound and cannot run
headlessly. That wiring is verified by inspection against the editor's existing
`MonitoredEntry` seam (citations above) and is the human's GUI sign-off check
(`Surfaces: gui`). The brief explicitly accepts the headless predicate test as
the demonstration (its "If the predicate cannot be reached headlessly …"
fallback to a GUI repro does not apply, since it *can* be reached). I did not
ship a fragile AT-SPI Name-editor repro: navigating Person→Names→Name-editor
sub-dialog and reading the Call field's red state via AT-SPI would `skipTest`
under the headless harness far more often than it would give a clean red→green,
adding noise rather than evidence.

## Alternatives considered / rejected

- **Wire the GTK `validate` signal directly from the given field instead of via
  `changed=`.** Rejected: `validate` is the call field's own validation signal;
  the natural "this field's text changed" seam on a `MonitoredEntry` is its
  `changed` callback (`monitoredwidgets.py:154-157`), already used elsewhere in
  this very editor. Using it is fewer moving parts and consistent with house
  style.
- **Recompute inside `_validate_call` by also observing the given field there.**
  Not possible — `_validate_call` only runs when the validation is *triggered*;
  the whole defect is that nothing triggers it on a given change.
- **Put the predicate in `gramps/gen/lib/name.py` (the `Name` class).** Rejected
  as wider scope: it would add a method to a core lib class for a GUI-validation
  helper. A standalone import-light util in `gramps/gen/utils/` is the smaller,
  self-contained home (sits next to `callback.py`, also `POTFILES.skip`).

## Files / registration

- New `gramps/gen/utils/callname.py` — no translatable strings (`_()`), so
  registered in `po/POTFILES.skip` (next to `callman.py`), per doc-16
  §Adding and removing Python files.
- New `gramps/gui/editors/test/editname_test.py` — test module, registered in
  `po/POTFILES.skip` (next to `editreference_test.py`).
- `T2-potfiles` (gating) therefore satisfied for both added `.py`.

## Formatter

`python3 -m black --check` over `callname.py`, `editname.py`, `editname_test.py`
→ "All done! … 3 files would be left unchanged." (commit-ready for the gramps
pre-commit `black` hook).
