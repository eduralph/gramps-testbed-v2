## Root cause

The DescendantsLines report derives the graphic's output filename solely from its persisted "Destination" option (`DescendantsLines.py:316-320`), which is saved in the report's option state and persists across Gramps sessions. The addon ignores the destination the user selects for the current run in the standard report dialog's "Document Options" (`gramps/gen/plug/report/_reportbase.py:56-59`), so the graphic always lands on the previous session's name.

## Fix

Extract the filename derivation into a pure helper module `descendantslines_output.py` (free of `gi` imports so it can be unit-tested headlessly) and route production through `derive_output_filename` (`DescendantsLines.py:316-324`). The function sources the current run's destination (`options_class.get_output()`, `gramps/gen/plug/report/_options.py:914-920`) instead of the persisted option, falling back to the persisted option only when no current destination is given. When the derived name would equal the document's own output path, a `-chart` suffix is added to avoid clobbering by the document's `close()`.

## Verified against

- `DescendantsLines.py:316-320` — the original code deriving filename from the persisted option only
- `DescendantsLines.py:1548-1551` — the `DestinationOption` definition and its persistence across sessions
- `DescendantsLines.py:455` — where the graphic is written via `draw_file(p, self.output_fn, …)`
- `gramps/gen/plug/report/_reportbase.py:56-59` — the framework obtaining the current run's document destination
- `gramps/gen/plug/report/_options.py:914-920` — `get_output()` returning the user's chosen destination for this invocation

## Test

`DescendantsLines/tests/test_descendantslines_name.py` (new regression test file, `test_*.py` prefix per addon convention) drives `derive_output_filename` directly with four test cases: (1) current-run destination overrides stale option with no carry-over; (2) two runs with different current destinations yield different names; (3) fallback to persisted option when no current destination; (4) distinct naming from document path (clobber guard). The production report (`DescendantsLines.py:318`) and the test both call the same function (`descendantslines_output.derive_output_filename`), so the test exercises the exact code path the report runs — no parallel copy. Verified locally: RED without the helper (ModuleNotFoundError), GREEN with it (all 4 tests pass). The cross-GUI session behavior (open, run, reopen with different name, run again) cannot be automated headlessly but is described in the build notes for manual verification.

Fixes #5965
