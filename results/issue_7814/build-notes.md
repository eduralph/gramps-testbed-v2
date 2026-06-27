# Build notes — issue 7814 (detdescendant-death-line-for-living)

## Disposition: no-fix close — `not-reproducible` (already fixed on maintenance/gramps61)

The brief is a **verify-first** bundle ("POSSIBLY-FIXED → verify first"). I verified
the defect against the target branch and it **does not reproduce**: the
`probably_alive` guard the brief points at is present and load-bearing. The Success
criterion ("a probably-alive person with no death event produces NO 'Died …' line")
already holds, so per the brief the disposition is a no-fix close and the regression
test is the recorded deliverable.

## What I verified (root cause of the original report, and why it no longer fires)

Mantis 7814 (Gramps 4.0.3): the Detailed Descendant Report printed
`Died ______ in ______.` for a living person with no death event. The narrator
emits those empty-entry placeholders whenever the "replace missing dates/places"
options are on (`EMPTY_ENTRY = "_____________"`,
`gramps/plugins/textreport/detdescendantreport.py:85`). The report used to call the
narrator's death/burial routines unconditionally.

On `maintenance/gramps61` (worktree `gramps-6.1` @ `b679c084f6`), every death/burial
emission is now gated by `if not probably_alive(...)`:

- `gramps/plugins/textreport/detdescendantreport.py:54` — imports `probably_alive`.
- `detdescendantreport.py:902-909` — `write_person_info`: the guard wraps
  `get_died_string` / `get_buried_string`. This is the main-person site the reporter
  saw (and the site reached for spouses, since `__write_mate` →
  `write_person_info`, `detdescendantreport.py:665,677`).
- `detdescendantreport.py:769-773` — `__write_children`: the same guard wraps the
  child-list death/burial text.

There is no third, unguarded emission: `grep -n 'get_died_string\|get_buried_string\|
probably_alive'` returns only lines 54, 769-772, 902-907.

## Red→green evidence (the test exercises the SHIPPED guard, not a copy)

The recorded regression test `detdescendantreport_test.py` drives the **real**
production routines `DetDescendantReport.write_person_info` and
`DetDescendantReport.__write_children` (via `DetDescendantReport.__new__` + injecting
the collaborators those methods touch — a real `Narrator`, the real name displayer,
an in-memory SQLite db, and a recording doc). It is import-light (only `gramps.gen.*`
and `gramps.plugins.lib.libnarrate` / `…textreport.detdescendantreport`, none of which
import `gi`/`gramps.gui`), so it runs under the headless C4 runner.

I confirmed it discriminates on the guard, using the engine image
`gramps-testbed:ubuntu-6.1.0` (wrapped in `timeout`, since the test is in-memory and
sub-second):

- **Green** on the unmodified tree — all 4 tests pass (`Ran 4 tests … OK`).
- **Red** when I neutralised both guards (`if not probably_alive(person…)` /
  `(child…)` → `if True:`): the two "living" tests fail with exactly the 7814
  symptom —
  `AssertionError: 'Died _____________ in _____________.' unexpectedly found in
  'Born 1990 in _____________.  Died _____________ in _____________. '`
  (and the same for the living child). The two "deceased" cases stay green, so the
  guard is not over-broad.

So the test would catch any future removal of either guard. (This was a builder
self-check; the harness's C4-verify gate is N/A for a close bundle — see below.)

## Why no patch.diff (and why the test is a recorded artifact, not a tree change)

The bug is already fixed, so there is **no production change to ship**. The brief's
"Invariant to restore" is n/a and the scope is "verify (and, only if it still
reproduces, remove)". It still does not reproduce → nothing to remove.

I considered contributing the regression test to the tree as a normal patch, and
rejected it because the harness gates make it infeasible for an already-fixed bug —
this is a concrete mechanical conflict, not a preference:

- A patch adding `gramps/plugins/textreport/test/detdescendantreport_test.py` (+ the
  package `__init__.py`) **must** register both new `.py` files in
  `po/POTFILES.skip` (doc 16; `engine/conformance/t2_potfiles.py:123-128` fails the
  T2 gate otherwise).
- But with `po/POTFILES.skip` in the patch, `run-verify.sh` classifies it as a
  production file (it is not `*_test.py`), so `PROD=["po/POTFILES.skip"]` is
  non-empty → C4 does **not** take its test-only "unverifiable" branch
  (`run-verify.sh` `[ "${#PROD[@]}" -gt 0 ]` guard). It runs red/green, reverts
  `POTFILES.skip` for the red leg, the test stays green (POTFILES has no runtime
  effect), so `red-without-fix=FAIL` → C4 reports a hard **FAIL** — a false signal
  that the test does not catch the bug.
- Dropping `POTFILES.skip` to get the test-only/unverifiable branch instead trips
  the T2 MUST gate.

A no-fix close sidesteps both: no `patch.diff` ⇒ the close marker is the Do artifact
(`state.py:31-34,52-54`) and Check writes the all-N/A close matrix without running a
gate (`gates.py:67-75`). The regression test ships as a recorded bundle artifact
(per the "record all bundle artifacts" rule), available to drop into the tree the day
upstream wants a regression guard for this routine.

## Files in this bundle

- `close-disposition` → `not-reproducible` (already-fixed; the canonical close token
  matching "the defect does not reproduce on the target branch").
- `detdescendantreport_test.py` — the regression guard, proven red→green above,
  black-clean (`black --check` passes; gramps default config).
- No `patch.diff` / `commit-msg` / `pr-description` (no-fix close).

## Citations (target: gramps-project/gramps @ maintenance/gramps61, worktree b679c084f6)

- `gramps/plugins/textreport/detdescendantreport.py:54` — `probably_alive` import.
- `gramps/plugins/textreport/detdescendantreport.py:768-773` — guarded child death/burial.
- `gramps/plugins/textreport/detdescendantreport.py:901-909` — guarded person death/burial.
- `gramps/plugins/textreport/detdescendantreport.py:85` — `EMPTY_ENTRY` placeholder.
- `gramps/plugins/textreport/detdescendantreport.py:665,677` — `__write_mate` →
  `write_person_info` (spouses reach the same guard).
