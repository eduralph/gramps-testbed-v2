# Running PDCA in parallel lanes (gramps-testbed-v2)

> **Status: two mechanisms, one implemented.**
> - **In-driver worker pool — IMPLEMENTED (§0, the primary path).** `PDCA_LANES=N` /
>   `pdca batch|flow --lanes N` runs N bundles concurrently in **one** workspace; each
>   worker is pinned to a slot and the gates patch that lane's own per-version worktree
>   (`gramps-6.1-lane$PDCA_LANE`, built by `make worktrees LANES=N`). The cross-fix merge
>   re-gate (`pdca gates --working-tree`) already exists.
> - **Full-copy lanes — DESIGN, not built (§1–§8 below).** A separate `$WORKSPACE` per
>   lane with `new-lane.sh` / `scatter-briefs.sh` / `make lane`: the heavier alternative,
>   kept here as a runbook. Sections that reference scripts "(to add)" describe intended
>   behavior, not current. Prefer §0 unless per-lane disk / sign-off ergonomics force a
>   full split.
>
> What exists today regardless: `pdca batch` (serial when `lanes=1`), the C4
> apply→test→trap-restore, `make worktrees`, and the refuse-on-dirty guards.

## 0. In-driver worker pool (the implemented path)

The driver (`pdca-harness` v0.14.0+) can fan the **unattended Do+Check band** out across a
worker pool while Plan, sign-off, publish and Act stay serial. Set the pool size with
`[driver].lanes` in `pdca.toml`, or override per run with `PDCA_LANES=N` /
`pdca batch|flow --lanes N`. `lanes = 1` (the default) is the strictly-serial driver,
unchanged.

Each worker thread is pinned to a fixed slot `0..N-1` and exposes it to every gate command
as `$PDCA_LANE`. The instance side honors the pdca.toml contract — *a gate that touches a
shared mutable resource outside its bundle MUST name it by `$PDCA_LANE`*:

- **Per-version worktrees are lane-private.** The runners
  (`engine/scripts/ubuntu/run-verify.sh`, `run-addon-{unit,interface}.sh`) derive
  `LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"` and patch `gramps-6.{0,1}$LANE_SFX` /
  `addons-source-6.{0,1}$LANE_SFX` / `gramps-<ver>-essential$LANE_SFX`. Serial runs (no
  `$PDCA_LANE`) get the bare worktrees, byte-for-byte as before.
- **Create the lane copies:** `make worktrees LANES=N` (and `make essential-worktrees
  LANES=N` if any bundle may hit the essential fallback) adds the `-lane0…-lane{N-1}`
  worktrees alongside the bare set. They are extra `git worktree add` of the same
  `upstream/maintenance/*` ref — objects shared with the primary, disk ≈ a working tree
  each (the in-driver model's payoff over full `$WORKSPACE` copies).
- **Containers need no lane scoping.** Each gate runs as a fresh subprocess, so the
  PID-named `grampstest-$$-…` is already unique per gate invocation even across pool
  threads; the shared resource is the filesystem worktree path, which the suffix isolates.

Converge exactly as in §6: each accepted bundle opens its own `fix/<id>` PR and CI runs the
single-sourced merge re-gate `pdca gates --working-tree` on the merge result.

Run it: `make worktrees LANES=2 && PDCA_LANES=2 make batch IDS="<a> <b>"` (locality-disjoint
ids per §3). The §1–§8 full-copy runbook follows for the heavier, fully-isolated option.

> Instance realization of the template doctrine
> `PCDA/quality-cycle/09-parallel-lanes.md`. Everything here is instance-side (engine
> scripts + this runbook); the `pdca-harness` template needs no change for it.
>
> Prereqs already in place in this testbed: `run-verify.sh` derives
> `WORKSPACE="$REPO_ROOT/.."` **relatively**, the target checkouts are **siblings** under
> `$WORKSPACE`, containers are **PID-named** (`grampstest-$$-$leg`), and the runner
> **refuses to patch a dirty checkout** — a loud-failure backstop against silent tangling.
>
> **Default target is UPSTREAM (since the upstream-default change).** Both core and addon
> C4-verify patch the per-version worktrees `gramps-6.{0,1}` (based on
> `upstream/maintenance/*`), **not** `$WORKSPACE/gramps` — so the shared mutable resource a
> core cycle touches is also lane-private, and the isolation argument below covers it. A
> core bundle that fails on upstream is retried on the lane's own `gramps-<ver>-essential`
> worktree (`engine/essential-fixes.tsv`); each cleared leg is `git clean -fdq`-scrubbed,
> so residue can't tangle a later run in the same lane.

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
~/lanes/lane-A/{gramps-testbed-v2, gramps, addons-source,
                gramps-6.0, gramps-6.1, gramps-6.1-essential,
                addons-source-6.0, addons-source-6.1, …}
~/lanes/lane-B/{…}
```

## 2. `engine/scripts/new-lane.sh` (to add) — spec

Create an isolated lane cheaply:

1. `mkdir -p <lane-parent>`.
2. **Reference-clone the siblings** so a lane costs a working tree, not a full clone:
   `git clone --reference <primary>/gramps  <upstream-or-primary>/gramps  <lane>/gramps`
   (same for `addons-source`). `--reference` borrows the primary's object store via
   `alternates` — keep the primary around; don't aggressively `gc`/delete it.
   **Set the `upstream` remote in each clone** (run `engine/scripts/bootstrap-forks.sh`, or
   `git remote add upstream …`): a reference-clone inherits objects but **not remote
   config**, and step 4's `make worktrees` now fetches `upstream` and bases the per-version
   worktrees on `upstream/maintenance/*` — without the remote the fetch warns and the
   upstream-ref checkout fails.
3. **Place the testbed**: `git clone <primary>/gramps-testbed-v2 <lane>/gramps-testbed-v2`
   (or `cp -r`).
4. **Create the per-version worktrees *locally*** in the lane:
   `cd <lane>/gramps-testbed-v2 && make worktrees` (upstream-based; needs the `upstream`
   remote from step 2). If any of the lane's bundles may hit the essential fallback, also
   `make essential-worktrees` to build the lane's own `gramps-<ver>-essential` from
   `engine/essential-fixes.tsv`. **Never `cp` worktrees** from another lane — their `.git`
   is an absolute `gitdir:` pointer and would cross-link back to the source (the one real
   trap); the same applies to the essential worktrees.
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
  re-gate (`pdca gates --working-tree` — the same impl, single-sourced) on the
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
(where a Pi is a full self-sufficient lane) or an always-on dashboard/queue role.

The in-driver worker pool (one workspace, `PDCA_LANES` thread pool) is now **implemented**
— see §0; it is the default path. The full-copy lanes of §1–§8 stay design-only, the
heavier fallback for when per-lane sign-off ergonomics or disk pressure justify fully
separate `$WORKSPACE`s.
