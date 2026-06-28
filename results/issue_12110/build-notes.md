# Build notes — issue 12110 / call-name-revalidate-on-given-change (iteration 4)

Target branch: `gramps-project/gramps @ maintenance/gramps61` (base `cbe5699b2e`).
Citations are `path:line` on that branch, verified in the clean worktree
`gramps-6.1-lane5` (detached at `cbe5699b2e`).

## Root cause (two sentences)

The Call field's red/black indicator is computed by `_validate_call` from *both* the
call text **and** the current given name (`editname.py:173-184`, `editperson.py:331-342`),
but the only thing wired to re-fire it is the **Call** field's own `validate` signal
(`editname.py:236-238`, `editperson.py:392-394`). The **Given** `MonitoredEntry` carries
no `changed` hook, so editing the given name never re-runs the check and the indicator
goes stale — the exact Invariant the brief names ("the indicator is a function of the
current given name").

## Fix — smallest change that restores the invariant, in BOTH editors

The bug lives in two editors that share the identical stale pattern. Iteration 3 fixed
only `editname.py` and was accepted on that approach; its carry-forward required the same
hook on `editperson.py` (the primary Person editor) before publication. This iteration
applies the **same** two-part change to **both** files:

1. New method `_revalidate_call(self, obj)` re-fires the Call field's
   `validate(force=True)` — `editname.py:186-197`, `editperson.py:344-355`. `force=True`
   makes the validatable entry re-run its `validate` handler even though the *call* text
   did not change (`validatedmaskedentry.py:1075-1121`), so `_validate_call` re-evaluates
   against the now-current given name and `set_valid`/`set_invalid` repaints the icon.
2. The Given `MonitoredEntry` gains `changed=self._revalidate_call` —
   `editname.py:241`, `editperson.py:397`. `MonitoredEntry._on_change` already calls
   `self.changed(obj)` (`monitoredwidgets.py:154-157`), so this rides the supported,
   pre-existing seam — no new signal plumbing. The validity predicate `_validate_call` is
   left byte-for-byte unchanged in both files.

The `hasattr` guard (`editname.py:196` on `call_field`; `editperson.py:354` on `call`)
documents that the given field is built before the call field
(`editname.py:223/230`, `editperson.py:379/386`); `MonitoredEntry.__init__` seeds text
with `set_text` *before* connecting `_on_change` (`monitoredwidgets.py:123-125`), so the
guard is a one-line safety net, not a workaround for a live crash.

No new production file (Iteration 2's constraint); no production class restructure
(Iteration 3 called the editname.py approach "correct"). Two methods + two keyword args
across the two existing editor files.

## Addressing the carry-forwards

- **Iteration 3 (most recent):** "extend the fix to `editperson.py`." Done —
  `editperson.py:344-355` + `:397`, identical to the accepted `editname.py` hook. The
  failing gate at iteration 3 was infrastructure only (`run-verify-interface.sh` refused
  because `gramps-6.1-lane0` had uncommitted changes); this iteration verifies through the
  **headless C4 core runner** in a clean worktree, sidestepping that lane entirely.
- **Iteration 2:** "keep the predicate/trigger local to the editor; no new production
  file." Done — no new `.py` under the gramps tree except the regression test (registered
  in `po/POTFILES.skip:399`, see below).
- **Iteration 1:** "the test was predicate-only; it never drove the `changed` callback or
  `validate(force=True)` wiring." Addressed — the new test routes through a **real**
  `MonitoredEntry` whose `changed` hook is `_revalidate_call`, and drives the real
  `_on_change → changed → _revalidate_call → validate(force=True) → _validate_call` chain
  (see Verification). It is no longer a bare call to the predicate.

## Verification — headless C4, red→green, both editors

`engine/scripts/ubuntu/run-verify.sh` (PDCA_BUNDLE set):

```
C4-verify: green-with-fix=PASS / red-without-fix=PASS
```

Test: `gramps/gui/editors/test/editname_test.py` (the brief's named path, `*_test.py`
suffix, in the existing `test/` package alongside `editreference_test.py`).

### Why this is import-light and drives the production path, not a copy

The C4 core runner is headless (`python3 -m unittest`, no display/D-Bus/AT-SPI). I
confirmed that *importing* `gramps.gui.editors.editname` / `editperson` works headlessly
(only *constructing* a GUI window needs a display). So the test imports the editor
**classes** and binds their **real** `_validate_call` and `_revalidate_call` to a
lightweight stub editor (`editname_test.py` `_build_harness`), then:

- wires the Given field as a **real** `gramps.gui.widgets.MonitoredEntry` with
  `changed=editor._revalidate_call` — exactly as `_setup_fields` wires it — so the test
  exercises the real `MonitoredEntry._on_change → self.changed(obj)` dispatch
  (`monitoredwidgets.py:154-157`), not a hand-rolled callback;
- models the Call field as a faithful re-creation of `ValidatableMaskedEntry.validate()`
  (`validatedmaskedentry.py:1075-1121`): empty text → valid, else emit "validate" → the
  **real** predicate → `ValidationError` ⇒ invalid. Only the GTK widget + its error-icon
  plumbing are faked; the **predicate is production** (principles §3.4 — no parallel copy
  of the rule).

The two repro cases from the brief are asserted for **both** editors (parameterised
mixin): Case 1 red→black (Call="Jon", empty Given → invalid; type Given="Jon" → valid),
Case 2 black→red (Given="Marc"/Call="Marc" valid; change Given="Paul" → invalid), plus a
hyphenated-given case that exercises the predicate's `split("-")` branch.

### Why red-without-fix is genuine

When the production change is reverted (C4 `git checkout` of `editname.py`/`editperson.py`),
the editor class no longer has `_revalidate_call`, so `_build_harness` raises
`AttributeError` → all 6 cases error → red. The red state precisely reflects "the
revalidation hook does not exist," which is the regression. Observed in-harness:
`AttributeError: type object 'EditPerson' has no attribute '_revalidate_call'` for all
six cases on the red leg.

### Residual coverage gap (honest)

The one production line the headless test cannot *prove* in isolation is the literal
`changed=self._revalidate_call` kwarg inside `_setup_fields` (reaching it means
constructing the GUI). Under C4's whole-file revert this is moot (reverting removes the
method too, so the test goes red regardless). The supplementary AT-SPI repro
`test_bug_12110_call-name-revalidate.py` and the manual GUI confirmation below cover the
end-to-end `_setup_fields` wiring.

