# Brief — issue 820-review-nits / batched low-risk cleanups in the #820 harness

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Decomposed from `results/issue_pr820-ci-checkin/` (the nits batch). Tracks
> addons-source PR #820. NOTE: bundles several *independent* low-risk cleanups; the
> human/planner may split any item into its own brief if it warrants a separate PR.

- **Slug:** 820-review-nits
- **Defect:** a set of independent low-risk issues in PR #820's test/harness code:
  - **(a)** `tests/gramps_test_env.py` defines `make_gramps_user()` but nothing on the
    branch references it (dead API).
  - **(b)** `tests/test_plugin_registration.py::_get_addon_plugins` reaches the
    name-mangled private `registry._PluginRegister__plugindata`, while the public
    `type_plugins()` is already used elsewhere in the same file.
  - **(c)** the same file's `ADDONS_ROOT in pdata.fpath` is a substring test where a
    path-prefix check is meant (`pdata.fpath.startswith(ADDONS_ROOT + os.sep)`).
  - **(d)** the `compile-check` job excludes `*.gpr.py` from `py_compile` (cheap to
    include; would catch `.gpr.py` syntax errors at the compile stage rather than only
    at registration).
  - **(e)** the workflow `branches:` filter `maintenance/gramps**` also matches
    `maintenance/gramps-foo`, which then only fails later in the `setup` regex —
    tighten it or document it as intentional.
- **Success criterion:** each item resolved — (a) helper wired in or removed; (b)
  public `type_plugins()` used; (c) path-prefix check; (d) `.gpr.py` included in
  `py_compile`; (e) branch filter tightened or documented. PR #820 CI green on the
  `eduralph/addons-source` fork.
- **Repo + branch target:** gramps-project/addons-source @ `maintenance/gramps60` via
  `feature/ci-cd-pipeline-upstream`; tested on the `eduralph/addons-source` fork.
- **Verification base:** origin/feature/ci-cd-pipeline-upstream
- **Onto branch:** origin/feature/ci-cd-pipeline-upstream
- **Surfaces:** data.
- **Depends on:** 820-build-toolchain-coverage
  (nits runs **last** in the C2 → C3 → nits `ci.yml` chain — depending on C3 transitively
  orders it after C2 too. It also edits `tests/test_plugin_registration.py` ((b)/(c)); R-C
  (`820-pluginloading-gate`) already shipped that file and is COMPLETE, so the old
  "not concurrently with R-C" conflict is moot — no `Conflicts with` needed.)
- **Scope:** the five cleanups above. / out of scope: the lib convergence
  (`820-converge-*`), the gating fix (`820-pluginloading-gate`), the toolchain
  decision (`820-build-toolchain-coverage`). (No invariant cited — these are
  independent non-structural cleanups, principles §1.1.)
- **Repro instruction:** per item — `git grep make_gramps_user` (definition only);
  `grep -n "_PluginRegister__plugindata\|ADDONS_ROOT in pdata.fpath"
  tests/test_plugin_registration.py`; the `compile-check` step's `find … ! -name
  '*.gpr.py'`; the `on:` `branches:` glob in `ci.yml`/`docker-build.yml`.
- **Test file:** existing `tests/test_plugin_registration.py` must still pass; for (c)
  add a small unit asserting path-prefix matching (a sibling dir sharing a name prefix
  is not matched). The rest are behaviour-preserving / CI-observable.
- **Citations expected:** Do cites path:line for each of (a)–(e) on the PR branch.
- **Prior-art check (triage cycles):** review nits batch
  (`results/issue_pr820-ci-checkin/`); no prior fix.
- **Disposition hint:** likely-fix (small, low-risk; splittable).

## STOP discipline

Draft only until Check sign-off. The PR MUST NOT be marked ready before sign-off
accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: C5 is not fulfilled: item (b)'s refactor is NOT equivalent to the code it replaces, and the divergence silently hides the exact defect the test exists to catch. The defect (verified against gramps-6.1 gramps/gen/plug/_pluginreg.py): - old: `for pdata in registry._PluginRegister__plugindata` (ALL plugin data, path-filtered) → includes a pdata whose ptype was never set. - new: `for ptype in PTYPE: registry.type_plugins(ptype)`, and type_plugins is `[x for x in __plugindata if x.ptype == ptype]` (_pluginreg.py:1534). This yields only {pdata : pdata.ptype in PTYPE}. - PluginData._ptype defaults to None (_pluginreg.py:465); the ptype setter raises if ptype not in PTYPE (line 632). So a plugin that registered WITHOUT a valid ptype keeps _ptype=None, which is not in PTYPE, and type_plugins never returns it. - Net: the new code silently drops a malformed / typeless addon from _get_addon_plugins — and that feeds the plugin-REGISTRATION smoke test, i.e. the new code makes the very failure class the test exists to catch invisible. Same silent-coverage-loss-reported-as-green anti-pattern the rest of #820 fights. Fix in the rebuild: enumerate so a typeless/unset-ptype pdata still surfaces (keep iterating __plugindata, or explicitly include unset-ptype entries), so a half-registered addon FAILS the registration test rather than vanishing. (PTYPE does cover all 16 defined types REPORT..CITE, so well-formed addons are fine; the gap is only the ptype=None case.) Also carry forward: - T5 / scope: the brief itself (brief.md:5-6,47) flags the five nits (a)-(e) are splittable and the discipline is one-logical-change-per-PR. Prefer splitting per logical change rather than one combined patch (at minimum, item (b)'s enumeration fix is its own change). - C4 FAILED on a path/harness mismatch (run-verify.sh could not find tests/test_plugin_registration.py though the patch modifies it) — red->green was never executed; verify on the correct tree next time. - T3-61 delta (8x Sqlite test_export_sq) is unattributed and touches no Sqlite code — confirm it reproduces without this patch (likely 6.1 baseline noise). - Rebuild on the synced base: local main is 11 behind origin + dirty; update gramps-testbed-v2 before the rebuild (batch is pausing for that).
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — error: tests/test_plugin_registration.py: No such file or directory
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 8 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: issue_820-review-nits: C4 was a gating FAIL ("patch does not apply" against the verification base) — root cause was the brief missing the branch/base information, so the patch was verified against the wrong base. The brief has now been updated with the correct branch target. Rebuild on the synced base so the patch applies and red→green actually runs; then re-verify the §6 items (C2 repro, C5 causal, T3 6.1 noise, T5 scope). Also honor the standing carry-forward on T5 scope: split the combined diff per logical change (item (b)'s enumeration fix is its own change at minimum), per the brief and iter-1 carry-forward.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — error: .github/workflows/ci.yml: patch does not apply
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 3 — carry-forward (from the previous attempt)
- Sign-off rationale: issue_820-review-nits Rejected: C4 gate red — patch.diff does not apply ("error: .github/workflows/ci.yml: patch does not apply"), so the test was never shown red-pre/green-post. Patch was cut against a stale base; re-cut all hunks against current maintenance/gramps60 (ci.yml has moved since these hunks were written). Also fix before re-Check: - Advisory review never completed (reviewer leaf crashed, exit 1) — there is no §5 verdict and the §6 NEEDS-HUMAN item cannot be cleared until a review exists. Ensure the reviewer leaf runs. - T3 gramps61 × core 6.1 regression: 1 new failure vs baseline — Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq. Investigate whether the py_compile/.gpr.py inclusion change or the type_plugins() rewrite triggers it; gramps60 matrix is green.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — error: .github/workflows/ci.yml: patch does not apply
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Full previous attempt preserved in `iteration-v3/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
