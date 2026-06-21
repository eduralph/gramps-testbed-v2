# Build notes — 820-review-nits (iteration 2)

Target branch: `gramps-project/addons-source` PR #820 head
`feature/ci-cd-pipeline-upstream` (fork `eduralph/addons-source`), HEAD `67ed38d39`
(= `origin/feature/ci-cd-pipeline-upstream`, the brief's Verification base; local
branch is in sync with origin, 0 ahead / 0 behind). All citations below are
pre-fix line numbers on that branch.

Five independent, low-risk cleanups (brief items a–e). Each is addressed; the one
behaviour-changing item that admits an import-light unit test (c) is proven red→green.

## Why this is not iteration 1 re-submitted

The previous attempt was rejected on **two** grounds; both are fixed here.

1. **C5 — item (b) was not equivalent (the substantive rejection).** Iteration 1
   replaced `for pdata in registry._PluginRegister__plugindata` with
   `for ptype in PTYPE: registry.type_plugins(ptype)`. `type_plugins(ptype)` is
   `[x for x in __plugindata if x.ptype == ptype]` (`gramps-6.1`
   `gramps/gen/plug/_pluginreg.py:1534-1538`; identical body in 6.0 `:1534-1538`).
   `PTYPE` lists only the 16 *valid* types (`_pluginreg.py:99-116`), and a
   `PluginData._ptype` **defaults to `None`** (`_pluginreg.py:465`) — the setter
   refuses anything outside PTYPE (`_pluginreg.py:631-636`). So a half-registered
   addon whose ptype was never set keeps `_ptype is None`, which is **not** in PTYPE,
   and the `for ptype in PTYPE` union silently dropped it — making the very
   failure class this registration smoke test exists to catch invisible.

   **Fix:** iterate `for ptype in (None, *PTYPE)`. `type_plugins(None)` returns
   exactly the typeless records (the same call the file already trusts at
   `test_plugin_registration.py:126`, `type_plugins(None)`), so the union over
   `{None} ∪ PTYPE` reproduces the full `__plugindata` master list exactly: every
   record's `_ptype` is in that set, and since each record has exactly one ptype,
   none is double-counted. A typeless / half-registered addon now still surfaces in
   `_get_addon_plugins`, so it FAILS the registration test rather than vanishing.
   This keeps the brief's intent (use the public API, drop the name-mangled private
   access) **without** the coverage loss. See `patch.diff:157-176`.

2. **C4 — red→green never ran (a path/harness mismatch).** Iteration 1's verify
   failed with `tests/test_plugin_registration.py: No such file or directory`. Root
   cause: `run-verify.sh` (addon mode + a `Verification base` field) patches the
   dedicated `addons-source-6.0-fork` worktree, which was **stale** — checked out at
   an older commit that predated the harness/workflow shape this patch edits, so
   `git apply` could not land the `ci.yml` / `test_plugin_registration.py` hunks.
   **Fix:** realigned it with `make fork-worktrees` (reads `engine/fork-bases.tsv`:
   `6.0 → origin/feature/ci-cd-pipeline-upstream`) so the worktree is at `67ed38d39`,
   the same base the patch is built against. Verify then ran clean — see below.

The other carry-forward notes (T1 "no .gpr.py", T3 8× Sqlite delta) are addressed
under "Non-issues" at the end.

## What each item does, and the line it fixes

### (a) Remove the dead `make_gramps_user()` helper — `patch.diff:113-133`
- Cite: `tests/gramps_test_env.py:116-123` defines `make_gramps_user()`.
- `git -C addons-source grep make_gramps_user` → **only the definition**, zero call
  sites on the branch. Dead API.
- Brief offers "wired in or removed". Removed: nothing references it, and it is the
  only thing that would pull `gramps.cli.user.User` into the helper module. Wiring up
  an unused helper would mean inventing a caller. `Any` (its return annotation) is
  still used by `_plugin_cache: dict[str, Any]` and the `ClassVar[Any]` attributes,
  so `from typing import Any` stays — no follow-on lint.

### (b) Public `type_plugins()` instead of name-mangled private state — `patch.diff:134-176`
- Cite: `tests/test_plugin_registration.py:74` reaches
  `registry._PluginRegister__plugindata`. The public `type_plugins()` is already used
  in the same file (`:121`, `:126`, `:252`, `:285`).
- Fix described above: `for ptype in (None, *PTYPE): registry.type_plugins(ptype)`,
  with an inline comment recording the `{None} ∪ PTYPE` equivalence argument and the
  deliberate inclusion of `None`. `PTYPE` is added to the existing
  `from gramps.gen.plug._pluginreg import …` line (`patch.diff:142-143`).

