# Build notes — 820-pluginloading-gate (iteration 2)

## Success criterion (restated)
`TestPluginLoading.test_load_all_addon_modules` must either **gate** on
non-dependency `hard_failures` or declare itself advisory — the always-pass-by-
omission state must be removed, proven with a synthetic non-dep load failure.

## Disposition chosen: GATE (not documented-advisory)
The brief permits either contract; the carry-forward asked to "confirm gate is
intended." It is. The two sibling smoke tests in the same file already
`self.fail` on their findings (feature-branch
`tests/test_plugin_registration.py:257-261` import smoke, `:289-293` export
smoke). Making the load test advisory would leave the file with two
contradictory contracts for "an addon won't load." The brief's **Invariant**
("a CI test that names a failure class gates on it") is served by the load test
*gating*, consistent with its siblings. So the load test now gates.

## Root cause
On the PR branch, `test_load_all_addon_modules` accumulated `hard_failures` and
only `LOG.warning`-ed them (feature-branch `tests/test_plugin_registration.py:224-229`).
Its sole assertion was `assertGreater(len(plugins), 0)` (`:166`). Any genuine
non-dependency load failure therefore passed silently — an always-pass gate.

## The fix (one logical change, three files)
1. **`tests/plugin_load_gate.py`** (new): `hard_load_failure_message(hard_failures)`
   returns the gating message, or `None` when there are none. Import-light (no
   `gi` / `gramps.gui`), so the decision has one implementation shared by
   production and test.
2. **`tests/test_plugin_registration.py`** (modified): the
   `if hard_failures: LOG.warning(...)` block (`:224-229`) becomes
   ```python
   gating_message = hard_load_failure_message(hard_failures)
   if gating_message:
       self.fail(gating_message)
   ```
   plus a docstring stating the gate contract. `dep_skips` / `crash_failures`
   stay advisory warnings; the subprocess crash isolation and dependency-skip
   classification are untouched (the brief keeps them).
3. **`tests/test_plugin_load_gate.py`** (new): `TestPluginLoadingGate` — the
   regression test, driving the **real production method** (see C2 below).

## Addressing the iteration-1 carry-forward

### C2 — the substantive miss: drive the production path, not just the helper
Iteration 1 only called `hard_load_failure_message([...])` in isolation, so the
red leg came from a missing import and never exercised the silent-pass defect.

Now `TestPluginLoadingGate._run_load_test_with` constructs a real
`TestPluginLoading` instance and calls the **actual production method**
`test_load_all_addon_modules()`, injecting one synthetic always-failing addon at
the production module's own load seams (`mock.patch.object` on `prod._get_addon_plugins`,
`prod._check_dependencies`, `prod.subprocess.run`). It asserts the method raises
its `failureException`, so the `if gating_message: self.fail(...)` wiring is
exercised end-to-end on the real code path — not a copy, not just the helper.

**Negative control — proves the test goes red on the silent-pass, not on import.**
With `tests/plugin_load_gate.py` *present* but the production wiring reverted to
the original `LOG.warning`, running only `TestPluginLoadingGate` in the addon
docker env (core 6.0.8, `xvfb` + `gi_bootstrap`) gave:
```
FAIL: test_hard_failure_gates_the_load_test
AssertionError: None is not an instance of <class 'AssertionError'> :
  a non-dependency load failure must gate the run (self.fail), not pass silently
... (the production method logged) "1 addon(s) failed to load:
       synthetic_broken_addon (ModuleNotFoundError: No module named 'totally_missing_dep')"
```
The module imported cleanly — the test failed because the production method ran
the full loop, collected the synthetic hard failure, and **returned without
raising**. Red on the exact R-C defect, on the real path. Restoring `self.fail`
→ both cases pass.

