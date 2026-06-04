# Brief — issue bootstrap-root-depth / bootstrap-forks-workspace-root-off-by-one

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** bootstrap-forks-workspace-root-off-by-one
- **Defect:** `agent-work/scripts/bootstrap-forks.sh` carries the same move-induced off-by-one that `c201b5a` fixed in the 8 platform runners, but was missed (it sits one level up in `agent-work/scripts/`, not `agent-work/scripts/{ubuntu,windows}/`, so it was outside both the prior brief's enumeration and the guard's `RUNNERS` list). Its fixed-depth walk — `TESTBED="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` then `WORKSPACE="$(cd "$TESTBED/.." && pwd)"` — now resolves `TESTBED` to `<repo>/agent-work` (want `<repo>`) and `WORKSPACE` to `<repo>` (want `<repo>/..`). The script then `cd "$WORKSPACE"` and clones `gramps`, `addons-source`, `addons` there, so it places the fork checkouts *inside* the testbed repo instead of as siblings — exactly the layout the now-fixed runners no longer look in. The defect class is therefore not fully closed: `c201b5a` moved the breakage from the runners onto the script that sets up the layout they depend on.
- **Success criterion:** `bootstrap-forks.sh` resolves `TESTBED` to the repo root and `WORKSPACE` to the repo's parent (the dir that will hold the sibling `gramps/` checkout); AND the regression guard covers *every* tracked `agent-work/scripts/**/*.sh` that assigns `WORKSPACE`/`TESTBED` (discovery by pattern, not a hand-maintained list), so a future script with the fragile walk fails the guard instead of slipping through as `bootstrap-forks.sh` did.
- **Repo + branch target:** gramps-testbed @ main (testbed-itself fix, INTEGRATION §2)
- **Scope:** Replace the fixed-depth walk in `bootstrap-forks.sh:35-36` with the `git rev-parse --show-toplevel` resolution already established by `c201b5a` (match `agent-work/scripts/ubuntu/rebuild-image.sh:20-21` verbatim — `TESTBED` from git top-level, `WORKSPACE="$(cd "$TESTBED/.." && pwd)"`), and generalize `tests/test_runner_workspace_root.py` to discover all `agent-work/scripts/**/*.sh` that assign `WORKSPACE`/`TESTBED` rather than the explicit `RUNNERS` tuple. / out of scope: re-litigating git-rev-parse vs. deepening the walk (settled by `c201b5a` — match it); `verify-pr.sh` and `run-batch.sh` (verified to compute no workspace root); any behavioural change to what the script clones or where, beyond correcting the root.
- **Repro instruction:** On `main`, from a checkout at `<ws>/gramps-testbed`, run `./agent-work/scripts/bootstrap-forks.sh` (or just evaluate its root lines): `WORKSPACE` resolves to `<ws>/gramps-testbed` and the `git clone` at line 77/88-94 would drop `gramps/` at `<ws>/gramps-testbed/gramps` instead of `<ws>/gramps`. Equivalently: `cd "$(dirname agent-work/scripts/bootstrap-forks.sh)/.." && pwd` prints `<repo>/agent-work`, not `<repo>`.
- **Test file:** tests/test_runner_workspace_root.py (extend the existing guard; it must fail pre-fix once `bootstrap-forks.sh` is in coverage, and pass post-fix)
- **Citations expected:** Do must cite path:line on main — `agent-work/scripts/bootstrap-forks.sh:35-36` (the walk), `:37,:88-94` (the `cd "$WORKSPACE"` + clones that consume it), `agent-work/scripts/ubuntu/rebuild-image.sh:20-21` (the pattern to match), and `tests/test_runner_workspace_root.py:44-53` (the `RUNNERS` list being generalized).
- **Disposition hint:** likely-fix (same root cause as the verified `c201b5a`; this completes the defect class and hardens the guard against a third miss)

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
