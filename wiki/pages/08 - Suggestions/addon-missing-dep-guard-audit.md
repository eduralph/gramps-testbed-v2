---
title: "Audit all addons: missing-dep guards must raise ImportError or SkipTest, not bare Exception or silent LOG.error"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Surfaced by the
  Gramps Testbed v2 cross-cycle Act review (act-log 2026-06-27, issue_5965 §10).
  This is the general pattern; specific instances have their own pages:
  [[lifelinechart-missing-dep-collection-crash]],
  [[pdfforms-missing-reportlab-collection-crash]],
  [[tmgimporter-dbf-silent-log-nameerror]].
-->

# Suggestion — Audit addon missing-dep guards: require `ImportError` or `SkipTest`

> **Repo:** addons-source · **Category:** Tests / Plugin loading · **Severity:** enhancement

**Summary:** Several addons handle a missing pip dependency with a bare `Exception` or
a silent `LOG.error`, causing pytest collection crashes or `NameError` at runtime.
Every addon that depends on an optional pip package should re-raise as `ImportError`
(collection-time skip) or use a sentinel + `self.skipTest()` (test-time skip). A
one-off audit against all addons that declare `requires_mod` entries is needed to close
this systematically.

**Description:**

When a pip-dependent addon is imported in a test environment that lacks the required
package, three problematic patterns have been observed:

| Pattern | Addon | Symptom |
|---------|-------|---------|
| `raise Exception("…pkg required…")` | LifeLineChartView | pytest collection crash (`collection::import_or_collection`) |
| Silent `LOG.error`; name left undefined | TMGimporter | `NameError` at first use of `Table` |
| Unguarded module-level code | PDFForms | pytest collection crash (`"The reportlab package is required"`) |

All three manifest as unexplained T3 delta noise in the Gramps Testbed, each requiring
a human to triage and clear the §6 NEEDS-HUMAN flag even though the failure is
environmental and unrelated to any patch under review.

**The correct patterns:**

*Collection-time skip* — re-raise as `ImportError` so pytest skips the module before
collecting any tests:

```python
try:
    import some_package
except ImportError as e:
    raise ImportError("MyAddon requires some_package: pip install some_package") from e
```

*Test-time skip* — set a sentinel at module level; call `self.skipTest()` in `setUp()`:

```python
try:
    import some_package
    _PKG_AVAILABLE = True
except ImportError:
    _PKG_AVAILABLE = False

class MyAddonTests(unittest.TestCase):
    def setUp(self):
        if not _PKG_AVAILABLE:
            self.skipTest("some_package not installed")
```

The silent-`LOG.error` + undefined-name pattern (TMGimporter) is never acceptable: it
hides the problem and causes a confusing `NameError` later.

**Proposed audit scope:**

1. Identify all addons that declare a `requires_mod` (or equivalent) entry listing a
   pip package.
2. For each, inspect the top-level module for how a missing import is handled.
3. Where the pattern is `raise Exception(…)`, `LOG.error(…)` without re-raise, or an
   unguarded module-level call that errors on import — replace with one of the correct
   patterns above.

Known instances (specific suggestion pages):
- [[lifelinechart-missing-dep-collection-crash]] — LifeLineChartView, `life_line_chart`
- [[pdfforms-missing-reportlab-collection-crash]] — PDFForms, `reportlab`
- [[tmgimporter-dbf-silent-log-nameerror]] — TMGimporter, `dbf`

**Additional information:**

- Identified in cross-cycle Act review: act-log 2026-06-27 (issue_5965 §10).
- Once fixed, the per-addon collection crashes can be removed from the Gramps Testbed's
  `run-addon-unit-{60,61}.json` baseline known_failures / run_level_signatures.