### C4 — verify in a checkout that contains the tests/ tree
Iteration 1's run-verify died with `tests/test_plugin_registration.py: No such
file or directory` because the default `addons-source-6.{0,1}` worktrees sit on
clean `upstream/maintenance/gramps6{0,1}`, which lack the PR #820 CI harness.
Following the sibling `820-review-nits` pattern I made feature-branch lane
worktrees and ran the engine runner (never a hand-rolled `docker run`):
```
git -C addons-source worktree add --detach addons-source-6.{0,1}-lanegate feature/ci-cd-pipeline-upstream
git -C gramps        worktree add --detach gramps-6.{0,1}-lanegate <gramps 6.{0,1} lane HEAD>
PDCA_BUNDLE=…/issue_820-pluginloading-gate PDCA_LANE=gate ./engine/scripts/ubuntu/run-verify.sh
```
Result, both legs:
```
C4-verify (addon, core 6.0.8): green-with-fix=PASS / red-without-fix=PASS
C4-verify (addon, core 6.1.0): green-with-fix=PASS / red-without-fix=PASS
```
Red leg: `plugin_load_gate.py` is removed → `ModuleNotFoundError` → red. The
"right reason" proof is the negative control above.

### Why the regression lives in a *separate* `tests/test_plugin_load_gate.py`
The brief's **Test file** field names `tests/test_plugin_registration.py`, and
the **production change** lives there. The regression *case*, however, is in a
dedicated module — a deliberate, called-out deviation, for two concrete reasons
discovered while verifying:

1. **C4 runs the whole selected test module.** When the case sat inside
   `test_plugin_registration.py`, run-verify's green leg ran the real,
   registry-backed `TestPluginLoading.test_load_all_addon_modules`, which — now
   that it gates — fails on purely *environmental* addon-load gaps in the minimal
   testbed image. Captured failure (real run, EXIT=1):
   ```
   FAIL: tests.test_plugin_registration.TestPluginLoading.test_load_all_addon_modules
   AssertionError: 2 addon(s) failed to load:
     Collections Clipboard Gramplet (gi.repository.GLib.GError:
       gtk-icon-theme-error-quark: Icon 'stock_link' not present in theme Yaru (0))
   ```
   This is the gate firing on a missing GTK icon theme — an image gap, not a
   defect this fix introduces, and flaky run-to-run (one run passed, the next
   failed). Isolating the regression keeps the gate's *verification*
   deterministic while the real integration test still does its job in actual
   CI.
2. **Import-collection gotcha.** `python3 -m unittest tests.test_plugin_load_gate`
   collects every `TestCase` bound in that module's namespace. A bare
   `from tests.test_plugin_registration import TestPluginLoading` would drag the
   heavy class in and unittest would re-run its real test here (observed: "Ran 3
   tests" with the heavy one failing). The fix imports the production *module*
   (`from tests import test_plugin_registration as prod`) and reaches the class
   via `prod.TestPluginLoading`, so only this file's two cases are discovered —
   while still driving the real production method.

## Scope / T5
Two new files beyond the brief's named edit surface, both deliberate and called
out: `tests/plugin_load_gate.py` (the gating decision, also the non-`test_*.py`
production file run-verify needs to revert for its red leg) and
`tests/test_plugin_load_gate.py` (the deterministic regression). Both are GI-free
test-tree modules with no translatable strings; addons-source has no top-level
`po/POTFILES`, and the T2-potfiles MUST is core-only (INTEGRATION.md §4), so no
POTFILES registration applies.

## Alternatives weighed (with cost)
- **Documented-advisory contract** (brief's other option). Rejected on the
  Invariant, not diff size — it would contradict the two sibling smoke tests.
  Cost difference is ~3 lines (`self.fail` wiring) vs a docstring.
- **Inline gate in `test_load_all_addon_modules`, no extracted module** (smallest
  diff: replace the 6 warn-lines with `if hard_failures: self.fail`, ~ -6/+3 in
  one file). Rejected: the only changed file would be a `test_*.py`, so run-verify
  exits "patch has no production change to revert" and the C4 gate cannot run. The
  extracted `plugin_load_gate.py` is the minimum that keeps the gate verifiable.
- **Regression case inside `test_plugin_registration.py`** (matches the brief's
  Test file field exactly). Rejected on the flaky-environment evidence above
  (EXIT=1 on the `stock_link` icon GError); a dedicated module is the cost of a
  deterministic gate.
- **Test the helper in isolation** (iteration 1). Rejected by the carry-forward
  and here: it never exercises `self.fail` on the production method.

## Commit-readiness
`black` (26.5.0) run over both new files (clean) and over the production hunks in
`test_plugin_registration.py`; the only line `black` wanted to reflow in that file
is a pre-existing one outside this change (`test_target_version_matches`'s fail
message), which I deliberately left untouched to keep the diff to one logical
change.

## Platforms exercised
Linux/Docker addon C4, both legs (core 6.0.8 and 6.1.0) under `xvfb` +
`gi_bootstrap`. Data-surface CI change, no GUI; no Windows / interface coverage.

## Cleanup
Throwaway `*-lanegate` worktrees were used for verification; shared infra left
clean (remove with `git worktree remove`).
