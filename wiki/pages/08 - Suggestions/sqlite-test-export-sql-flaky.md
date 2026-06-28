---
title: "Sqlite addon: test_export_sql is flaky due to hardcoded /tmp paths and missing tearDown"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Filed as a bug
  report against the addons-source repository: eduralph/addons-source #56
  (https://github.com/eduralph/addons-source/issues/56). Surfaced by the Gramps
  Testbed v2 cross-cycle Act review (act-log 2026-06-27); the test ID has appeared as
  a recurring T3 delta across 7+ bundles with no causal link to any patch under review.
-->

# Addon bug — `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sql` is flaky

> **Repo:** addons-source · **Category:** Tests · **Severity:** bug ·
> **Tracker:** eduralph/addons-source #56

**Summary:** `test_export_sql` uses hardcoded `/tmp` paths and does no `tearDown`
cleanup, making the test order-dependent and intermittently failing in CI.

**Description:**

`Sqlite/tests/test_sqlite.py` `ExportSQLTestCase::test_export_sql` fails
non-deterministically. The root cause is two interacting issues:

1. **Hardcoded `/tmp` paths.** The test writes to a fixed location under `/tmp` rather
   than a process-unique temporary directory. If a previous run (or a parallel run) left
   residual state at that path, the next run may read stale data, hit a collision, or
   encounter a permissions conflict.

2. **No `tearDown` cleanup.** There is no `tearDown` (or `addCleanup`) that removes
   the temporary file after each test method. State leaks between test methods within
   the class, and between successive test runs in the same process.

The test has been observed failing across 7+ Gramps Testbed bundles — all against
patches that touch no SQLite code — confirming the failure is environmental rather than
patch-induced:
- issue_10415, issue_10628, issue_5516, issue_5965, issue_6793, issue_7344, issue_7832

**Proposed fix:**

Replace hardcoded `/tmp` paths with `tempfile.mkdtemp()` (or
`tempfile.TemporaryDirectory` as a context manager) to obtain a unique, isolated
directory for each test run:

```python
import tempfile, shutil

class ExportSQLTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_export_sql(self):
        outfile = os.path.join(self.tmpdir, "export.sql")
        # … rest of test …
```

**Short-term mitigation (testbed):**

Add the test ID to `known_failures` in both
`engine/baselines/run-addon-unit-60.json` and `engine/baselines/run-addon-unit-61.json`
via `make preflight` (t3_baseline `--update`) so it stops surfacing as a T3 NEEDS-HUMAN
delta in every bundle. Remove the baseline entry once the test is fixed.

**Additional information:**

- Tracker issue: https://github.com/eduralph/addons-source/issues/56
- Identified in cross-cycle Act review: act-log 2026-06-27.
