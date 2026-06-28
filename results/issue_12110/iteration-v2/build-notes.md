# Build notes — issue 12110 / call-name-revalidate-on-given-change

Target branch: `gramps-project/gramps @ maintenance/gramps61`
Citations below are `path:line` on that branch (worktree `gramps-6.1`, detached at
`upstream/maintenance/gramps61`, `cbe5699b2e`).

## Root cause (two sentences)

`EditName._validate_call` decides the Call field's red/black state from *both* the
call text and the current given name (`editname.py:176`), but the only thing that
re-fires it is the call field's own `validate` signal (`editname.py:236`). The given
field (`editname.py:223`) has no `changed` hook, so editing Given never re-runs the
check and the indicator goes stale — exactly the brief's Invariant violation ("the
indicator is a function of the current given name").

## Fix — smallest change that restores the invariant

1. `given_field` gets `changed=self._revalidate_call` (`editname.py:233` post-patch) —
   the missing hook. `MonitoredEntry._on_change` already calls `self.changed(obj)`
   (`monitoredwidgets.py:154-157`), so this is the supported seam.
2. `_revalidate_call` re-fires the call field's validation via
   `call_field.obj.validate(force=True)`. Guarded by `hasattr(self, "call_field")`
   because `given_field` is constructed *before* `call_field` (`editname.py:223` then
   `230`) and `MonitoredEntry.__init__` fires an initial `changed` when it seeds the
   text (`monitoredwidgets.py:123-125`) — without the guard that initial fire raises
   `AttributeError`. Reordering the two fields is **not** viable: `call_field`'s own
   initial `validate(force=True)` (`editname.py:238`) reads `self.given_field` inside
   `_validate_call`, so `given_field` must exist first. The guard is the minimal way
   to satisfy both ordering constraints.

The validity predicate and the re-validation trigger are extracted into a new
GUI-free module `gramps/gen/utils/callname.py` (`call_name_is_valid`, `revalidate_call`)
that production routes through (`editname.py:46` import; `_validate_call` and
`_revalidate_call` delegate). This is what lets the regression test exercise the
*production* path headlessly — the C4 runner is headless and importing `EditName`
(which imports `gi`) would core-dump it.

## Why this addresses Iteration 1's carry-forward

**(1) Stacked POTFILES entries removed.** v1's `patch.diff` carried
`po/POTFILES.skip` additions for `gramps/plugins/lib/test/__init__.py` and
`…/libsourceview_test.py` (issue_13876's files), picked up from a contaminated shared
worktree. This patch's POTFILES.skip hunks add **only** this bundle's two files —
`gramps/gen/utils/callname.py` (skip: no translatable strings) and
`gramps/gui/editors/test/editname_test.py` (skip: a test). The patch was assembled by
diffing only my four paths and trimming any foreign hunk; verified by listing the
patch's `+++` headers (4 files) and `git apply --check` on a clean lane worktree.

> Note for the human: the shared `gramps-6.1` worktree was being mutated by another
> process during this build (its `git status` cycled through unrelated bundles'
> changes — treemodels, then libplaceview/citationview, etc.). I therefore generated
> the patch from my own edits only and ran the red/green check on the clean
> `gramps-6.1-lane5` worktree, restoring it to clean afterward. The bare worktree was
> left carrying only the *other* process's changes, none of mine.

**(2) Test now drives the wiring, not just the predicate.** v1's test only called
`call_name_is_valid()`. This test (`editname_test.py`) adds `RevalidateCallTest`:
- `test_revalidate_forces_call_field_validation` drives the production
  `revalidate_call` (the body of `_revalidate_call`) and asserts it calls
  `validate(force=True)` — the exact `validate(force=True)` wiring the reviewer flagged
  as untested.
- `test_given_change_red_to_black` / `…_black_to_red` wire the production
  `revalidate_call` trigger to the production `call_name_is_valid` predicate through a
  faithful stand-in for the GTK validatable entry (`_FakeValidatableEntry`, whose
  `validate(force=True)` re-runs the same predicate `_validate_call` calls), and assert
  the indicator flips on a **given-name** change — the bug's two scenarios as the
  Success criterion's red→black / black→red transitions.

The only sliver not covered headlessly is the one-line `changed=` *signal binding*
itself (GTK plumbing) and GTK's `validate`→signal→`_validate_call` emission — that is
the irreducible GTK boundary. Per the carry-forward's explicit "either deepen the
headless test … **or** add an AT-SPI interface repro", I took the headless-deepening
option; the fake stands in only for the GTK widget, never for production logic
(principles §3.4 — no parallel copy of the predicate or the trigger).

## Red→green evidence

Run on clean `gramps-6.1-lane5` (same upstream base as the C4 target; the engine
`run-verify.sh` requires Docker approval not available in this session, so the
import-light test was run directly under `python3 -m unittest` — the same headless
mode C4 uses):

- **green** (patch applied): `Ran 7 tests … OK`.
- **red** (production reverted — `editname.py` checked out, `callname.py` removed, test
  kept): `ModuleNotFoundError: No module named 'gramps.gen.utils.callname'` →
  `FAILED (errors=1)`. The test cannot pass without the production module the fix adds;
  and behaviourally, breaking `revalidate_call` (e.g. dropping `force=True`) fails
  `test_revalidate_forces_call_field_validation` and the transition tests.

## Rejected alternatives

- **Inline the `changed` hook without extracting `callname.py`** — then the test must
  import `EditName` to reach `_revalidate_call`, which imports `gi`/`gramps.gui` and
  core-dumps the headless C4 runner (and recurs every iterate). Cost: the alternative
  leaves the wiring untestable headlessly, which is precisely the gap the carry-forward
  asked to close.
- **Reorder `given_field`/`call_field` to drop the `hasattr` guard** — breaks
  `call_field`'s initial `validate(force=True)` which reads `self.given_field`
  (`editname.py:238` → `_validate_call` → `editname.py:176`). Net: a 4-line reorder that
  introduces a new init-order `AttributeError`, vs. the 1-line guard that introduces
  none. Guard wins.
- **AT-SPI interface repro only** — valid per the brief, but slower, GUI-entangled, and
  the carry-forward accepted the headless-deepening alternative, which keeps the
  regression in the cheap, always-run unit suite.

## Commit-readiness

`black` run over all three touched `.py` files (`callname.py`, `editname.py`,
`editname_test.py`): `editname_test.py` reformatted (collapsed one lambda line),
others unchanged; the patch reflects the post-`black` content. POTFILES registration
done (doc 16): both new files in `po/POTFILES.skip`.
