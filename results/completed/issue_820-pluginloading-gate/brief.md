# Brief — issue 820-pluginloading-gate / make TestPluginLoading gate, not silently pass

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Decomposed from `results/issue_pr820-ci-checkin/` (review finding R-C). Tracks
> addons-source PR #820 (CI/CD pipeline harness). Re-planned after two C4-only
> rejections: the fix design was judged SOUND both times; the block was a harness
> gap (the PR-#820 file is absent from clean upstream, so run-verify could not find
> it). That gap is now CLOSED — `engine/fork-bases.tsv` + `make fork-worktrees` build
> `addons-source-6.0-fork` at `feature/ci-cd-pipeline-upstream`, and run-verify.sh
> honors the `Verification base` field (issue #96). C4 can now execute red→green.

- **Slug:** 820-pluginloading-gate
- **Defect:** on the PR #820 branch, `TestPluginLoading.test_load_all_addon_modules`
  (`tests/test_plugin_registration.py:163`) accumulates `hard_failures` (init `:168`,
  appended `:207`) for genuine non-dependency load failures, but its **only** action on
  them is `LOG.warning(...)` (`:224-229`). The method's sole assertion is
  `assertGreater(len(plugins), 0)` (`:166`). A real addon that fails to load therefore
  makes the test pass silently — unlike the two sibling smoke tests in the same file
  (`TestImportPluginSmoke` `self.fail` `:258`, `TestExportPluginSmoke` `self.fail`
  `:290`), which gate on their findings. The test names a failure class
  (`hard_failures`) it cannot fail on: an always-pass-by-omission gate.
- **Success criterion:** a non-dependency hard load failure makes
  `test_load_all_addon_modules` **fail** (the test gates, like its two siblings); the
  always-pass-by-omission state is gone. Demonstrated red→green: with one synthetic
  always-failing addon injected, the production method raises its `failureException`
  with the fix applied and does **not** without it — proven by `run-verify.sh` against
  the fork verification base (no longer the unverifiable state of the prior two
  iterations).
- **Invariant to restore:** a CI test that names a failure class either **gates** on it
  or **declares itself advisory** — no test silently always-passes while presenting
  itself as a loadability check. Stated over the category (every gating test in this
  suite), not this one method. Source: `docs/principles.md` and global CLAUDE.md ("a
  green mechanical check is not a correctness verification"); the two sibling smoke
  tests in the same file are the in-repo precedent that this class of test gates.
- **Disposition (settled — gate, not advisory):** the original brief permitted *gate*
  **or** *documented-advisory*; the human's iteration-2 sign-off and the invariant both
  resolve to **gate**. Making it advisory would leave one file with two contradictory
  contracts for "an addon won't load" (the two siblings already `self.fail`). Do
  implements the gate; the advisory alternative is closed.
- **Repo + branch target:** gramps-project/addons-source @ `maintenance/gramps60` via
  `feature/ci-cd-pipeline-upstream`; tested on the `eduralph/addons-source` fork
  (maintainer cherry-picks gramps60 → gramps61).
- **Verification base:** origin/feature/ci-cd-pipeline-upstream
- **Surfaces:** data (CI test; no GUI).
- **Depends on:** none.
- **Conflicts with:** 820-review-nits — both edit `tests/test_plugin_registration.py`
  (nits (b)/(c) touch `_get_addon_plugins` at `:74`/`:76`, still unmerged on the
  branch), so the two MUST NOT run in the same concurrent lane wave (git-apply
  collision on the shared file).
- **Scope:** make `test_load_all_addon_modules` fail on non-dependency hard load
  failures instead of only logging them — the single gating decision. / out of scope:
  the two sibling import/export smoke tests (already gate); the dependency-skip and
  subprocess-crash classification (`_check_dependencies`, the per-plugin subprocess
  isolation, `dep_skips`/`crash_failures` advisory warnings — keep as-is); the
  `820-review-nits` edits to the same file.
- **Repro instruction:** on `addons-source-6.0-fork` (built by `make fork-worktrees`),
  inject one synthetic addon module that raises a non-dependency error at load; run the
  suite (`python3 -m unittest tests.test_plugin_registration` under the addon env, xvfb
  + `gi_bootstrap`). Pre-fix `test_load_all_addon_modules` still passes (the failure is
  only `LOG.warning`-ed); post-fix it fails on the synthetic hard failure.
- **Test file:** `tests/test_plugin_load_gate.py` — the regression case. It MUST drive
  the **real production method** `TestPluginLoading.test_load_all_addon_modules` (the
  iteration-1 reject: testing the decision in isolation is a parallel copy, not the
  production path; principles §3.4), asserting it raises its `failureException` when a
  synthetic hard failure is injected at the production module's own load seams.
  Testable-seam requirement (forced, not optional): because the code under fix is
  itself a `test_*.py` file, `run-verify.sh` (line 130) has **no non-test production
  file to revert** for its red leg and the C4 gate cannot run on a test-only patch — so
  the gating decision is extracted into a **non-`test_*.py`** unit that BOTH production
  and the regression route through (the same unit, not a mirror). Keep the regression
  in its own module so the C4 green leg does not boot the full registry-backed real
  test (flaky on the minimal image's missing GTK icon theme — observed `stock_link`
  GError); the real integration test still runs in actual PR #820 CI.
- **Citations expected:** Do cites `tests/test_plugin_registration.py` lines on the
  fork branch (`test_load_all_addon_modules:163`, sole assertion `:166`, the
  `LOG.warning` hard-failure block `:224-229`) for the production edit, and the new
  module(s) it adds.
- **New/removed files:** the fix adds test-tree `.py` modules (a regression module and
  the extracted non-test gating unit). N/A for POTFILES: addons-source carries no
  top-level `po/POTFILES.{in,skip}`, and the POTFILES-registration MUST is core-only
  (INTEGRATION §4); the added modules carry no translatable strings.
- **Prior-art check (triage cycles):** searched by file path — the file does not exist
  on clean `upstream/maintenance/gramps60` (introduced wholesale by the unmerged PR
  #820), so there is no upstream history to collide with; review finding R-C is the
  origin; the two sibling smoke tests in the same file are the gating reference. No
  prior fix to this gating contract.
- **Mantis:** none — addons-source PR #820 (CI/CD pipeline) follow-up; decomposed from
  `results/issue_pr820-ci-checkin` finding R-C. No tracker ticket (a Mantis reference
  is optional for addons-source, INTEGRATION §1); the T4 trailer MUST is waived and the
  PR body states the PR #820 origin.
- **Disposition hint:** likely-fix (small; one gating decision + the seam C4 requires,
  now verifiable on the fork base).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration history — carry-forward (do NOT re-litigate the settled calls)

- **Iteration 1 (rejected):** C2 — the regression only exercised the extracted decision
  in isolation, never the production path. **Settled:** the regression now drives the
  real `test_load_all_addon_modules` (Test file field above). Do not regress to testing
  the unit alone.
- **Iteration 2 (rejected, parked):** the fix design was judged **sound** (gate drives
  the real production method); the only failing gate was **C4**, which errored
  `tests/test_plugin_registration.py: No such file or directory` because the harness
  applied the patch against clean upstream worktrees that lack the PR-#820 file. The
  bundle was parked pending an engine capability to verify against the fork PR branch.
  **Settled:** that capability now exists (`engine/fork-bases.tsv` 6.0 row +
  `make fork-worktrees` → `addons-source-6.0-fork`; run-verify honors `Verification
  base`). The corrective is simply to run C4 against the fork base and demonstrate
  red→green — not to redesign the fix.
- Both prior attempts are preserved in `iteration-v1/` and `iteration-v2/`
  (patch.diff, build-notes.md, SUMMARY.md, check-*). The carried regression module is
  in this bundle's `tests/`.
