# Regression test for duplicate descendant numbering (issue 3068)

## Root cause

When a descendant is reachable through multiple descent paths in the Detailed Descendant Report (e.g. the child of two first cousins), the Henry-numbering filter in `gramps/plugins/textreport/detdescendantreport.py:apply_henry_filter` was assigning the `dnumber` mapping unconditionally on each visit, causing it to overwrite with the number from the last path visited. The `write_person` method (line 453) retrieves and prints this value verbatim, so the wrong number appeared in the "is the same person as [N]" reference line.

## Fix

PR #100 (merge commit 9a516b1058, "Merge pull request #100 from SNoiraud/bug3068") added a guard to `apply_henry_filter` at lines 239–243:

```python
if person_handle in self.dnumber:
    if self.dnumber[person_handle] > pid:
        self.dnumber[person_handle] = pid
else:
    self.dnumber[person_handle] = pid
```

This keeps the first/smaller reference number for duplicate descendants. The production fix is present on the target branch; this patch adds a regression test to verify it.

The test is added to `gramps/plugins/test/reports_test.py` (the established home for report-level regressions, already carrying `test_hourglass_graph_includes_spouse_mantis_9628` at line 143). The patch introduces a minimal `_HenryProbe` class that binds the real `DetDescendantReport.apply_henry_filter` method and exercises it on an in-memory tree with the reported structure (child of two first cousins). This avoids re-implementing the filter's logic and ensures the test always exercises the real production code.

## Verified against

Target branch: `gramps-project/gramps @ maintenance/gramps61`

- `gramps/plugins/textreport/detdescendantreport.py:235–250` — the `apply_henry_filter` method with the guard at lines 239–243
- `gramps/plugins/test/reports_test.py` — existing test module where the regression is added (imports verified against lines 25–27)

## Test

The regression test `TestDetDescendantDuplicateNumber.test_duplicate_descendant_keeps_smaller_number` (added at lines 110–129):

1. Builds a minimal in-memory Gramps tree with the reported structure: person a → persons b and c → persons d and e (first cousins) → person f (child of d and e)
2. Calls `apply_henry_filter` on person a as root with Henry numbering
3. Asserts that the duplicate descendant f retains the first/smaller Henry number ("1111" via d, not "1211" via e)
4. Asserts the unambiguous descendants get their expected numbers (a="1", b="11", c="12", d="111", e="121")

The test fails with the bug reverted (guard replaced by unconditional `self.dnumber[person_handle] = pid`), producing the exact wrong-number symptom: `AssertionError: '1211' != '1111'`.

Fixes #3068
