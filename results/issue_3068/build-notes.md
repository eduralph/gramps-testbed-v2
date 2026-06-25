# Build notes — issue 3068 / detdescendant-duplicate-person-number

## Disposition: verify-first (fix already merged). Iteration 2.

PR #100 (merge `9a516b1`, "bug3068", SNoiraud) already added the
keep-the-smaller-number guard to `apply_henry_filter`. It is present on the
target branch:

- `gramps/plugins/textreport/detdescendantreport.py:239-243`
  (gramps-6.1 worktree = maintenance/gramps61) —

  ```
  239  if person_handle in self.dnumber:
  240      if self.dnumber[person_handle] > pid:
  241          self.dnumber[person_handle] = pid
  242  else:
  243      self.dnumber[person_handle] = pid
  ```

There is **no production change to ship** — only the missing regression test.

## Why iteration 1 hard-failed C4 (the carry-forward) — root cause

Iteration 1 shipped a **new** test module plus the two files a new core `.py`
drags in: `gramps/plugins/textreport/test/__init__.py` and a `po/POTFILES.skip`
registration. `run-verify.sh` classifies every patched non-`*_test.py` file as a
*production* file to revert for the red leg (run-verify.sh:142-154). So it saw
`PROD = {__init__.py, POTFILES.skip}` — non-empty — and therefore did **not**
take the test-only `PDCA-UNVERIFIABLE` exit-77 branch (run-verify.sh:162).
Instead it ran the real red→green mechanic:

