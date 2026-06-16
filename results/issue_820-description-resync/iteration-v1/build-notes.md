# Build notes — 820-description-resync

## What this bundle delivers

A documentation-only change: the rewritten body for **PR #820**
(gramps-project/addons-source, head `feature/ci-cd-pipeline-upstream`, base
`maintenance/gramps60`). No repo file changes, no test — exactly as the brief
specifies (`Test file: no test — documentation change`; `Repo + branch target:
… PR #820 description text (no branch code change)`).

Artifacts:
- `pr-820-description.md` — the full rewritten body (the deliverable; this is what
  goes into the PR description at the publish step).
- `pr-820-description.OLD.md` — the body as it stood at build time, captured via
  `gh pr view 820 --json body`, kept so the diff is reproducible.
- `patch.diff` — unified diff OLD→new of the body text. There is no
  source-tree diff because the description is not a repo file; a normal
  `git`-apply patch is not meaningful here, so the "patch" is the prose delta a
  reviewer reads.

## Why these three changes (the Success criterion)

Success criterion: the description's gate policy, file list and commit summary
match HEAD's tree and `ci.yml`'s actual `continue-on-error` settings. I verified
each against HEAD (`refs/tmp/pr820` = `1466491ab`) rather than recalling:

### (1) Gate policy — only `addon-structure` is advisory
`git grep -n continue-on-error … ci.yml` at HEAD returns a single hit:

    .github/workflows/ci.yml:111:    continue-on-error: true

Line 111 sits inside the `addon-structure` job (job header at `ci.yml:106`,
comment at `ci.yml:109-110`: "Non-blocking until the four addons missing
po/template.pot are fixed in a follow-up PR"). Lint (`ci.yml:56`), compile-check
(`:148`), unit-test-linux (`:192`), unit-test-windows (`:379`), integration-test
(`:563`) and build (`:722`) carry **no** `continue-on-error`, so they default to
blocking.

The old body had this inverted two ways: it listed Lint + both Unit-test jobs +
Addon Structure as advisory, and Compile/Integration/Build as the only blocking
set. It also carried a now-false paragraph ("The four advisory gates are
currently red…"). Both were flipped by commits `d265612` (lint blocking) and
`0dd3f1b` (both unit-test jobs blocking) — confirmed in the log. I corrected the
blocking/advisory lists, rewrote the trailing paragraph to state the lint/
unit-test backlog is cleared, and kept the genuine remaining advisory
(addon-structure, pending the four `po/template.pot` gaps) — matching the
in-file comment.

### (2) File list — six omitted paths added
`gh pr view 820 --json files` lists 15 files; the old body named only 9. The six
omitted, all confirmed present at HEAD via `git ls-tree -r refs/tmp/pr820`:
- `.github/CI-MAINTAINER.md` — maintainer runbook (added `3b2a947`).
- `.github/scripts/addon_system_deps.py` — system-dep single source of truth
  (`requires_gi`/`requires_exe` → apt/conda packages); module docstring lines
  1-30 describe the design and apt-vs-conda asymmetry.
- `.github/scripts/gi_bootstrap/sitecustomize.py` — GI-version pin shim for
  subprocess-loading steps (docstring lines 1-18).
- `.github/scripts/run_addon_tests.py` — per-addon runner: GI bootstrap +
  per-module timeout + honest skip accounting (docstring lines 1-22).
- `tests/test_addon_dependencies.py` — undeclared-sibling-import detector,
  Mantis 13707 bug class (header lines 21-26).
- `CONTRIBUTING.md` — the unreleased-branch CI note (diff at lines 1094+; a
  +12-line insertion).

I grouped the three scripts under a new "Shared CI scripts" heading,
`test_addon_dependencies.py` under the existing test-harness heading, and the two
docs under a new "Docs" heading. Each description is drawn from the file's own
docstring/header, not invented.

### (3) Commit summary — all 21 commits
`git rev-list --count upstream/maintenance/gramps60..refs/tmp/pr820` = 21; the
old table had 7 rows ending at `205b21c`. I replaced it with all 21, dates from
`git log --date=short`, ordered as in the log. SHAs use 7-char abbreviations to
match the body's existing style; I confirmed `d265612`, `0dd3f1b`, `9927626`
resolve unambiguously with `git rev-parse --short=7`.

## Adjacent corrections made (kept minimal)
While the table/file-list edits forced me through the `ci.yml` job bullets, two
were stale and would mislead a reviewer about CI structure (still within the
"gate policy / commit summary match HEAD" intent):
- "seven jobs" → "eight jobs", adding the **Setup** job (`ci.yml:34`, added by
  `9a91d89`) that derives the image tag / `make.py` suffix from the branch ref.
- Unit-test-linux now runs via `run_addon_tests.py` (not bare dotted-path
  loading); integration adds `tests/test_addon_dependencies.py`. The Dockerfile
  bullet dropped the stale "(pip)" / `dbf` (removed in `8d2654a`) and notes the
  PyPI-vs-snapshot install.

I deliberately did **not** touch the "Local reproduction" commands, the Companion
PRs tracker, or any prose unrelated to the three named defects — out of scope
per the brief ("only the *description* is stale … no change to ci.yml/the
wiring").

## Why no code patch / no test, and no red→green run
The brief's `Test file` is explicit: documentation change, no test
(principles §1.1). The C4 `run-verify.sh` gate has nothing to drive — there is no
production code path and no test module. Manual verification is the three repro
commands in the brief, all run here:
- `grep continue-on-error ci.yml` → `addon-structure` only ✓
- PR `files` (15) vs body list → six were missing, now present ✓
- `log --oneline` range count → 21 vs body's 7 ✓

## STOP discipline
I did **not** run `gh pr edit` / mutate the live PR body, and did not push or open/
ready any PR. Applying the new body to PR #820 is the human's publish step after
Check sign-off. The fetched `refs/tmp/pr820` ref is local-only (read for
verification); it can be deleted with `git update-ref -d refs/tmp/pr820`.
