# Build notes — issue 10628 (deep-connections-repeats-same-path)

## Root cause (two sentences)

`DeepConnectionsGramplet.main()` runs a breadth-first search whose queue items
are `(handle, path)`. When it dequeues the active/target person it reports the
path, pauses, and — on resume — **falls through and expands the target like any
other node** (`DeepConnectionsGramplet/DeepConnectionsGramplet.py:457-463` on
maintenance/gramps60), pushing the target's own relatives into the queue; those
relatives then re-reach the target, so the next "Continue" re-emits the same
connection with the target re-entered as an interior step — the reporter's
"same path every time I press Continue."

## The fix

Add a single `continue` after the pause/`yield False` in the found-the-target
branch (`DeepConnectionsGramplet/DeepConnectionsGramplet.py:455` original →
new line after the `yield False` at original :455). On resume the loop now
advances straight to the next queued candidate instead of expanding the target.

Why this is the root-cause fix, not a symptom guard:
- A connection *to* the target never needs to route *through* the target, so
  expanding the target can only ever produce spurious back-paths. Removing that
  expansion removes the source of the repeats.
- Genuinely distinct connections are enqueued by *other* relatives during the
  normal BFS before the target is first found (and continue to be as the queue
  drains); they are untouched, so all independent paths remain reachable —
  exactly the Success criterion.

I validated the BFS behaviour by replaying the production `get_relatives` +
`main` loop on the test fixture (gi-free local sim, since the C4 docker runner
needed an approval unavailable in this session):

```
BUGGY: 3 paths -> ['X','D'], ['Y','D'], ['C','A','X','D']  (3rd re-enters target A)
FIXED: 2 paths -> ['X','D'], ['Y','D']                      (no re-entry)
```

The real test drives `main()` itself, so this matches what C4 exercises.

## Alternatives considered and rejected

1. **Add the target to `self.cache` when found.** Rejected: the found-check
   (`if current_handle == active_person.handle`) runs *before* the cache check
   (`elif current_handle in self.cache`), so caching the target does not stop it
   being re-reported, *and* it would wrongly suppress the genuinely distinct
   target entries already queued via other relatives (the via-Y path). It treats
   a symptom and breaks reachability — fails the Success criterion.

2. **Track reported paths and skip duplicates before emitting.** This is the
   "exclude the already-reported path" framing in the brief's Scope. Rejected as
   heavier *and* less correct: the spurious paths are not byte-identical to the
   first (`['C','A','X','D']` ≠ `['X','D']`), so a dedup key has to normalise
   "the same connection" — and any normalisation that collapses `C-A-X-D` onto
   `X-A` would also need to not collapse the genuine `Y-A`. Concretely it costs
   a new per-search set, a path-signature helper, and a guard at the emit site
   (~15-20 lines) versus the 1-line `continue`, while still leaving the target
   being pointlessly expanded (work + queue growth). The `continue` removes the
   *generator* of the duplicates, so there is nothing to deduplicate.

3. **Stop the search entirely after the first found path** (so "Continue" just
   says "No further paths"). Rejected: that is the reporter's *fallback*
   suggestion, but the brief's Success criterion explicitly requires successive
   Continues to yield the *distinct* alternative connections, which this fix
   preserves.

## Test

`DeepConnectionsGramplet/tests/test_deep_connections_paths.py` (new) drives the
real `main()` generator (production path, principles §3.4) against a fixture
with two node-disjoint Home→target connections (via X and via Y) plus a private
child of the target that triggers the bounce-back repeat. It asserts:
- no produced path re-enters the target as an interior anchor (the red-maker:
  fails pre-fix on the `C-A-X-D` path, passes post-fix);
- both independent connections remain reachable (reachability guard);
- no two consecutive reported paths are identical.

Import-safety: the gramplet imports `gi`/Gtk at load; the addon C4 leg runs
under `xvfb` with the GI bootstrap (same pattern as the existing
`tests/test_deep_connections.py`), and the harness skips `Gramplet.__init__`,
so no display-bound widget is ever constructed.

## Commit-readiness / scope

- `black 26.5.0` run over both touched files (prod left unchanged; the test was
  reformatted before the diff was generated).
- Patch `git apply --check`s cleanly on both `addons-source-6.0` and
  `addons-source-6.1` worktrees (the file is byte-identical across the two
  maintenance branches, so the cherry-pick remains correct, not just appliable).
- New file is an addon test (`test_*.py` under the addon `tests/` package, which
  already carries `__init__.py`) — no `po/POTFILES` entry required per the brief.
- No changes to result formatting, the #946 home-person-interior handling, or
  relationship naming (out of scope).
