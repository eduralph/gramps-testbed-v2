# Running PDCA in parallel lanes (gramps-testbed-v2)

> **Status: DESIGN — not implemented.** This is a runbook/spec, not a description of
> working machinery. What exists today: `pdca batch` (strictly serial, one bundle at a
> time), the C4 apply→test→trap-restore, `make worktrees`, and the refuse-on-dirty
> guards. What does **not** exist: lanes, `new-lane.sh`, `scatter-briefs.sh`, the
> `PDCA_LANES` worker pool, and the automated cross-fix merge re-gate. Sections below
> that reference scripts "(to add)" or "lanes" describe intended behavior, not current.

> Instance realization of the template doctrine
> `PCDA/quality-cycle/09-parallel-lanes.md`. Everything here is instance-side (engine
> scripts + this runbook); the `pdca-harness` template needs no change for it.
>
> Prereqs already in place in this testbed: `run-verify.sh` derives
> `WORKSPACE="$REPO_ROOT/.."` **relatively**, the target checkouts are **siblings** under
> `$WORKSPACE`, containers are **PID-named** (`grampstest-$$-$leg`), and the runner
> **refuses to patch a dirty checkout** — a loud-failure backstop against silent tangling.

## The model in one line

The bundle (`results/issue_<id>/`) is already isolated, so concurrency is safe once every
*shared mutable resource* a cycle touches **outside** its bundle (the target checkout, the
runner's containers) is private to a lane. Correctness *across* the parallel results is a
**separate** problem — two patches each green in isolation can still conflict when merged —
solved by **lane planning** (up front) and the **merge re-gate** (at the end), never by
isolation alone. See the doctrine for the full rationale.

## 1. The lane unit

A **lane** is a self-contained `$WORKSPACE`: its own testbed copy **plus** its own `gramps`
/ `addons-source` checkouts as siblings. Because every path derives from the script's own
location, a relocated `$WORKSPACE` just works.

```
~/lanes/lane-A/{gramps-testbed-v2, gramps, addons-source, gramps-6.0, gramps-6.1, …}
~/lanes/lane-B/{…}
```

## 2. `engine/scripts/new-lane.sh` (to add) — spec

Create an isolated lane cheaply:

1. `mkdir -p <lane-parent>`.
2. **Reference-clone the siblings** so a lane costs a working tree, not a full clone:
   `git clone --reference <primary>/gramps  <upstream-or-primary>/gramps  <lane>/gramps`
   (same for `addons-source`). `--reference` borrows the primary's object store via
   `alternates` — keep the primary around; don't aggressively `gc`/delete it.
3. **Place the testbed**: `git clone <primary>/gramps-testbed-v2 <lane>/gramps-testbed-v2`
   (or `cp -r`).
4. **Create the per-version worktrees *locally*** in the lane:
   `cd <lane>/gramps-testbed-v2 && make worktrees`. **Never `cp` worktrees** from another
   lane — their `.git` is an absolute `gitdir:` pointer and would cross-link back to the
   source (the one real trap).
5. **`make setup`** in the lane (writes a self-located `settings.local.json` pointing at
   the lane's own siblings).
6. **Print the two manual steps** the script can't do: accept the one-time folder *trust*
   for `<lane>/gramps-testbed-v2` on first interactive launch (global `~/.claude.json`),
   and the **issue-id range** assigned to this lane.

A `make lane DIR=~/lanes/lane-B` target can wrap it.

## 3. Lane assignment — by code locality (the doctrine's rule)

**Do not shard by id round-robin.** Group issues whose fixes touch the **same area** into
the **same** lane (they run serially there, so a later fix sees the earlier one);
parallelize only across lanes touching **disjoint** areas. The information is already at
hand from Plan's root-cause analysis (which files/module each fix touches). When the areas
can't be predicted, prefer fewer/broader lanes and lean on the merge re-gate (§6).

## 4. Plan once, then scatter briefs

- Run **one** batch Plan session (`make flow CSV=…`) to brief all issues — it's
  interactive, so keep it single.
- **`engine/scripts/scatter-briefs.sh` (to add)**: copy each `results/issue_<id>/brief.md`
  into the owning lane's `results/`, per the §3 locality assignment (not blind
  round-robin). Bundles are just files, so this is a plain `cp` per issue.

## 5. Fan out the unattended band

In each lane, drive the already-briefed issues with **no Plan beat**:
`cd <lane>/gramps-testbed-v2 && make batch IDS="<this lane's ids>"`. These are headless
(Do + gates + reviewer) and run side by side. Each lane's `pdca` is internally sequential,
so **lanes ≈ concurrent gate suites** — bound the number of lanes you launch to host
capacity and the shared model-API rate limit (tune per host; not a fixed number). No
engine change is needed for isolation: each lane's per-version worktrees and PID-named
containers are already private because the whole `$WORKSPACE` is separate.

## 6. Converge: sign-off, then the integration re-gate

- **Sign-off is per lane** (independent copies → independent cheap-first queues); attend
  them in turn. This is the ergonomic cost of full copies versus a single-workspace
  in-driver fan-out — acceptable for now.
- **Validate the combination at the merge boundary, not in the lane.** Each accepted
  bundle publishes its own `fix/<id>` draft PR. Correctness-under-combination is
  established there: GitHub surfaces merge **conflicts**, and CI runs the repo-scoped
  re-gate (`pdca gates` over the working tree — the same command, single-sourced) on the
  **merge result**. A per-lane green says only "correct on its own"; the merge re-gate is
  what says "mergeable with the others." Resolve any conflict/failure at the PR — not by
  re-opening a lane.

## 7. Operational guardrails

- **Build the Docker image once** (`gramps-testbed:ubuntu-$gv`) — shared read-only across
  lanes; don't rebuild per lane.
- **Disjoint ids per lane** — the single rule that prevents duplicate `fix/<id>` branches
  / PRs on the shared remote.
- **No engine changes for naming/isolation** — PID-named containers and the
  refuse-on-dirty guard already make concurrent runs safe (a refusal is the loud-failure
  backstop if two lanes ever shared a tree — which should never happen with separate
  `$WORKSPACE`s).

## 8. Verification (before relying on it)

Spin up 2 lanes with locality-disjoint ids and run both `make batch` concurrently:

- **Runtime isolation:** each lane's gramps worktree only ever holds its own patch; the
  refuse-on-dirty guard never trips; `docker ps` shows distinct `grampstest-<pid>-*`.
- **Cheap disk:** `du -sh` a `--reference` lane ≈ a working tree, not a full clone.
- **Integration:** combine the two accepted patches; the working-tree re-gate flags a
  conflict if one exists, passes if clean.

## What stays out of scope

The 3 Raspberry Pis don't help here — they can't run the Docker/GTK gates and the
orchestration they *can* run isn't the bottleneck. Keep them for a lightweight project
(where a Pi is a full self-sufficient lane) or an always-on dashboard/queue role. The
in-driver worker pool (one workspace, `PDCA_LANES` thread pool) is the future upgrade if
the per-lane sign-off ergonomics or disk become a pain point.
