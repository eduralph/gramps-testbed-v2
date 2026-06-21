# Build notes — 820-review-nits

Target branch: `gramps-project/addons-source` PR #820 head
`feature/ci-cd-pipeline-upstream` (fork `eduralph/addons-source`), HEAD `1466491ab`.
All citations below are on that branch (pre-fix line numbers).

Five independent, low-risk cleanups (brief items a–e). Each is addressed; the one
behaviour-changing item that admits a unit test (c) is proven red→green.

## What each item does, and the line it fixes

### (a) Remove the dead `make_gramps_user()` helper
- Cite: `tests/gramps_test_env.py:116-123` defines `make_gramps_user()`.
- `git grep make_gramps_user origin/feature/ci-cd-pipeline-upstream` → **only the
  definition**, zero call sites on the branch. It is dead API.
- Brief offers "wired in or removed". Removed: nothing references it, and it is the
  only thing pulling `gramps.cli.user.User` into the helper module. Removing dead code
  is the minimal change; wiring up an unused helper would be inventing a caller.
- `Any` (the function's return annotation) is still used by `_plugin_cache: dict[str,
  Any]` and the `ClassVar[Any]` attributes, so the `from typing import Any` import
  stays — no follow-on lint.

### (b) Use the public `type_plugins()` instead of name-mangled private state
- Cite: `tests/test_plugin_registration.py:74` reaches
  `registry._PluginRegister__plugindata` — Python name-mangled access into
  `PluginRegister`'s private master list.
- The public `type_plugins()` is already used in the same file at
  `test_plugin_registration.py:120` (`type_plugins(t)` for a list of types) and `:126`.
- Fix: iterate the public type enumeration —
  `for ptype in PTYPE: for pdata in registry.type_plugins(ptype)`.
- Equivalence to `__plugindata`: `PTYPE` (`gramps/gen/plug/_pluginreg.py:99-116`) lists
  every plugin-type constant 0–15, and `register()` assigns each PluginData exactly one
  of those ptypes (`type_plugins` filters `x.ptype == ptype`,
  `_pluginreg.py:1534-1538`). The union over `PTYPE` therefore reproduces the full set
  of registered plugins — no duplicates (one ptype per record), nothing dropped. This
  is behaviour-preserving; the existing integration suite (`test_addons_discovered`,
  `test_load_all_addon_modules`, which assert the addon set is non-empty) is the
  CI-observable guard on the fork.
- `PTYPE` is added to the existing `from gramps.gen.plug._pluginreg import …` line.

### (c) Path-prefix check, not a substring test  ← the unit-tested item
- Cite (3 substring sites): `tests/test_plugin_registration.py:76`
  (`ADDONS_ROOT in pdata.fpath`), `:246` and `:278`
  (`p.fpath and ADDONS_ROOT in p.fpath` in the import/export smoke tests).
- Bug: `ADDONS_ROOT in fpath` is a *substring* test. A sibling checkout whose path
  merely starts with the repo path — e.g. `/work/addons-source-6.1/…` next to
  `/work/addons-source` — contains the root string and is wrongly classified as part of
  this repository. The intended test is a directory-prefix one:
  `fpath.startswith(ADDONS_ROOT + os.sep)`.
- Fix: extracted the predicate into **`tests/addon_paths.py`** as
  `is_in_addons_tree(fpath, addons_root)` and routed all three production sites through
  it (`_get_addon_plugins` and both smoke tests). Production and the test share one
  implementation — the test drives the same function production calls, not a copy.
- Why a new module rather than an inline change: the headless C4 runner cannot import
  `test_plugin_registration.py` (it pulls in `gramps.gen.plug` + the full plugin
  registration via `GrampsTestCase`). The predicate is pure-stdlib, so extracting it
  into a Gramps/GI-free module lets the unit run under a plain `python3 -m unittest`
  while keeping production on the same code path.

### (d) Include `.gpr.py` in the `compile-check` `py_compile` pass
- Cite: `.github/workflows/ci.yml:157` step name "(excluding .gpr.py)" and `:186`
  `find . -name '*.py' ! -name '*.gpr.py' …`.
- Fix: drop the `! -name '*.gpr.py'` exclusion (a `*.gpr.py` file already matches
  `-name '*.py'`), and update the step name + add a comment. `py_compile` only checks
  **syntax** — it does not execute the descriptor, so the `register()`/globals injected
  at registration time are irrelevant and there is no false failure; it just catches a
  `.gpr.py` syntax error at the compile stage instead of only at registration.

### (e) Tighten the `branches:` glob to real series branches
- Cite: `.github/workflows/ci.yml:23` and `:25` (`maintenance/gramps**`), and
  `.github/workflows/docker-build.yml:9` (same glob).
- Bug: `gramps**` also matches `maintenance/gramps-foo`, which then only fails later in
  the `setup` job's ref regex (`ci.yml:47`, `case "$suffix" in gramps[0-9][0-9])`).
- Fix (brief's "tighten" option): `maintenance/gramps[0-9][0-9]` in all three filters.
  GitHub Actions branch filters support `[0-9]` character classes (filter-pattern cheat
  sheet), and this exactly mirrors the `setup` job's existing `gramps[0-9][0-9]` regex,
  so the two no longer disagree. PR #820 (base `maintenance/gramps60`) and gramps61 both
  still match.

## Verification (red → green)

The unit test is `tests/test_addon_paths.py` (brief item c: "a sibling dir sharing a
name prefix is not matched"). Items a/b/d/e are behaviour-preserving / CI-observable per
the brief and are not separately unit-tested.

**C4 runner.** `run-verify.sh` validates an addon patch against the clean
`upstream/maintenance/gramps{60,61}` worktrees — but those branches do **not** carry the
PR #820 harness files (`tests/test_plugin_registration.py`, `tests/gramps_test_env.py`,
`.github/workflows/*`), so a patch that modifies them cannot `git apply` there. The
contribution target for these cleanups is the PR #820 head branch itself (see
`results/issue_pr820-ci-checkin/README.md`: "the workflows live *in* the PR … CI is
exercised end-to-end on the `eduralph/addons-source` fork"). I therefore ran the **same**
engine runner against a throwaway lane of feature-branch worktrees:

```
git worktree add --detach addons-source-6.{0,1}-lanenits <feature HEAD>
git worktree add --detach gramps-6.{0,1}-lanenits <gramps 6.{0,1} HEAD>
PDCA_BUNDLE=…/issue_820-review-nits PDCA_LANE=nits ./engine/scripts/ubuntu/run-verify.sh
```

Result, both legs:
```
C4-verify (addon, core 6.0.8): green-with-fix=PASS / red-without-fix=PASS
C4-verify (addon, core 6.1.0): green-with-fix=PASS / red-without-fix=PASS
```
(worktrees removed afterward; shared infra left clean.)

The patch is ordered so `tests/test_addon_paths.py` is the **last** `test_*.py` hunk, so
the runner selects it (not the heavyweight `test_plugin_registration.py`) as the C4
module — keeping the gate import-light and headless-safe.

**Negative control (proves the test checks the prefix logic, not just import
presence).** The C4 red leg goes red because reverting the production change removes
`tests/addon_paths.py` → `ModuleNotFoundError`. To show the *test content* actually
encodes the prefix requirement, I ran it against a deliberately substring-buggy
`is_in_addons_tree` (`return addons_root in fpath`):
```
FAIL: test_sibling_sharing_name_prefix_not_matched  (AssertionError: True is not false)
FAIL: test_root_itself_not_matched
```
So the test fails on the exact behaviour item (c) fixes, and passes only with the
prefix implementation. End result (c) — sibling dirs no longer misclassified — holds.

## Commit-readiness

`addons-source` has no repo-level `black`/pre-commit hook (only `ChatWithTree` ships its
own `.pre-commit-config.yaml`). I still ran `black` over the four touched/added Python
files: it left my edits unchanged and the new files conformant. It additionally wanted to
re-join one *unrelated* line in `test_plugin_registration.py` (the `self.fail(…)` block I
do not touch); I reverted that to keep the diff to the five items only — one logical change
set, no drive-by reformatting.

## Rejected alternatives
- **(b) keep `__plugindata`, add a `# noqa`/comment.** Rejected: the brief asks for the
  public API and one is already in use in the file; silencing the access leaves the
  private coupling.
- **(c) inline `startswith` at all three sites, no shared helper.** Diff would be ~3
  one-line edits instead of a new 47-line module, but it (i) duplicates the predicate
  three times and (ii) leaves nothing headless-importable to unit-test, forcing the C4
  module to be the full `GrampsTestCase` integration test (boots plugin registration
  under xvfb — minutes, AT-SPI-fragile) instead of a 0.001 s stdlib unit. The shared
  helper is the smaller *testable* change.
- **(e) document the glob as intentional instead of tightening.** The brief allows it,
  but the `setup` job already enforces `gramps[0-9][0-9]`; tightening the filter to match
  removes the disagreement rather than annotating it, at the cost of two extra comment
  lines.