- green leg (patch applied): test PASSES — the guard is in the tree.
- red leg: it reverts `POTFILES.skip` and removes `__init__.py` — **but the
  actual guard lives in `detdescendantreport.py`, which the patch never touched**,
  so it stays in the tree. The test still PASSES → `red=0` → the
  `green && !red` contract fails → C4 hard fail. The essential-line retry hits
  the identical state and fails identically ("a real failure, not a missing
  prerequisite").

A removed `__init__.py` does **not** make the test fail to import either:
`gramps.plugins.textreport` is a regular package, so `test/` resolves as a
namespace-package portion and the module imports fine without the marker —
confirmed empirically. So there was no accidental red to rescue the contract.

Conclusion: for an **already-merged** fix the red leg can never go red unless the
patch itself carries the production change to revert — which is impossible here
(the guard's lines already exist on maintenance/gramps61; a patch re-adding them
would not even `git apply`). The only correct automated outcome is the
`PDCA-UNVERIFIABLE` exit-77 → §6 NEEDS-HUMAN that the brief anticipates. The job
was therefore to make run-verify.sh actually *reach* exit-77.

## The fix: ship the regression as a modification of an existing registered test

exit-77 fires iff the patch's only files are `*_test.py` (run-verify.sh:161-162).
The conflict iteration 1 hit is structural between two **gating** gates:

| patch shape | C4-verify | T2-potfiles |
|---|---|---|
| new file + `__init__.py` + `POTFILES.skip` (iter 1) | **FAIL** — PROD non-empty, runs mechanic, red leg green | pass |
| new file only (drop `POTFILES.skip`) | exit-77 ✓ | **FAIL** — new unregistered `.py` (t2_potfiles.py:122-128) |
| **modify an existing registered `*_test.py` (this patch)** | **exit-77 ✓** — PROD empty | **pass** ✓ — no new `.py`, no POTFILES change |

So I add the 3068 regression to the existing
`gramps/plugins/test/reports_test.py` instead of a new module:

- patch.diff: a single modified file, `gramps/plugins/test/reports_test.py`
  (+116 lines) — imports + `_HenryProbe` + `TestDetDescendantDuplicateNumber`.
- It is already listed in `po/POTFILES.skip` and already lives in a package with
  `__init__.py`, so **no** `__init__.py` and **no** `POTFILES.skip` change is
  needed → `PROD = {}` → `run-verify.sh` emits `PDCA-UNVERIFIABLE` and exits 77
  *before* any container starts (verified by replaying the script's
  classification: one `+++ b/…reports_test.py`, zero `--- /dev/null`, so
  `TEST_REL` set and `PROD` empty).

This is also the codebase's **established home for report regressions**:
`reports_test.py` already carries a Mantis regression added the same way —
`test_hourglass_graph_includes_spouse_mantis_9628`
(gramps/plugins/test/reports_test.py:143 on the target). So this is not an
ad-hoc dumping ground; it is the conventional location.

### Deviation from the brief's named path — flagged for the human

The brief names a **new** file
`gramps/plugins/textreport/test/detdescendantreport_test.py`. That path provably
cannot pass the automated gates (row 1/2 of the table above), which is the exact
gate the carry-forward requires green. Changing the test's host file is "fix the
test so C4 goes green" per the carry-forward, not a scope change. A runnable,
self-contained copy of the regression is kept in the bundle as
`detdescendantreport_test.py` (a record artifact; its header points back to
`reports_test.py`).

## Success criterion targeted (not a proxy)

Criterion: a duplicated descendant keeps the smaller/first reference number and
the "same person as" line cites it. The duplicate line in `write_person` prints
`self.dnumber[person_handle]` verbatim (detdescendantreport.py:452, also
:668-672, :744-748) — there is **no transform** between the value the filter
stores and what the reader prints. Asserting the filter keeps the smaller number
for the duplicated person is therefore the end result itself.

## The test exercises production, not a copy

`_HenryProbe.apply_henry_filter = DetDescendantReport.apply_henry_filter`
binds the **production** method to the probe via the descriptor protocol; its
recursive `self.apply_henry_filter(...)` calls resolve back to the same shipping
code. The probe supplies only the five attributes the method reads
(`_db`, `max_generations`, `dnumber`, `map`, `gen_keys`). No logic is
re-implemented, so future drift in `apply_henry_filter` is caught (avoids the
issue-8653 "test mirrors production" trap). Driving the method directly (rather
than building a full `DetDescendantReport` with its options menu + docgen
backend, ~tens of lines of report scaffolding) keeps the unit headless and
import-light — `detdescendantreport.py` imports only `gramps.gen.*` /
`gramps.plugins.lib.*` (no `gi`/`gramps.gui`; checked the import block,
:42-78).

## Red→green proof (manual; C4 is UNVERIFIABLE by construction)

Run against the target code with the production guard in place / reverted, via
the same production method the patch's test drives:

- **green** (guard present): `Ran 1 test … OK`.
- **red** (guard reverted to the pre-fix unconditional
  `self.dnumber[person_handle] = pid`):
  `AssertionError: '1211' != '1111'` — the exact wrong-number symptom of bug
  3068 (the duplicate kept the LAST path's number). The production file was then
  restored; the patch ships **no** production change (`git diff` of
  `detdescendantreport.py` is empty).

The tree used (reported structure — child of two first cousins):

    a (1)
    |-- b (11) --- d (111) --+
    |-- c (12) --- e (121) --+-- f   (f is the child of d & e)

DFS reaches f first via d → "1111", then via e → "1211"; the guard keeps "1111".

## Conformance / commit-readiness

- `black gramps/plugins/test/reports_test.py` → "1 file left unchanged"
  (commit hook will pass).
- `git apply --check` of patch.diff against the clean gramps-6.1
  (maintenance/gramps61) worktree: EXIT 0, no fuzz.
- No new/removed `.py` → T2-potfiles N/A-clean (no registration owed).
- Existing GPL header on the touched file is unchanged; the added code has no
  `print()`.

## Residual flagged for the human (NOT this issue's repro)

`apply_mhenry_filter` (detdescendantreport.py:271) and `apply_daboville_filter`
(:294) still assign `dnumber` **unconditionally** and would exhibit the same
last-path-wins wrong-number bug for the Modified-Henry and d'Aboville numbering
modes. That is out of scope for issue 3068 (reported case is default Henry, now
fixed) but is worth a follow-up.
