# Brief — issue 820-description-resync / resync PR #820 description with HEAD

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Decomposed from `results/issue_pr820-ci-checkin/` (finding R-A). Tracks
> addons-source PR #820 (Mantis FR 9393). Prose-only; do first.

- **Slug:** 820-description-resync
- **Defect:** PR #820's description is materially out of sync with HEAD of
  `feature/ci-cd-pipeline-upstream`: (1) the **Gate policy** section lists Lint plus
  both Unit-test jobs as advisory (`continue-on-error: true`), but in `ci.yml` only
  the `addon-structure` job carries `continue-on-error: true` — lint and the
  unit-test jobs are **blocking** (flipped by commits `d2656125`, `0dd3f1b2`); (2)
  the **What's in the PR** list omits six shipped files: `.github/CI-MAINTAINER.md`,
  `.github/scripts/addon_system_deps.py`, `.github/scripts/gi_bootstrap/sitecustomize.py`,
  `.github/scripts/run_addon_tests.py`, `tests/test_addon_dependencies.py`, and the
  `CONTRIBUTING.md` edit; (3) the **commit table** stops at `205b21c` (7 of the 21
  commits). A reviewer acting on the body mis-judges what blocks merge and what the
  PR contains.
- **Success criterion:** the PR #820 description's gate policy, file list, and commit
  summary match HEAD's tree and `ci.yml`'s actual `continue-on-error` settings — a
  reviewer reading only the body draws correct conclusions.
- **Repo + branch target:** gramps-project/addons-source — PR #820 description text
  (no branch code change). Exercised by reading the rendered PR; CI itself is tested
  on the `eduralph/addons-source` fork.
- **Surfaces:** data (documentation; no code, no GUI).
- **Depends on:** none. PR-description prose only — touches no repo files, so it
  conflicts with nothing and can run in any wave, parallel with anything.
- **Scope:** rewrite the PR #820 description prose to match HEAD. / out of scope: any
  change to `ci.yml`, the workflows, or the gate wiring (the *state* is correct; only
  the *description* is stale).
- **Repro instruction:** `grep -n continue-on-error .github/workflows/ci.yml` →
  `addon-structure` only; `gh pr view 820 --json files -q '.files[].path'` vs the
  body's file list; `git -C addons-source log --oneline feature/ci-cd-pipeline-upstream`
  shows 21 commits vs the body's 7-row table.
- **Test file:** no test — documentation change (principles §1.1). Manual
  verification: the three commands above, plus a visual diff of the rewritten body
  against HEAD.
- **Citations expected:** Do references `.github/workflows/ci.yml` `continue-on-error`
  lines and the six omitted paths in the rewritten body (no source-line patch).
- **Prior-art check (triage cycles):** review finding R-A
  (`results/issue_pr820-ci-checkin/`); no prior description fix.
- **Disposition hint:** likely-fix (prose; trivial, high reviewer-trust payoff).

## STOP discipline

Draft only until Check sign-off. The PR MUST NOT be marked ready before sign-off
accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Rebuild on the latest code foundation. This bundle was built/reviewed against a stale tree: local main is 11 commits behind origin/main AND dirty (uncommitted edits to engine/scripts/lib/addon_system_deps.py + addon_python_deps.py). A "description-resync to HEAD" deliverable is only meaningful against the CURRENT HEAD, so the rebuild must happen after gramps-testbed-v2 is synced to latest. Why iterate rather than accept (the change itself is sound): - The advisory review found no defect in the prose rewrite (C1/C3/C5/T4 PASS); the diff correctly resolves the three documented drifts (gate policy, the six restored file entries, 7->21 commit table). - BUT the success criterion is "matches HEAD (1466491ab) and ci.yml's actual continue-on-error settings" (V). That match could NOT be verified against a stale/dirty tree, and HEAD may have moved past 1466491ab. Re-derive the "after" text against the freshly-synced HEAD so the description provably matches it, then re-confirm V (gh pr view 820 --files; git log on the PR branch; the addon-structure-only continue-on-error grep). - C4 is a non-blocker: doc/prose change, no-test exemption under principles §1.1 — not a reason to change anything. Batch note: stop the flow after this batch completes and update gramps-testbed-v2 to origin/main (reconcile the local lib edits first) before any rebuild runs.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — run-verify.sh: patch ships no addon test (test_*.py) to verify
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- Failing gate: T3 runtime: GUI interface smoke (launch + open tree, headless dogtail) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- Failing gate: T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail) (advisory) — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
