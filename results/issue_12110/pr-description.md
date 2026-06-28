# Call-name validity re-validation on given-name change (bug 12110)

## Root cause

The Call field's red/black indicator is computed by `_validate_call` from both the call text **and** the current given name (`gramps/gui/editors/editname.py:173-184`, `gramps/gui/editors/editperson.py:331-342`), but the only thing wired to re-fire it is the **Call** field's own `validate` signal (`editname.py:236-238`, `editperson.py:392-394`). The **Given** `MonitoredEntry` carries no `changed` hook, so editing the given name never re-runs the check and the indicator goes stale — a violation of the behavioural invariant that the red/black state reflects the *current* given name.

## Fix

Add a new `_revalidate_call(self, obj)` method to both editors that re-fires the Call field's `validate(force=True)` (`editname.py:186-197`, `editperson.py:344-355`). The `force=True` flag ensures the validatable entry re-runs its `validate` handler even though the *call* text did not change, so `_validate_call` re-evaluates against the now-current given name.

Wire the Given field's `MonitoredEntry` `changed` callback to this method (`editname.py:241`, `editperson.py:397`). `MonitoredEntry._on_change` already calls `self.changed(obj)` (`monitoredwidgets.py:154-157`), so this rides the supported, pre-existing seam — no new signal plumbing is required.

The validity predicate `_validate_call` itself is left byte-for-byte unchanged in both files. The `hasattr` guard on the call field documents the field-build order (`editname.py:223/230`, `editperson.py:379/386`) and is a safety net, not a workaround for a live crash.

## Verified against

- `gramps/gui/editors/editname.py` — the two-part change: `_revalidate_call` method (lines 186-197) + given-field `changed=` kwarg (line 241)
- `gramps/gui/editors/editperson.py` — identical two-part change: `_revalidate_call` method (lines 344-355) + given-field `changed=` kwarg (line 397)
- `gramps/gui/widgets/monitoredwidgets.py:154-157` — the `_on_change` dispatch that invokes the `changed` callback
- `gramps/gui/widgets/validatedmaskedentry.py:1075-1121` — the `validate(force=True)` dispatch that re-evaluates the predicate
- `po/POTFILES.skip` — test-module registration at line 399

## Test

Regression test: `gramps/gui/editors/test/editname_test.py` (205 lines, parameterised over both EditName and EditPerson).

The test is **headless** (no display/D-Bus/AT-SPI) and **import-light** by design — it imports the editor classes (which load fine headlessly) but never constructs a GUI window. It exercises the **production** `_validate_call` predicate and `_revalidate_call` trigger bound to a lightweight stub editor, driving them through a **real** `MonitoredEntry` whose `changed` hook is wired exactly as `_setup_fields` wires it in production.

The Call field is modelled as a faithful re-creation of `ValidatableMaskedEntry.validate()`'s dispatch around the *real* predicate (empty text → valid, else emit "validate" → custom predicate → `ValidationError` ⇒ invalid). Only the GTK widget and its error-icon plumbing are faked; the predicate is production code (principles §3.4 — no parallel copy of the rule).

**Test cases** (parameterised for both editors):
1. **Case 1 red→black:** Call="Jon" with empty Given is invalid (red); typing Given="Jon" clears the red without touching Call.
2. **Case 2 black→red:** Given="Marc"/Call="Marc" is valid (black); changing Given to "Paul" turns Call red.
3. **Hyphenated-given case:** exercises the predicate's `split("-")` branch (Given="Jean-Marc" → call="Marc" valid).

**Red without the fix:** When the production change is reverted (C4 `git checkout` of `editname.py`/`editperson.py`), the editor class no longer has `_revalidate_call`, so `_build_harness` raises `AttributeError` → all 6 cases error → red. The red state precisely reflects "the revalidation hook does not exist," which is the regression.

**Manual GUI confirmation** in example.gramps:
- **Name editor** (Edit person → Names → add/edit name): Call="Jon" → red; type Given "Jon" → turns black immediately. Given="Marc"/Call="Marc" → black; change Given to "Paul" → turns red immediately.
- **Person editor** (Edit person, main Given/Call fields): identical transitions, now live.

Fixes #12110
