# Gramps Testbed v2

A CI/CD harness that runs the **PDCA quality cycle** over Gramps (core + addons),
driven by the Claude CLI. One command takes a tracker issue from a brief all the
way to a human-signed-off, verified fix — `Plan → Do → Check → sign-off → Act` —
pausing only where a human belongs.

The driver is deterministic (state machine + gates + the C6 accept-guard are plain
code); a model is invoked only at the five **leaves**. See [PCDA/quality-cycle.md](PCDA/quality-cycle.md)
for the model and [docs/INTEGRATION.md](docs/INTEGRATION.md) for the gramps specifics.

## Prerequisites

- The **Claude CLI** (`claude`) installed and authenticated.
- **Docker** (the gramps test gates run in a container).
- The sibling fork checkouts next to this repo — `../gramps`, `../addons-source`
  (bootstrap with `./engine/scripts/bootstrap-forks.sh` if missing).
- Python 3.11+ (stdlib only; no install needed — the `Makefile` runs from source).

## Quick start

```bash
make setup              # ONCE: grant Claude read of the workspace + sibling repos
make flow ID=13636      # run the whole cycle for tracker issue 13636
```

Run `make flow` **in a real terminal** — the Plan, sign-off, publish and Act steps
open Claude interactively. The first interactive session asks once to *trust* the
project; accept it (this is Claude Code's folder trust, stored globally and
separate from `make setup`'s permissions — it persists after one accept).

What happens, step by step (the cycle has four beats; review/sign-off/publish are
steps *within* Check):

1. **Plan** (interactive) — Claude reads the **tracker row for the issue id** from
   the configured Mantis export (`pdca.toml [tracker].export_csv`; override with
   `CSV=…`) and, with you, writes `results/issue_<id>/brief.md`. For the full bug
   thread, run `./engine/scripts/scrape-mantis.sh <id>` first (optional) — the
   planner reads `results/issue_<id>/mantis-notes.json` if present.
2. **Do** (headless) — Claude implements the brief: `patch.diff`, the test, `build-notes.md`.
3. **Check** — the deterministic gates run (`→ … still working` heartbeats while
   they do), then a headless advisory reviewer.
4. **Sign-off** (Check step, interactive) — Claude reviews the result *with* you; you
   clear the §6 items and decide `accept` / `iterate-do` / `iterate-plan`. The driver
   records §9 under the C6 guard.
5. **Publish** (Check step, interactive, on accept) — Claude drafts the contribution
   artifacts (commit-msg + PR description) and the driver opens a **draft PR** — the
   closing work of Check. `NO_PUBLISH=1` skips it; offline `rehearse` dry-runs it.
6. **Act** (interactive, only with `--act` / `ACT=1`) — Claude reviews the frozen
   cycle and suggests process improvements if any are warranted.

When a Plan/sign-off/publish session ends, exit the Claude session (**Ctrl-D**) to
let the flow continue.

**Closing Check — contribute the fix.** Once a fix is accepted, `make publish ID=<id>`
does the *closing work of Check*: a publisher leaf drafts `commit-msg.txt` +
`pr-description.md` (doc-16-conformant, validated by the T4 gate), then the driver
branches from `upstream/<base>`, applies the patch, commits, pushes, and opens a
**draft PR** — and stops. You review CI and mark it ready/merge yourself. Preview the
exact git/gh commands first with `DRY=1`. (This is Check's contribution arm, not a new
beat; `make flow` does not push for you.)

## Commands

| Command | What it does |
|---|---|
| `make setup` | One-time: write the permission config so the interactive leaves don't prompt. |
| `make flow ID=<id> [CSV="<path>"] [NO_PUBLISH=1] [ACT=1] [BY=<name>]` | Run the full cycle for one issue. On an accept it opens a draft PR (`NO_PUBLISH=1` stops at COMPLETE). `CSV` seeds Plan; `ACT=1` runs Act; `BY` overrides §9 attribution (defaults to the project author). |
| `make flow CSV="<path>"` | **Batch**: one Plan session may brief several issues; then every in-flight bundle builds unattended and you sign off the cheap-first queue. **Resumable** — re-run it to pick up where you left off (it skips/authors at Plan, then drives whatever's outstanding). |
| `make batch IDS="<id> …" [NOACT=1] [BY=<name>]` | Drive specific **already-briefed** bundles by id through the **full cycle** (no Plan): Do→Check→sign-off (cheap-first across the set)→Act once at the end — `make flow` seeded by ids. Run it in a terminal. `NOACT=1` stops after sign-off. **Resumable** — re-run to pick up whatever is still in flight. |
| `make publish ID=<id> [DRY=1] [BY=<name>]` | Closing work of Check: contribute an accepted fix as a **draft PR** (drafts the commit/PR artifacts, runs the T4 gate, branches from upstream, applies, commits, pushes, opens the draft). `DRY=1` previews. Ready/merge stay yours. |
| `make rehearse ID=<id> [CSV="<path>"]` | Dry-run the *same* control flow with stub leaves + stub gates — **no Claude, no Docker, instant**. Watch `PLANNED → … → COMPLETE` before a real run. |
| `make status` | List every bundle and its state. |
| `make cli ARGS="<subcommand>"` | Any other `pdca` subcommand (e.g. `signoff 13636 --accept`). |
| `make` / `make check` | Self-test (full / fast offline). |
| `make install` | Optional: a real `pdca` console script in `.venv/`. |

If something looks stuck, it isn't — a headless `claude -p` and a Docker gate print
nothing until they finish, so the flow shows a `… still working (NmSSs elapsed)`
heartbeat. Let it run.

## Gates (what makes a fix "verified")

Configured in [pdca.toml](pdca.toml) `[[gates.checks]]`, single-sourced for the local
driver and CI:

- **C4-verify** (gating) — the per-fix correctness check. Applies the bundle's
  `patch.diff` and runs *only* its test, asserting it is **red without the fix,
  green with it** (`engine/scripts/ubuntu/run-verify.sh`).
- **T3-unit** (advisory) — the whole gramps unit suite on the unmodified tree;
  informational baseline, not a per-fix gate.

## Bug fix vs. feature

The planner picks the brief template with you: ordinary fixes *and* most new
functionality use [templates/brief.md.tpl](templates/brief.md.tpl); a change big
enough to warrant a design proposal (a GEPS) uses
[templates/design-proposal.md.tpl](templates/design-proposal.md.tpl). Not every
feature is a GEPS — the design proposal is the exception, authored at Plan.

## Layout

```
src/pdca_harness/   the deterministic driver (state machine, gates, leaves, flow)
engine/             the gramps verification engine (Docker runners, lib, C4-verify)
templates/          brief / design-proposal / SUMMARY templates
results/issue_<id>/ one bundle per issue — the state IS the files here
pdca.toml           project config: leaves, gates, tracker, paths
docs/INTEGRATION.md gramps concretizations
PCDA/               the generic model (reference docs)
.claude/agents/     the five leaf agents (planner, builder, reviewer, signoff, act)
```

## Notes

- **Iteration is built in.** `iterate-do` rebuilds against the same brief;
  `iterate-plan` re-opens Plan. The flow loops until `COMPLETE` (bounded).
- **Nothing is pushed for you.** The builder may open a *draft* PR for CI but can
  never mark it ready/merge — enforced by `.claude/hooks/builder_guard.py`.
- **Harness changes feed back upstream.** This repo is rendered from a copier
  template; changes to the generic machinery are filed as `enhancement` issues on the
  [`pdca-harness`](https://github.com/eduralph/pdca-harness/issues) template repo for
  propagation.