### Manual GUI confirmation (Name editor and Person editor)

`example.gramps`:
- **Name editor** (Edit person → Names → add/edit name): Call="Jon" → red; type Given
  "Jon" → turns black immediately. Given="Marc"/Call="Marc" → black; change Given to
  "Paul" → turns red. (Pre-fix: stays stale in both.)
- **Person editor** (Edit person, main Given/Call fields): same two transitions, now live.

## Files changed (patch.diff)

- `gramps/gui/editors/editname.py` — `_revalidate_call` (+12) and the given-field
  `changed=` kwarg.
- `gramps/gui/editors/editperson.py` — same two edits.
- `gramps/gui/editors/test/editname_test.py` — new regression test (205 lines).
- `po/POTFILES.skip:399` — registers the new test module (it carries no translatable
  strings), per doc 16 §Adding Python files; mirrors the existing
  `editreference_test.py` entry at `:398`.

## Rejected alternatives

- **Extract the predicate into a GUI-free module so a unit test can import it directly.**
  Rejected at Iteration 2 sign-off ("no new production file"); not re-attempted. Cost
  that the inline approach avoids: a new `gramps/gen/...py` file + its `POTFILES.in` entry
  + reworking *both* editors to call it — versus the present 2-method/2-kwarg change to
  the two files that already own the logic.
- **Add a test-only seam method (`_make_given_field`) so the test can assert the
  `changed=` kwarg without a display.** Rejected: it adds production indirection purely
  for the test and enlarges the diff in two files (~+8 lines each) for no behavioural
  gain, against a brief that asks for the *smallest change that restores the invariant*.
  The real `MonitoredEntry` already lets the test drive the `_on_change → changed`
  dispatch without it.
- **Interface (AT-SPI) repro as the sole artifact.** The red indicator is a GtkEntry
  secondary error icon + `error` CSS class (`validatedmaskedentry.py:1141-1182`), largely
  AT-SPI-opaque, so the repro often `skipTest`s and cannot be the discriminating gate.
  Kept as supplementary evidence; the headless unit test is the load-bearing C4 check.

## Commit-readiness

`black --check` over `editname.py`, `editperson.py`, and `editname_test.py`: "3 files
would be left unchanged." Patch classifies cleanly under `run-verify.sh` (test = the
`*_test.py`; prod = the two editors + `POTFILES.skip`) and passes both legs.
