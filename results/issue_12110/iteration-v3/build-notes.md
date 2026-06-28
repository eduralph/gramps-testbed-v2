# Build notes — issue 12110 / call-name-revalidate-on-given-change

Target branch: `gramps-project/gramps @ maintenance/gramps61` (base `cbe5699b2e`).
Citations are `path:line` on that branch (verified in worktree `gramps-6.1-lane5`,
detached at `cbe5699b2e`).

## Root cause (two sentences)

`EditName._validate_call` (`editname.py:173-184`) decides the Call field's red/black
state from *both* the call text and the current given name, but the only thing wired
to re-fire it is the Call field's own `validate` signal (`editname.py:236-238`). The
`given_field` `MonitoredEntry` (`editname.py:223-228`) carries no `changed` hook, so
editing the Given name never re-runs the check and the indicator goes stale — the
exact Invariant violation the brief names ("the indicator is a function of the current
given name").

## Fix — smallest change that restores the invariant (editname.py only)

Two edits, both in `gramps/gui/editors/editname.py`:

1. **`given_field` gains `changed=self._revalidate_call`** (added after
   `editname.py:227`, the `self.db.readonly` arg of the `given_field` MonitoredEntry).
   `MonitoredEntry._on_change` already calls `self.changed(obj)`
   (`monitoredwidgets.py:154-157`), so this is the supported, pre-existing seam — no
   new signal plumbing.
2. **New method `EditName._revalidate_call`** (inserted after `_validate_call`, i.e.
   after `editname.py:184`) re-fires `self.call_field.obj.validate(force=True)` — the
   same `validate(force=True)` the editor already uses for the Call field's initial
   check (`editname.py:238`). `force=True` makes the validatable entry re-run its
   `validate` handler (`validatedmaskedentry.py:1075`) even though the *call* text did
   not change, so `_validate_call` re-evaluates against the now-current given name and
   `set_valid`/`set_invalid` repaints the icon (`validatedmaskedentry.py:1120,1139`).

That is the whole production change: **one new method + one keyword argument.** The
validity predicate `_validate_call` is left byte-for-byte unchanged.

### Why the `hasattr(self, "call_field")` guard

`given_field` is constructed before `call_field` (`editname.py:223` then `230`). The
guard documents that ordering dependency and prevents an `AttributeError` if a future
refactor ever lets the given field's `changed` fire before `call_field` exists. (In
the current code `MonitoredEntry.__init__` seeds the text with `set_text` *before*
connecting `_on_change` — `monitoredwidgets.py:123-125` — so the guard is not hit during
construction; it is a one-line safety net, not a workaround for a live crash.)

## Addressing Iteration 2's carry-forward (the gate that rejected v2)

> "the call-name validity predicate and revalidation trigger must stay local to
> `gramps/gui/editors/editname.py`. Do not introduce `gramps/gen/utils/callname.py` or
> any other new production file; inline the logic in editname.py directly."

Done. **No new production module.** v2's `gramps/gen/utils/callname.py` is gone; the
predicate stays inline (untouched) and the trigger is the new `_revalidate_call`
method *in editname.py*. The patch touches exactly one file and adds/removes no `.py`
file, so there is **no `po/POTFILES.*` change** — which also disposes of Iteration 1's
"stacked POTFILES entries" complaint at the source (there is nothing to stack).

> "T3 unit-runner crash is a known infrastructure issue — do not block on it. T5/V: if
> headless GTK signal-path testing is not feasible, manual confirmation of the Name
> editor behaviour is sufficient."

Acknowledged and acted on (see Verification).

## Verification

### Why there is no headless `*_test.py`, and C4 is `unverifiable`

The brief's test field is explicit: *"If the predicate cannot be reached headlessly,
ship the GUI repro at `engine/interface/test_bug_12110_call-name-revalidate.py` and
record C4 (unit) as unverifiable for human sign-off."*

