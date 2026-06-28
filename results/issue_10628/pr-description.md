# Deep Connections: skip expanding target in path search

## Root cause

`DeepConnectionsGramplet.main()` in the breadth-first path search finds the active/target person and reports the path, then pauses. On resume ("Continue"), the search falls through and expands the target itself (lines 457–463), pushing the target's own relatives into the queue; those relatives re-reach the target, so the next "Continue" re-emits the same connection with the target re-entered as an interior step, creating the repeated path behavior.

## Fix

Adds a `continue` statement after the pause/`yield False` (line 455) in the found-target branch of `DeepConnectionsGramplet.main()`, skipping the target expansion. On resume, the loop now advances directly to the next queued candidate instead of re-expanding the target. Since genuinely distinct connections are already enqueued by *other* relatives during the normal BFS before the target is first found, they remain reachable and reported on successive "Continue" presses — exactly matching the success criterion.

Also adds a new regression test `DeepConnectionsGramplet/tests/test_deep_connections_paths.py` that drives the production `main()` generator on a fixture with two node-disjoint paths plus a target child, asserting that: (1) no produced path re-enters the target, (2) both independent connections remain reachable, and (3) consecutive paths are never identical.

## Verified against

- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:455` — the pause/`yield False` where the `continue` is inserted
- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:457-463` — the target expansion (fall-through) that is now skipped on resume
- `DeepConnectionsGramplet/tests/test_deep_connections_paths.py` — new regression test file implementing the production-path fixture harness

## Test

New regression test `DeepConnectionsGramplet/tests/test_deep_connections_paths.py` drives the real `DeepConnectionsGramplet.main()` generator (not a copy) on an in-memory fixture with two node-disjoint Home→target paths and a target child that triggers the repeated-path behavior. The test harness overrides only GUI surface methods (`append_text`, `link`, `pretty_print`, `pause`), allowing `main()` to run the production queue/cache/`get_relatives` path-construction code. It verifies: no produced path re-enters the target, both independent paths remain discoverable, and no two consecutive paths are identical. The test fails pre-fix on the spurious C-A-X-D path that re-enters the target, passes post-fix with only X-D and Y-D reported.

Fixes #10628
