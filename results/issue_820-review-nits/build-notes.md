# Build notes — 820-review-nits (iteration 4)

> Withheld from the reviewer. Rationale + what I ruled out, for the human at sign-off.

## TL;DR

Iteration 4 is **not a new approach** — iterations 2 and 3 were rejected on a single
mechanical fault: **C4 "patch does not apply"** because the patch was cut against / verified
on a *stale* `addons-source-6.0-fork` worktree. The substantive design from v3 (item (b)'s
typeless-preserving enumeration, item (c)'s extracted path predicate) was already correct and
already addressed the iteration-1 carry-forward. So this iteration:

1. Re-confirmed the verification base: the fork worktree HEAD `67ed38d39` now **equals**
   `origin/feature/ci-cd-pipeline-upstream` (the brief's Verification base / Onto branch).
2. Re-cut/re-checked the patch against that synced tree — `git apply --check` is clean on all
   six files.
3. Ran `run-verify.sh` (C4) end-to-end: **green-with-fix=PASS / red-without-fix=PASS**.
4. Re-verified each item (a)–(e) on the branch and confirmed the T3 Sqlite noise is unrelated.

The earlier failures were never about the *change* — they were base/worktree-sync. With the
base synced, red→green actually runs.

## The five items, with target-branch citations (branch `feature/ci-cd-pipeline-upstream`)

**(a) dead `make_gramps_user()` — removed.**
`tests/gramps_test_env.py:116` defines it; `git grep make_gramps_user` on the branch returns
**only that definition** (no caller). Removed the function (and its function-local
`from gramps.cli.user import User`, which was the only use of that import). No module-level
import is orphaned — `Any` is still used by `get_plugin_manager_and_registry()`
(`gramps_test_env.py:95`).

**(b) `_PluginRegister__plugindata` → public `type_plugins()` — enumeration that preserves the
typeless case.** `tests/test_plugin_registration.py:74` iterated the name-mangled master list
`registry._PluginRegister__plugindata`. Replaced with a union over the public API:
`for ptype in (None, *PTYPE): registry.type_plugins(ptype)`.

This is the crux of the **iteration-1 carry-forward**, which (correctly) rejected the naïve
`for ptype in PTYPE` rewrite: `type_plugins(ptype)` is `[x for x in __plugindata if x.ptype ==
ptype]` (verified at gramps-6.0 `gramps/gen/plug/_pluginreg.py:1538`), and `PluginData._ptype`
defaults to `None` (`_pluginreg.py:465`) — a half-registered addon whose `ptype` was never set
keeps `_ptype is None`, which is in **no** `PTYPE` member, so a `PTYPE`-only sweep would
*silently drop* exactly the malformed addon this registration smoke test exists to catch.

The fix: include `None` in the sweep. `type_plugins(None)` returns precisely the typeless
records (no raise — the getter is a plain attribute read, `_pluginreg.py:627-628`; only the
*setter* validates, `:631-636`). Since every record's ptype is in `{None} ∪ PTYPE` and the
filter is `==`, the union is **disjoint and exhaustive** — it reproduces the full
`__plugindata` master list exactly, with the typeless entries still surfaced. So a
half-registered addon now *fails* the registration test instead of vanishing from it. PTYPE
covers all 16 defined types (`_pluginreg.py:99-116`), so well-formed addons are unaffected.

**(c) substring → path-prefix check.** `test_plugin_registration.py:76,253,285` used
`ADDONS_ROOT in pdata.fpath` — a substring test that wrongly matches a sibling checkout sharing
the name prefix (e.g. `…/addons-source-6.1/…` contains the substring `…/addons-source`).
Extracted the predicate into a new GI-free module `tests/addon_paths.py::is_in_addons_tree`,
which does `fpath.startswith(addons_root + os.sep)` (and treats a falsy `fpath` as not-inside).
`_get_addon_plugins` and the import/export smoke filters now all route through it.

**(d) `.gpr.py` included in `py_compile`.** `ci.yml:162`'s `find … ! -name '*.gpr.py'` excluded
descriptors. `py_compile` only checks *syntax* — it never executes the file, so the
`register()`/injected globals at registration time are irrelevant and there's no false failure;
including them catches a `.gpr.py` syntax error at the compile stage instead of only later at
registration. Dropped the exclusion and updated the step name/comment (`ci.yml:141`).

**(e) branch filter tightened.** `ci.yml:23,25` and `docker-build.yml:9` used
`maintenance/gramps**`, which also matches `maintenance/gramps-foo` (only to fail later in the
`setup` job's `gramps[0-9][0-9]` ref regex). Tightened to `maintenance/gramps[0-9][0-9]` so only
real series branches trigger the workflow, with a comment explaining why.

## Why an extracted module + import-light test (not a test that imports the tool)

C4 is **headless** (addon mode = xvfb only, no D-Bus/AT-SPI). `test_plugin_registration.py`
imports `GrampsTestCase`, which boots the plugin manager — too heavy / GUI-entangled for the C4
runner. Per principles §3.4 the test must drive the **production path**, not a copy. So I put
the item-(c) predicate in `tests/addon_paths.py` (imports only `os`) and had **both** production
(`_get_addon_plugins`, the import/export smoke filters) and the new unit
(`tests/test_addon_paths.py`) call the *same* `is_in_addons_tree`. The test is import-light
(`os`, `unittest`, the helper) so it runs under plain unittest; production routes through it, so
there is no parallel hand-copy to drift.

The C4 red leg removes the new `addon_paths.py`, so red-without-fix is an `ImportError`. The
*behavioral* guard is still real: `test_sibling_sharing_name_prefix_not_matched` asserts the
prefix semantics, so reverting `is_in_addons_tree` to a substring implementation fails it. The
brief asked exactly for "a small unit asserting path-prefix matching (a sibling dir sharing a
name prefix is not matched)" — that is the case the test encodes.

## Alternatives ruled out

- **Item (b): keep reaching into `_PluginRegister__plugindata`.** Rejected — the brief names the
  public `type_plugins()` as the target and the public API is already used elsewhere in the file
  (`type_plugins(IMPORT)`, `type_plugins(EXPORT)`). The `(None, *PTYPE)` union is the
  smallest public-API change that is *provably equivalent* to the master list (disjoint +
  exhaustive over the ptype domain), so it satisfies (b) without the coverage regression the
  iteration-1 carry-forward caught.
- **Item (a): wire `make_gramps_user()` in somewhere.** Rejected — nothing on the branch needs a
  batch `User`; there is no import/export driver here that would consume it. Removing dead API
  is the lower-risk resolution and matches the brief's "(a) helper wired in **or removed**".
- **Item (c): inline `pdata.fpath.startswith(ADDONS_ROOT + os.sep)` at each of the 3 call
  sites.** Rejected — three identical inline expressions can't be unit-tested without booting
  the plugin system (GUI-heavy, not C4-runnable). Extracting one predicate is ~47 lines of new
  module + 3 one-line call-site edits, versus 3 inline copies that drift and are untestable
  headless. The extraction is what makes the brief's required unit test possible at all.

## Splitting (T5 / one-logical-change)

The brief (`brief.md:5-6,47`) explicitly bundles five *independent* nits and says the
planner/human "may split any item into its own brief if it warrants a separate PR." The planner
did **not** split this bundle, so the bundle's scope is all five. I keep them in one
`patch.diff` (one bundle = one patch), but they are cleanly separable into per-item commits at
publish if the human prefers:
- commit 1 — (a) remove dead `make_gramps_user` (`gramps_test_env.py`)
- commit 2 — (b)+(c) `type_plugins()` enumeration + `is_in_addons_tree` predicate + its unit test
  (`test_plugin_registration.py`, new `addon_paths.py`, new `test_addon_paths.py`)
- commit 3 — (d) include `.gpr.py` in `py_compile` (`ci.yml`)
- commit 4 — (e) tighten branch filter (`ci.yml`, `docker-build.yml`)

(b) and (c) share `test_plugin_registration.py` edits, so they naturally co-commit; (b)'s
enumeration is the iteration-1 carry-forward's "own change at minimum" — it is isolated in
commit 2.

## Verification performed

- **C4 (gating):** `PDCA_BUNDLE=… run-verify.sh` → leg 6.0 against `addons-source-6.0-fork`
  (FORK_REF = `origin/feature/ci-cd-pipeline-upstream`): `tests.test_addon_paths` —
  **green-with-fix=PASS / red-without-fix=PASS** (red = `ModuleNotFoundError` once the helper is
  removed; the 5 prefix assertions pass with it present).
- `git apply --check` clean on all six files against the synced fork worktree (HEAD
  `67ed38d39` == verification base).
- `py_compile` OK on all four touched/added `.py` files; `PTYPE` and `is_in_addons_tree` are
  imported **and used** (no F82 undefined-name).
- `black --check`: my edited regions are clean. Black would reformat an *unrelated* pre-existing
  region (`test_plugin_registration.py` ~line 152, a `self.fail(...)` my patch never touches) —
  this is upstream and out of scope, and addons-source enforces **no** black (no
  `.pre-commit-config.yaml`, no `[tool.black]`; CI lint is `ruff --select=E9,F63,F7,F82` only,
  `ci.yml:83`).

## POTFILES

Doc-16's `po/POTFILES.in`/`.skip` registration is a **gramps-core** rule. addons-source has no
top-level POTFILES (only per-addon, e.g. `DynamicWeb/po/POTFILES.in`); the harness-level
`tests/` tree is not in any addon's translatable set. So the new `tests/addon_paths.py` and
`tests/test_addon_paths.py` need no POTFILES entry, and the removed function (a same-file edit,
not a file deletion) needs none either.

## T3 advisory Sqlite delta — not this patch

The carry-forward flagged `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sql` failing
on the **gramps61 × core 6.1** advisory leg. Root cause from the log
(`t3-run-addon-unit-61.log:4598-4607`): `ValueError: too many values to unpack (expected 21)` in
`Sqlite/ExportSql.py:684` `export_person` — the Sqlite addon's hard-coded 21-field Person tuple
no longer matches gramps 6.1 core's `Person.serialize()` layout. This is a core-6.1↔Sqlite
schema drift; my patch touches **none** of `Sqlite/`, Person serialization, or gramps core (it
edits CI YAML, a path-predicate helper, a dead-function removal, and a behavior-preserving
registry enumeration). It is pre-existing 6.1-line baseline noise, reproduces without this
patch, and the gramps60 leg (the actual target) is green.
