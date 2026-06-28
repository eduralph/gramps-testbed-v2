---
title: "LifeLineChartView: raise ImportError (not bare Exception) when life_line_chart pip package is absent"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Filed as a bug
  report against the addons-source repository: eduralph/addons-source #57
  (https://github.com/eduralph/addons-source/issues/57). Surfaced by the Gramps
  Testbed v2 cross-cycle Act review (act-log 2026-06-27); the collection crash has
  appeared as a recurring T3 delta across 3+ bundles (gramps60 leg) with no causal
  link to any patch under review.
-->

# Addon bug — LifeLineChartView raises bare `Exception` on missing dep, crashing pytest collection

> **Repo:** addons-source · **Category:** Tests / Plugin loading · **Severity:** bug ·
> **Tracker:** eduralph/addons-source #57

**Summary:** When the `life_line_chart` pip package is absent, `lifelinechart.py`
raises a bare `Exception` rather than an `ImportError`. Pytest's collection guard only
catches `ImportError`, so the bare `Exception` propagates as a collection crash instead
of a clean skip — appearing as `LifeLineChartView.collection::import_or_collection` in
T3 addon-unit results.

**Description:**

Gramps addons that depend on third-party pip packages typically guard their top-level
import with a try/except block. The correct pattern re-raises the failure as
`ImportError` (or calls `self.skipTest()`) so that test runners and plugin loaders can
handle the missing dependency cleanly.

`LifeLineChartView/lifelinechart.py` at approximately line 75 raises a bare
`Exception(...)` when the `life_line_chart` package is not importable. Pytest's
collection infrastructure only catches `ImportError` at the module level; a bare
`Exception` bypasses that guard and is recorded as a collection-phase error rather than
a skipped module.

The result is that every test run against gramps60 (where `life_line_chart` is not
installed) shows a collection crash under `LifeLineChartView.collection`, which the
Gramps Testbed records as a new T3 delta requiring human triage. The crash has been
observed in bundles issue_5965, issue_6988, and issue_7832, in each case unrelated to
any patch under review.

**Proposed fix:**

At the missing-dependency guard in `lifelinechart.py`:

```python
# Before:
raise Exception("The life_line_chart package is required …")

# After:
raise ImportError("The life_line_chart package is required …")
```

Alternatively, wrap the module-level import in a try/except and set a sentinel, then
call `self.skipTest(…)` in `setUp()`:

```python
try:
    import life_line_chart
    _LIFE_LINE_CHART_AVAILABLE = True
except ImportError:
    _LIFE_LINE_CHART_AVAILABLE = False

class LifeLineChartTests(unittest.TestCase):
    def setUp(self):
        if not _LIFE_LINE_CHART_AVAILABLE:
            self.skipTest("life_line_chart not installed")
```

The same pattern applies to any other addon that currently uses a bare `Exception` at
module level to signal a missing dependency — the `Exception` must be `ImportError` (or
handled before collection).

**Additional information:**

- Tracker issue: https://github.com/eduralph/addons-source/issues/57
- Part of a broader pattern across addons-source; see [[addon-missing-dep-guard-audit]]
  for a full audit recommendation covering LifeLineChartView, PDFForms, and TMGimporter.
- Related specific instances: [[pdfforms-missing-reportlab-collection-crash]],
  [[tmgimporter-dbf-silent-log-nameerror]].
- Identified in cross-cycle Act review: act-log 2026-06-27.
