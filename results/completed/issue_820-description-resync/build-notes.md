# Build notes — 820-description-resync (Iteration 2)

> Withheld from the reviewer. Rationale + what I verified, for the human at sign-off.

## What the deliverable is

PR #820 is the **upstream** `gramps-project/addons-source` PR (verified:
`gh pr view 820 --repo gramps-project/addons-source` → `OPEN`, head
`feature/ci-cd-pipeline-upstream`, url …/pull/820). It ships **no branch code change**
— it *is* the CI pipeline, but the defect here is purely that the PR *description* has
drifted from the branch HEAD. So `patch.diff` is a prose diff of the PR body, not a
repo-file patch. There is **no regression test**: per the brief's *Test file* field,
"no test — documentation change (principles §1.1)". I did **not** fabricate a test to
make C4 green; doing so would be a green mechanical check on an adjacent artifact, not
proof of the real end result.

The real proof for a prose deliverable is the brief's own *Repro instruction* /
*manual verification*: the three commands, plus a visual diff of the rewritten body
against HEAD. I ran all three against **live** state (not the stale local tree the
Iteration-1 carry-forward flagged).

## Why Iteration 2 differs from Iteration 1

The carry-forward did **not** fault the prose (review found C1/C3/C5/T4 PASS and the
three drifts correctly resolved). It iterated because Iteration 1 was built against a
**stale + dirty** testbed tree, so the success criterion — "matches HEAD
(then 1466491ab)" — could not be *provably* re-confirmed, and HEAD "may have moved".

What I re-established this round, against freshly-fetched remotes:

- `git -C addons-source fetch origin feature/ci-cd-pipeline-upstream` → HEAD is
  **still `1466491ab`** ("ci(windows): document gramps-vs-branch series caveat"). HEAD
  did not move, so the Iteration-1 content remains on-target — but I re-derived every
  claim from HEAD rather than trusting that.
- The live PR body (`gh pr view 820 --repo gramps-project/addons-source --json body`)
  is **byte-identical** to `pr-820-description.OLD.md` (`diff` → IDENTICAL). So the
  diff's "before" is exactly what reviewers see today.

I adopted the already-present rebuilt body `pr-820-description.md` (it carries one
extra, correct refinement over Iteration 1 — the `environment.yml` line — see below)
and re-verified **every** line of it against HEAD before shipping.

## Verification of each "after" claim against HEAD @ 1466491ab

1. **Gate policy** — `git show …:ci.yml | grep -n continue-on-error` → the *only*
   match is line 111, inside the `addon-structure` job (line 106-111). Jobs `lint`
   (56), `compile-check` (148), `unit-test-linux` (192), `unit-test-windows` (379),
   `integration-test` (563), `build` (722) carry **no** `continue-on-error` → blocking.
   The rewrite's Blocking/Advisory split matches exactly. The flips are real:
   `d2656125e` "CI: make lint job blocking", `0dd3f1b2a` "CI: make unit-test-linux and
   unit-test-windows blocking" are both on the branch.
2. **"eight jobs" + Setup** — job names in `ci.yml`: setup(34), lint(56),
   addon-structure(106), compile-check(148), unit-test-linux(192),
   unit-test-windows(379), integration-test(563), build(722) = **8**. OLD said "seven"
   and omitted Setup; corrected.
3. **File list** — `git diff --stat upstream/maintenance/gramps60...HEAD` → 15 files.
   All six previously-omitted paths exist at HEAD (`git ls-tree`): `.github/CI-MAINTAINER.md`,
   `.github/scripts/addon_system_deps.py`, `.github/scripts/gi_bootstrap/sitecustomize.py`,
   `.github/scripts/run_addon_tests.py`, `tests/test_addon_dependencies.py`, and the
   `CONTRIBUTING.md` edit (12-line add). Every one of the 15 changed files now appears
   in a "What's in the PR" bullet (CI infrastructure / Shared CI scripts / Shared test
   harness / TMGimporter split / Docs).
4. **Commit table** — `git log --reverse upstream/maintenance/gramps60..HEAD` → **21**
   commits. The rewritten table lists all 21 in branch (topological) order with their
   real author dates and faithful summaries; OLD stopped at `205b21c` (7 rows). Short
   SHA `9927626` = `99276264a` (Dockerfile GRAMPS_SERIES arg) confirmed.
5. **`environment.yml` refinement** (the one line beyond Iteration 1) — HEAD's
   `.github/environment.yml` pins only `gramps>=6.0,<6.1` + `orjson` under `pip:` and
   carries a comment "Addon runtime deps (dbf, networkx, lxml, …) are installed at CI
   runtime by ci.yml's auto-derive step". So the new wording ("only the stable base
   (`gramps` + `orjson`) comes from pip; … `dbf` dropped in `8d2654a`") is accurate;
   the OLD "`gramps`/`orjson`/`dbf` come from pip" is stale. Corroborated by the
   Dockerfile: `RUN pip install … PyGObject pycairo orjson ruff` (no `dbf`), so the
   Dockerfile bullet dropping `dbf` from the tooling list is also correct.
6. **Integration Tests runs both test files** — the integration-test job's step runs
   `python3 -m unittest discover -s tests -p "test_*.py"`, which discovers both
   `tests/test_plugin_registration.py` and `tests/test_addon_dependencies.py`; the
   rewrite naming both is accurate.

## C4 / T3 gates (the carry-forward's "failing gates")

- **C4** — `run-verify.sh` reports "patch ships no addon test (test_*.py) to verify".
  That is the *expected* outcome of the brief-sanctioned no-test exemption for a
  documentation change, not a defect — the carry-forward itself states "C4 is a
  non-blocker … not a reason to change anything." I deliberately ship no test. (I could
  not execute the Docker-backed runner in this sandbox without interactive approval;
  the outcome is deterministic and identical to the prior run on an identical-kind
  prose patch.)
- **T3 deltas** (Sqlite `ExportSQLTestCase::test_export_sq`, `interface.test_smoke`
  `setUpClass`) — these are whole-suite advisory runtime gates against the *unmodified*
  checkout; a PR-description prose change touches no repo file and cannot cause or fix
  them. They match the known environmental baseline signature documented in
  `docs/INTEGRATION.md` §3 (the core-suite segfault / GUI-smoke `_Glade__dirname`
  reds). Not addressable by, and not attributable to, this contribution.

## Rejected alternatives

- **Edit the live PR body via `gh pr edit` now.** Rejected — STOP discipline: the
  publish/ready steps are the human's at Check sign-off. The bundle ships the resynced
  text + diff for the human to apply.
- **Also fix the stale comment in the Dockerfile (line 11 still says "ruff, dbf …").**
  Rejected — out of scope per the brief ("any change to `ci.yml`, the workflows, or the
  gate wiring … the *state* is correct; only the *description* is stale"). The actual
  pip install already excludes `dbf`; the description must match the image's *behaviour*,
  which it now does. The in-file comment is a separate, code-side nit for the pipeline
  PR, not this prose resync.
- **Re-order the commit table by strict date.** Rejected — the branch has rebase
  artifacts (05-19 commits are ancestors of 05-18 commits), so strict date order would
  misrepresent the actual branch sequence. Branch/topological order (what `git log`
  shows) is the faithful, reviewer-mappable representation; each row keeps its true
  author date.

## Files in this bundle
- `patch.diff` — before (live #820 body) → after (resynced, matches HEAD 1466491ab).
- `pr-820-description.md` — the full "after" body (apply target for the human).
- `pr-820-description.OLD.md` — the live "before" body (== `gh pr view 820`).
- No test file — documentation change, principles §1.1 (intentional).
