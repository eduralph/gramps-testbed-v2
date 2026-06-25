# Build notes — issue 3068 / detdescendant-duplicate-person-number

## Disposition: verify-first (fix already in tree)

The brief is a POSSIBLY-FIXED / verify-first item. PR #100 (merge `9a516b1058`,
"bug3068", SNoiraud — fix commit `78b5fba358`) already added the
keep-the-smaller-number guard to `apply_henry_filter`. Confirmed it is an ancestor of
`maintenance/gramps61` HEAD:

- guard present at `gramps/plugins/textreport/detdescendantreport.py:239-243`
  (target branch; the file is byte-identical to `upstream/maintenance/gramps61` —
  `git diff upstream/maintenance/gramps61 -- …detdescendantreport.py` is empty).

So **there is no production change to ship** — only the missing regression test. This
is the documented C4-UNVERIFIABLE shape: a test-only patch with no non-test production
file for the red leg to revert (INTEGRATION §3 "C4 *unverifiable*"). It routes to §6
NEEDS-HUMAN under the C6 accept-guard, as the brief anticipates.

## Success criterion targeted (not a proxy)

Criterion: for the reported repro (default Henry numbering, "Omit duplicate ancestors"
unchecked) a duplicated descendant keeps the smaller/first reference number and the
"same person as" line cites it.

The "same person as" / duplicate line in `write_person` reads
`self.dnumber[person_handle]` verbatim (`detdescendantreport.py:452`, also used at
:668-672 and :744-748). So the number the report prints **is** the value
`apply_henry_filter` stores in `self.dnumber`. Asserting the filter keeps the smaller
number for the duplicated person is therefore the end result, not an adjacent proxy —
there is no transform between `dnumber[handle]` and what the reader sees.

## Why drive the real method, not a copy

The test assigns the **production** function as the probe's method:

    apply_henry_filter = DetDescendantReport.apply_henry_filter

The descriptor protocol binds it to the probe instance, and the method's own recursive
`self.apply_henry_filter(...)` calls resolve back to that same shipping code. The probe
only supplies the five attributes the method touches (`_db`, `max_generations`,
`dnumber`, `map`, `gen_keys`). No logic is re-implemented — any future drift in
`apply_henry_filter` is caught (avoids the issue-8653 "test mirrors production" trap).

Driving the method directly (rather than instantiating the full `DetDescendantReport`)
avoids the heavy report machinery (`Report.__init__`, menu/options, docgen) — that path
needs a built options menu and a doc backend, ~tens of lines of GUI-adjacent scaffolding
per report, and would pull report option plumbing into a headless unit test for no extra
coverage of the bug. The filter is the entire locus of the defect.

## Import-light / headless

`detdescendantreport.py` imports only `gramps.gen.*` and `gramps.plugins.lib.*` — no
`gi`/`gramps.gui` (checked the import block, :42-78). The test ran under plain
`python3 -m unittest` (no Xvfb/D-Bus), matching the headless C4 runner; the only output
is a benign `PyGIDeprecationWarning` from `gramps.gen.const`'s locale init, not a GUI
import.

## Test tree (reported structure: child of two first cousins)

    a (1)
    |-- b (11) --- d (111) --+
    |-- c (12) --- e (121) --+-- f   (f is the child of d & e)

DFS visits f first via d → "1111", then via e → "1211". With the guard, "1111" (first /
smaller) is kept. The unambiguous descendants' numbers are asserted too, as a sanity
anchor that the traversal/numbering itself is correct.

## Red→green proof

The C4 runner needs Docker approval unavailable in this beat, and is UNVERIFIABLE here
anyway (test-only patch). I proved the contract by hand with a timeout-guarded run:

- **Green** with the shipped guard: `Ran 1 test … OK`.
- **Red** with the guard temporarily reverted to the pre-fix unconditional
  `self.dnumber[person_handle] = pid`:
  `AssertionError: '1211' != '1111'` — the exact wrong-number symptom from the bug.
  The production file was then restored (`git checkout --`); the patch ships **no**
  production change.

## Files / POTFILES

New core `.py` files registered in `po/POTFILES.skip` (neither has translatable
strings — one is the empty package marker, the other a test):
`gramps/plugins/textreport/test/__init__.py` and `…/detdescendantreport_test.py`,
inserted in the alphabetical `plugins/textreport/test` slot
(after `plugins/test/tools_test.py`). Satisfies the gating T2-potfiles MUST.

Core test placement convention: `test/` package + `<module>_test.py` suffix
(INTEGRATION §3), matching the 28 existing core `test/` dirs.

`black` reports both files unchanged (target's commit hook will pass). Patch applies
cleanly to clean `upstream/maintenance/gramps61` (`git apply --check`: hunk offset -1,
no fuzz failure).

## Residual flagged for the human (NOT this issue's repro)

`apply_mhenry_filter` (:271) and `apply_daboville_filter` (:294) still assign `dnumber`
unconditionally and would exhibit the same last-path-wins bug for the Modified-Henry and
d'Aboville numbering modes. That is out of scope for issue 3068 (reported case is default
Henry, now fixed) but worth a follow-up. Not addressed here.
