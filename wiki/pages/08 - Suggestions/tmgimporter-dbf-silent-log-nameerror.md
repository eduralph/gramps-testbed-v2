---
title: "TMGimporter: silent LOG.error on missing dbf leaves Table undefined, causing NameError at runtime"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Surfaced by the
  Gramps Testbed v2 cross-cycle Act review (act-log 2026-06-27, issue_5965 §10); the
  NameError causes a runtime crash rather than a clean skip when dbf is absent.
  See also the general guard suggestion: [[addon-missing-dep-guard-audit]].
-->

# Addon bug — TMGimporter silently logs when `dbf` is absent, leaving `Table` undefined

> **Repo:** addons-source · **Category:** Plugin loading / Error handling · **Severity:** bug

**Summary:** When the `dbf` pip package is absent, `TMGimporter` catches the
`ImportError`, emits a `LOG.error`, and continues — leaving the name `Table` undefined.
Any subsequent code path that references `Table` raises a `NameError`, crashing at
runtime rather than producing a clean diagnostic skip.

**Description:**

`TMGimporter` depends on the `dbf` package. Its top-level import guard catches the
`ImportError` and logs it silently:

```python
try:
    from dbf import Table
except ImportError:
    LOG.error("dbf not installed")
    # Table is now undefined
```

When `dbf` is not installed (as in the gramps60 matrix leg of the Gramps Testbed),
`Table` is left as an unbound name in the module's namespace. The first code path that
uses `Table` raises `NameError: name 'Table' is not defined`, which is harder to
diagnose than an `ImportError` and does not produce a clean test skip.

The correct approach is one of:
- Re-raise the `ImportError` immediately so pytest skips the test module at
  collection time.
- Set a sentinel (`_DBF_AVAILABLE = False`) and call `self.skipTest()` in `setUp()`.

Observed in T3-addon-unit-60 results for bundle issue_5965 (T3-60 description),
unrelated to the patch under review.

**Proposed fix:**

```python
try:
    from dbf import Table
    _DBF_AVAILABLE = True
except ImportError:
    _DBF_AVAILABLE = False
    Table = None  # prevent NameError; actual guard is in setUp / at call sites

# Then in any test class:
class TMGImportTests(unittest.TestCase):
    def setUp(self):
        if not _DBF_AVAILABLE:
            self.skipTest("dbf not installed; pip install dbf")
```

Or, if the guard is at the plugin level (not just tests), re-raise as `ImportError`:

```python
try:
    from dbf import Table
except ImportError as e:
    raise ImportError("TMGimporter requires dbf: pip install dbf") from e
```

**Additional information:**

- Part of a broader pattern across addons-source; see [[addon-missing-dep-guard-audit]]
  for a full audit recommendation.
- Identified in cross-cycle Act review: act-log 2026-06-27 (issue_5965 §10).
