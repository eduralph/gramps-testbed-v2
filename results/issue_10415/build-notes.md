# Build notes — issue 10415 / familylines-graph-prunes-direct-ancestors

## Root cause (confirmed against source)

`gramps/plugins/graph/gvfamilylines.py` HEAD `b679c084f6`,
`FamilyLinesReport.remove_uninteresting_parents` (target-branch lines 664–822).
The method walks every person currently selected and keeps them only if one of a
fixed set of heuristics fires. The relevant keep-tests were:

- has >1 child of interest / >1 spouse of interest (lines 746–752)
- has a kept parent, or a spouse with a kept parent (lines 756–762)
- is, or is married to, a person of interest (lines 765–770)
- **surname (or spouse surname) string-equals a person of interest** (772–791)
- has a surname colour (795–801)

Otherwise the person is removed (lines 804–806).

After `find_parents()` (lines 590–662), every handle in `self._people` is a
direct-line ancestor of a person of interest: the only handles ever queued are
the `father`/`mother` of an already-queued person (lines 647–662), and the parent
of an ancestor is itself an ancestor. So the *only* candidates this pruning ever
sees are direct ancestors. A top-of-tree ancestor (no further kept parents, single
child of interest, not a person of interest) is kept *only* by the surname-equality
test — so when the surname spelling drifts up the direct line (reporter's case:
same name, different spelling), that legitimate bloodline ancestor is dropped.
There was no lineage-based "this is a direct ancestor" criterion independent of
surname text. That is the bug.

## Fix

Add a keep criterion decided purely by lineage. New method `_direct_ancestors()`
computes the transitive closure of parent links from the interest set (cached),
and `remove_uninteresting_parents` now keeps any person whose handle is in that
set, *before* the surname heuristic:

```
if person.get_handle() in self._direct_ancestors():
    continue
```

Membership is decided by parent links, never by surname string — so surname
spelling drift no longer prunes the direct line. This restores the correctness
requirement in the brief ("a direct-line ancestor included by 'follow parents' is
not removed by the extra-people pruning; ancestor membership is decided by
lineage, not surname-string equality").

The pre-existing heuristics are left untouched (minimal change): they still apply
to any non-ancestor a future code path might place in the set; the new criterion
is purely additive.

## Testable seam (brief: "invert the GUI-entangled report into a drivable unit")

The selection methods (`find_parents`, `remove_uninteresting_parents`,
`find_children`) depend only on the database and the option flags — never on
`self.doc`, the menu, or the `Report` base — but they lived on `FamilyLinesReport`,
whose constructor needs the full GUI/report/menu machinery, so they could not be
driven in isolation.

I extracted them verbatim into a new GUI-free class `FamilyLinesSelection` in the
same module, plus a thin `__init__` (db + flags), a `select()` that reproduces
`begin_report`'s exact ordering, and `deleted_people` / `deleted_families`
accessors. `FamilyLinesReport.begin_report` now constructs a `FamilyLinesSelection`,
calls `select()`, and copies the four results back onto `self`
(`self._people`, `self._families`, `self._deleted_people`, `self._deleted_families`)
— so **production routes through the extracted unit**; the report and the test
drive the identical implementation (no parallel copy). The method bodies are moved
unchanged except for the one added keep-check + the new `_direct_ancestors` helper.

No new production `.py` file is added (the class lives in the existing
`gvfamilylines.py`, already in `po/POTFILES.in:700`), so only the new test file is
registered, in `po/POTFILES.skip` (it has no translatable strings).

## Test

`gramps/plugins/graph/test/gvfamilylines_test.py` (new). Builds a real in-memory
db via `import_as_dict` from an inline four-generation fixture whose paternal
surname drifts every generation (Smith → Smithe → Smyth) with a married-in spouse
each generation. It drives the production `FamilyLinesSelection.find_parents()` +
`remove_uninteresting_parents()` and asserts every direct-line ancestor — notably
I0005 "Smyth", the drifted top-of-line great-grandfather, and I0006 "White" — is
retained, and `deleted_people == 0`.

Import-light: `gvfamilylines` imports only `gramps.gen.*` (no `gramps.gui`); the
existing `year_only_date_test.py` already imports it and runs in the headless core
suite, so the new test runs headless too.

## Verification

- C4 (`run-verify.sh`, lane0, clean `upstream/maintenance/gramps61`):
  `green-with-fix=PASS / red-without-fix=PASS`.
- The C4 red reverts the *whole* production change, so the bare red is an
  `ImportError` (the extracted class is gone). To prove the test is a genuine
  **behavioural** guard and not merely an import check, I applied the patch to a
  clean lane and removed *only* the 8-line keep-check (class kept): the test then
  fails with `AssertionError: 'p3' not found ... direct-line ancestor I0003 was
  pruned` — i.e. it catches the actual pruning regression, not just the missing
  symbol.
- `black --check` clean on both `gvfamilylines.py` (unchanged result) and the new
  test (local black 26.5.0).

## Alternatives considered

- **Test via `FamilyLinesReport.__new__` + manually set attributes** (no
  extraction): ~15 production lines instead of relocating ~280, and it would drive
  the real methods too. Rejected because the brief explicitly directs inverting the
  report "into a drivable unit", and bypassing `__init__` couples the test to the
  exact private attribute set without giving production a clean seam. The extraction
  is the intended design; the relocation is mechanical (method bodies unchanged).
- **Fuzzy surname-variant matching** (keep an ancestor whose surname is a spelling
  variant): rejected — unreliable and explicitly contradicted by the brief, which
  requires lineage-based membership ("decided by lineage, not surname-string
  equality").

## Worktree note (harness)

`$PDCA_WORKTREE` was unset; edits were made in the C4 target worktree
`/home/eddie/workspace/gramps-6.1`. That shared worktree was concurrently dirtied
by another bundle (gramplet/surnames files). I generated `patch.diff` containing
**only** my three files (the `po/POTFILES.skip` hunk was hand-built against clean
`HEAD` to exclude the other bundle's entries — verified `git apply --check` clean
on lanes 1 and 2), then reverted my edits from the shared worktree, leaving the
other bundle's changes intact. C4 ran against clean lane worktrees.
