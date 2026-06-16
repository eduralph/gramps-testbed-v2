# Brief — issue 820-pluginloading-gate / make TestPluginLoading gate or be advisory

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Decomposed from `results/issue_pr820-ci-checkin/` (finding R-C). Tracks
> addons-source PR #820.

- **Slug:** 820-pluginloading-gate
- **Defect:** in `tests/test_plugin_registration.py`,
  `TestPluginLoading.test_load_all_addon_modules` accumulates `hard_failures` and
  `crash_failures` but only `LOG.warning`s them; its **only** assertion is
  `assertGreater(len(plugins), 0)`. A genuine non-dependency load failure therefore
  passes silently — unlike the sibling smoke tests (`TestImportPluginSmoke`,
  `TestExportPluginSmoke`), which `self.fail` on findings. The test is an always-pass
  gate (except for the zero-plugins case): it names a failure class it cannot fail on.
- **Success criterion:** the test either `self.fail`s on non-dependency
  `hard_failures` (a real gate) **or** its docstring explicitly declares it
  diagnostic-only / advisory and never gates — the decision is deliberate, and the
  always-pass-by-omission state is removed. A synthetic non-dep load failure produces
  the chosen outcome (fail, or a documented advisory warning).
- **Invariant to restore:** a CI test that names a failure class gates on it, or
  declares itself advisory — no test silently always-passes while appearing to check
  loadability. Stated over the category (every gating test). Source: `docs/principles.md`
  and global CLAUDE.md ("a green mechanical check is not a correctness verification").
- **Repo + branch target:** gramps-project/addons-source @ `maintenance/gramps60` via
  `feature/ci-cd-pipeline-upstream`; tested on the `eduralph/addons-source` fork.
- **Verification base:** origin/feature/ci-cd-pipeline-upstream
- **Surfaces:** data (CI test; no GUI).
- **Depends on:** none. Edits `tests/test_plugin_registration.py`, also touched by
  `820-review-nits` (nits (b)/(c)) → do NOT run R-C and `820-review-nits` in the same
  concurrent lane wave.
- **Scope:** the gating decision in `test_load_all_addon_modules`. / out of scope: the
  sibling smoke tests (already gate); the dependency-skip / crash classification
  (`_check_dependencies`, subprocess isolation — keep).
- **Repro instruction:** introduce a synthetic addon module that raises a non-
  dependency error at import; run `python3 -m unittest discover -s tests -p
  "test_*.py" -t .` — `test_load_all_addon_modules` still passes (only logs).
- **Test file:** `tests/test_plugin_registration.py` — add a case proving the chosen
  contract: either a synthetic always-failing module is detected and the test fails,
  or an assertion that the advisory contract holds (the warning is emitted, the gate
  does not block). Must fail pre-fix if gating is chosen; pass post-fix.
- **Citations expected:** Do cites `tests/test_plugin_registration.py`
  (`test_load_all_addon_modules` assertion / `LOG.warning` lines) on the PR branch.
- **Prior-art check (triage cycles):** review finding R-C; the sibling smoke tests in
  the same file are the gating reference. No prior fix.
- **Disposition hint:** likely-fix (small; one gating decision + a proving test).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle. The PR MUST NOT be marked ready before
sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Rejected: the gating C4 never ran and the C2 repro is inadequate — both fail. Carry-forward for the next Do: - C4 (verification gap): run-verify.sh failed with `tests/test_plugin_registration.py: No such file or directory`. The patch targets addons-source and the verify harness ran against a checkout without that tests/ tree, so red→green was never executed. Rebuild/verify in a checkout that actually contains the addons-source tests/ tree (re-sync first, as with the sibling #820 bundles). Until then C4 is unproven. - C2 (repro inadequacy — the substantive one): the regression test TestPluginLoadingGate only unit-tests the NEW helper hard_load_failure_message; it never drives the defective production path test_load_all_addon_modules. Pre-fix the helper did not exist, so the test would error on collection/import, not go red on the silent-pass defect. The brief's repro (synthetic always-failing module → test_load_all_addon_modules fails) is unmet. The next attempt must prove the gate end-to-end on the actual production path, not just the extracted helper. - T5 / scope: the patch adds a new module tests/plugin_load_gate.py beyond the brief's stated edit surface (tests/test_plugin_registration.py). Defensible extract-for-testability, but call it out and confirm it is in-scope. - T5 / disposition: builder chose the *gate* contract over the brief's permitted *documented-advisory* alternative — confirm gate is intended in the next pass. - T3 deltas (Sqlite 6.1 export; SmokeTest.setUpClass on GUI-smoke + addon-E2E) are decorrelated from a tests/ gating change — environmental/baseline drift, no need to chase.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — error: tests/test_plugin_registration.py: No such file or directory
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Failing gate: T3 runtime: GUI interface smoke (launch + open tree, headless dogtail) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- Failing gate: T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: Discontinue Do rebuilds — do NOT re-attempt the build unchanged; it will fail C4 a third time for the identical structural reason. Root cause of the repeated C4 failure is NOT the patch (the gate design is sound and iter-2 fixed iter-1's C2 objection by driving the real production method). It is an engine capability gap: `tests/test_plugin_registration.py` is introduced by the *unmerged* PR #820 and does not exist in upstream addons-source, while addon-mode `run-verify.sh` applies patches against the upstream `addons-source-6.0/6.1` worktrees (maintenance/gramps60/61). So C4 (red→green) is unprovable in the current harness — hence the identical `tests/test_plugin_registration.py: No such file or directory` in both iterations. The whole 820 family (all sub-issues are updates to PR #820) is blocked on this: the engine needs the ability to verify an addon patch against the PR #820 branch (`feature/ci-cd-pipeline-upstream` on `eduralph/addons-source`) — e.g. an addon analog of the core "essential line" worktree, or a configurable per-bundle base ref. That is out-of-band engine work (engine issue + PR, not a PDCA bundle), recorded as a §10 Act candidate. Plan action: park this bundle pending that engine capability; do not loop Do.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — error: tests/test_plugin_registration.py: No such file or directory
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Failing gate: T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix) (advisory) — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- Failing gate: T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