### (c) Path-prefix check, not a substring test  ← the unit-tested item
- Cite (3 substring sites): `tests/test_plugin_registration.py:76`
  (`ADDONS_ROOT in pdata.fpath`), `:253` and `:285`
  (`p.fpath and ADDONS_ROOT in p.fpath` in the import/export smoke tests).
- Bug: `ADDONS_ROOT in fpath` is a *substring* test. A sibling checkout whose path
  merely starts with the repo path — e.g. `/work/addons-source-6.1/…` next to
  `/work/addons-source` — contains the root string and is wrongly classified as part
  of this repository. The intended test is a directory-prefix one,
  `fpath.startswith(ADDONS_ROOT + os.sep)`.
- Fix: extracted the predicate into **`tests/addon_paths.py`** as
  `is_in_addons_tree(fpath, addons_root)` (`patch.diff:60-112`) and routed all three
  production sites through it. Production and the test drive the **same** function — no
  parallel copy.
- Why a new module rather than an inline `startswith`: the headless C4 runner cannot
  import `test_plugin_registration.py` (it pulls in `gramps.gen.plug` + the full
  plugin registration via `GrampsTestCase`). The predicate is pure-stdlib, so an
  import-light module lets the unit run under a plain `python3 -m unittest` while
  keeping production on that exact code path.

### (d) Include `.gpr.py` in the `compile-check` `py_compile` pass — `patch.diff:21-42`
- Cite: `.github/workflows/ci.yml:141` step name "(excluding .gpr.py)" and `:162`
  `find . -name '*.py' ! -name '*.gpr.py' …`.
- Fix: drop the `! -name '*.gpr.py'` exclusion (a `*.gpr.py` file already matches
  `-name '*.py'`), update the step name, add a comment. `py_compile` only checks
  **syntax** — it does not execute the descriptor, so the `register()`/globals
  injected at registration time are irrelevant and there is no false failure; it just
  catches a `.gpr.py` syntax error at the compile stage instead of only at
  registration.

### (e) Tighten the `branches:` glob to real series branches — `patch.diff:1-17,45-56`
- Cite: `.github/workflows/ci.yml:23` and `:25` (`maintenance/gramps**`), and
  `.github/workflows/docker-build.yml:9` (same glob).
- Bug: `gramps**` also matches `maintenance/gramps-foo`, which then only fails later
  in the `setup` job's ref regex (`ci.yml:47`, `case "$suffix" in gramps[0-9][0-9])`).
