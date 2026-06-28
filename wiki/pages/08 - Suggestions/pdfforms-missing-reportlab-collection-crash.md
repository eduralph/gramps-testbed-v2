---
title: "PDFForms: collection crash when reportlab is absent — should skip cleanly"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Surfaced by the
  Gramps Testbed v2 cross-cycle Act review (act-log 2026-06-27); the collection crash
  appears in T3-addon-unit-61 results and has surfaced as a recurring T3 delta with no
  causal link to any patch under review. See also the general guard suggestion:
  [[addon-missing-dep-guard-audit]].
-->

# Addon bug — PDFForms crashes pytest collection when `reportlab` is absent

> **Repo:** addons-source · **Category:** Tests / Plugin loading · **Severity:** bug

**Summary:** When the `reportlab` pip package is absent, the `PDFForms` addon raises
an unguarded error during pytest collection (`"The reportlab package is required"`),
crashing the collection phase instead of producing a clean skip.

**Description:**

The `PDFForms` addon depends on the `reportlab` package. When `reportlab` is not
installed in the test environment (as is the case in the gramps61 matrix leg of the
Gramps Testbed), the addon's module-level code raises an error that is not caught as
an `ImportError` by pytest's collection infrastructure. The result is a collection-phase
crash recorded as a new T3 delta every cycle.

This was observed in T3-addon-unit-61 results for bundle issue_7832, unrelated to the
patch under review.

**Proposed fix:**

Guard the `reportlab` import at module level and re-raise as `ImportError` (so pytest
skips the module cleanly at collection time), or set a sentinel and call
`self.skipTest("reportlab not installed")` in `setUp()`. See
[[addon-missing-dep-guard-audit]] for the general pattern and examples.

```python
try:
    import reportlab
except ImportError as e:
    raise ImportError("PDFForms requires reportlab: pip install reportlab") from e
```

**Short-term mitigation (testbed):**

Add the PDFForms collection-crash ID to `run_level_signatures` in
`engine/baselines/run-addon-unit-61.json` via `make preflight` so it stops surfacing
as a T3 NEEDS-HUMAN delta. Remove the baseline entry once the addon is fixed.

**Additional information:**

- Part of a broader pattern across addons-source; see [[addon-missing-dep-guard-audit]]
  for a full audit recommendation.
- Identified in cross-cycle Act review: act-log 2026-06-27 (issue_7832 §10).