With the predicate and trigger constrained to `editname.py` (Iteration 2's accepted
scope), reaching them from a unit test means `import`ing `EditName`, which pulls in
`gi` / `gramps.gui.*` at load. The C4 core runner is **headless** (plain
`python3 -m unittest`, no display/D-Bus/AT-SPI); importing a `gramps.gui` editor there
core-dumps the runner — the recurring crash the harness guidance warns about. A
`@skipUnless`-gated unit test does not help either: a *skipped* test exits 0, so C4's
**red-without-fix** leg would also "pass", and the gate requires red-without-fix to
**fail**. So a headless unit test cannot both run and discriminate the bug under this
scope. This is precisely the brief's documented fallback.

Concretely, `run-verify.sh` classifies `patch.diff` (only `+++ b/gramps/gui/editors/
editname.py`, no `*_test.py`) and takes the documented branch:
`PDCA-UNVERIFIABLE: patch ships no core test … the human accepts at sign-off` → exit
77, routing a `[ ]` into SUMMARY §6 for the human. (I could not *execute*
`run-verify.sh` in this session — it shells out to Docker, which needs an approval not
available here — but the classification is deterministic from the patch's `+++`
headers, which are the single editname.py file.)

### Regression artifact: the AT-SPI repro

`engine/interface/test_bug_12110_call-name-revalidate.py` drives the **real** Name
editor end to end: open Edit Person → Names tab → Add → Name Editor (the production
`EditName` from `editname.py`), set `Call="Jon"` with an empty Given (expect invalid),
then set `Given="Jon"` and assert the Call field is **no longer** invalid. It exercises
the actual `given_field` `changed` → `_revalidate_call` → `validate(force=True)` →
`_validate_call` path — no parallel copy of the predicate (principles §3.4).

The Call field's "red" is a GtkEntry secondary error icon + an `error` CSS class
(`validatedmaskedentry.py:1141-1182`); GTK does not reliably surface either through
AT-SPI. The repro therefore `skipTest`s (records UNVERIFIABLE) at any navigation or
readout step the accessibility tree does not expose, rather than false-failing. When
the indicator is readable it discriminates the bug (pre-fix: frozen after the Given
edit → FAIL; post-fix: tracks the new Given → PASS).

### Manual confirmation (the load-bearing check, per Iteration 2's T5/V)

`example.gramps` → Edit a person → **Names** → Add/Edit a name (opens the Name Editor):

- **Case 1 (red→black):** Call = `Jon` → field turns red. Type `Jon` into Given.
  *Post-fix:* the Call field turns black immediately, without re-touching Call.
  *Pre-fix:* it stays red.
- **Case 2 (black→red):** Given = `Marc`, Call = `Marc` → black. Change Given to
  `Paul`. *Post-fix:* the Call field turns red. *Pre-fix:* it stays black.

## Rejected alternatives

- **Extract the predicate/trigger into a GUI-free module
  (`gramps/gen/utils/callname.py`) so a headless unit test can drive it.** This was
  Iteration 2's approach and was **rejected at sign-off** ("Do not introduce
  `gramps/gen/utils/callname.py` or any other new production file"). Not re-attempted.
- **Reorder `given_field` before/after `call_field` to drop the `hasattr` guard.**
  `call_field`'s initial `validate(force=True)` (`editname.py:238`) reads
  `self.given_field` inside `_validate_call` (`editname.py:176`), so `given_field` must
  be constructed first; reordering to satisfy the guard-removal would break that
  initial check. Net cost of the alternative: a 4-line reorder that introduces a new
  init-order read-before-assign, versus the 1-line guard that introduces none. Guard
  kept.
- **AT-SPI interface repro as the *only* artifact, no manual note.** The error-icon
  indicator is largely AT-SPI-opaque, so the repro often `skipTest`s; pairing it with
  the explicit manual repro above is what actually closes the Success criterion for the
  human, per Iteration 2's "manual confirmation is sufficient".

## Commit-readiness

`black` (target-version py310) over `gramps/gui/editors/editname.py`: "would be left
unchanged". `py_compile`: clean. `git apply --check` of `patch.diff` against clean
`maintenance/gramps61`: applies (rc 0). The interface test was `black`-formatted in the
testbed repo. No `po/POTFILES.*` change is needed (no `.py` file added or removed in
the gramps tree).