- Fix (brief's "tighten" option): `maintenance/gramps[0-9][0-9]` in all three
  filters. GitHub Actions branch filters support `[0-9]` character classes, and this
  exactly mirrors the `setup` job's existing `gramps[0-9][0-9]` regex, so the two no
  longer disagree. PR #820 (base `maintenance/gramps60`) and gramps61 both still
  match; `gramps-foo` is now rejected at the trigger, not mid-job.

## Verification (red → green)

Unit test: `tests/test_addon_paths.py` (brief item c: "a sibling dir sharing a name
prefix is not matched"). Items a/b/d/e are behaviour-preserving / CI-observable per
the brief and are not separately unit-tested.

**C4 runner** (`./engine/scripts/ubuntu/run-verify.sh`, `PDCA_BUNDLE` set to this
bundle), after `make fork-worktrees` realigned `addons-source-6.0-fork` to
`origin/feature/ci-cd-pipeline-upstream` (`67ed38d39`):

```
→ fork verification base: origin/feature/ci-cd-pipeline-upstream → addons-source-6.0-fork (single leg 6.0)
→ C4-verify (addon, core 6.0.8): tests.test_addon_paths
→ green check (fix applied):      Ran 5 tests … OK
→ red check (production reverted): ModuleNotFoundError: No module named 'tests.addon_paths' → FAILED
C4-verify: green-with-fix=PASS / red-without-fix=PASS
```

The patch orders `tests/test_addon_paths.py` as the **last** `test_*.py` hunk so the
runner selects it (not the heavyweight `test_plugin_registration.py`, which imports
`gramps.gen.plug` via `GrampsTestCase` and would core-dump the headless C4 runner) as
the C4 module. Only `6.0` runs because the brief targets `maintenance/gramps60` and
`fork-bases.tsv` carries only the 6.0 fork leg; the maintainer cherry-picks gramps60
→ gramps61 and the helper is pure-stdlib, so it holds identically on 6.1.

**Negative control** (proves the test encodes the *prefix* requirement, not just
import presence). The C4 red leg goes red because reverting the change removes
`tests/addon_paths.py` → `ModuleNotFoundError`. To show the *test content* actually
requires prefix semantics, I re-ran the same test against a deliberately
substring-buggy `is_in_addons_tree` (`return addons_root in (fpath or "")`):

```
FAIL: test_sibling_sharing_name_prefix_not_matched  (AssertionError: True is not false)
FAIL: test_root_itself_not_matched
Ran 5 tests … FAILED (failures=2)
```

So the test fails on the exact behaviour item (c) fixes and passes only with the
prefix implementation. End result (c) — sibling dirs no longer misclassified — holds.

## Commit-readiness

`addons-source` has no repo-level `black`/pre-commit hook for the `tests/` harness
(only `ChatWithTree` ships its own `.pre-commit-config.yaml`). I still ran
`black 26.5.0` over the four touched/added Python files: it left every line I
add/change unchanged. It additionally wanted to re-join one *unrelated* `self.fail(…)`
continuation in `test_plugin_registration.py` (the
`test_target_version_matches_gramps_install` block I do not touch); I reverted that to
keep the diff to the five items only — one logical change set, no drive-by
reformatting.

**POTFILES:** N/A here. addons-source has no `po/POTFILES.in` / `po/POTFILES.skip`
for the `tests/` harness (its `po/` holds the addon-translation `addons.pot` + `.po`
only); the existing `tests/*.py` files are registered nowhere, so the new
`tests/addon_paths.py` / `tests/test_addon_paths.py` follow that same convention.
(The doc-16 POTFILES rule is a gramps-core mechanism, not an addons-source-harness
one.)

## Scope / splitting (carry-forward T5 — for the human)

The carry-forward asks to prefer one-logical-change-per-PR and, at minimum, to land
item (b) as its own change. This bundle's brief still scopes all five (a–e), and a
builder produces a single `patch.diff` per bundle — splitting into separate PRs is the
planner/human decision the brief itself flags (`brief.md:5-6,47`) and that T5 raises.
I have therefore kept the patch internally organised as **five independent hunks**
(each touches disjoint code: a→`gramps_test_env.py`; b→`_get_addon_plugins`;
c→`addon_paths.py` + 3 call sites + test; d→`ci.yml` compile step; e→`ci.yml` +
`docker-build.yml` triggers), so a `git apply`-per-hunk split is mechanical if the
human chooses to split at publish. Item (b)'s enumeration fix in particular stands
alone (`patch.diff:142-176`).

## Rejected alternatives

- **(b) keep `__plugindata`, add a `# noqa`/comment.** Rejected: the brief asks for
  the public API and one is already in use in the file; silencing the access leaves
  the private coupling — and does nothing for the typeless-coverage point. Cost of the
  chosen fix over this: +2 comment lines and `for ptype in (None, *PTYPE)` vs a single
  `# noqa` — trivially small, and it removes the private coupling the brief names.
- **(b) `for ptype in PTYPE` (iteration 1's approach).** Rejected — silently drops
  `_ptype is None` records (the rejection reason above). `(None, *PTYPE)` is the
  one-token-larger form that stays equivalent to `__plugindata`.
- **(c) inline `startswith` at all three sites, no shared helper.** The diff would be
  3 one-line edits instead of a 47-line module + 88-line test. But it leaves *nothing
  headless-importable to unit-test*, forcing the C4 module to be the full
  `GrampsTestCase` integration test — which boots plugin registration and imports
  `gramps.gen.plug`, i.e. it **core-dumps the headless C4 runner** (the exact failure
  the task warns about) and otherwise needs xvfb + minutes per run vs the 0.000 s
  stdlib unit here. The shared helper is the smallest *testable* change, and
  production routes through it (no copy).
- **(e) document the glob as intentional instead of tightening.** The brief allows it,
  but the `setup` job already enforces `gramps[0-9][0-9]`; tightening the filter to
  match removes the disagreement rather than annotating it, at the cost of two extra
  comment lines.

## Non-issues from the carry-forward

- **T1 "no .gpr.py".** Advisory, mechanically misfired: this patch is test-harness +
  workflow cleanup, not an addon submission, so the addon-structure rules
  (folder==id, `.gpr.py`, `target_version`) do not apply (`brief.md:33` Scope).
- **T3 8× `Sqlite … ExportSQLTestCase::test_export_sq` delta on the 6.1 axis.**
  Unattributed and in the Sqlite addon's *own* export tests; this patch touches only
  harness/workflow code and nothing under `Sqlite/`. Per the carry-forward it is
  6.1-baseline noise to confirm reproduces *without* this patch — it cannot be caused
  by these five cleanups.
