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

Run `make flow` **in a real terminal** — the Plan, sign-off and Act steps open
Claude interactively. The first interactive session may ask once to *trust* the
project; accept it.

What happens, step by step:

1. **Plan** (interactive) — Claude reads your input documents (a Mantis CSV via
   `CSV=…`) and, with you, writes `results/issue_<id>/brief.md`.
2. **Do** (headless) — Claude implements the brief: `patch.diff`, the test, `build-notes.md`.
3. **Check** — the deterministic gates run (`→ … still working` heartbeats while
   they do), then a headless advisory reviewer.
4. **Sign-off** (interactive) — Claude reviews the result *with* you; you clear the
   §6 items and decide `accept` / `iterate-do` / `iterate-plan`. The driver records
   §9 under the C6 guard.
5. **Act** (interactive, only with `--act` / `ACT=1`) — Claude reviews the frozen
   cycle and suggests process improvements if any are warranted.

When sign-off ends, exit the Claude session (**Ctrl-D**) to let the flow continue.

## Commands

| Command | What it does |
|---|---|
| `make setup` | One-time: write the permission config so the interactive leaves don't prompt. |
| `make flow ID=<id> [CSV="<path>"] [ACT=1] [BY=<name>]` | Run the full cycle for one issue. `CSV` seeds Plan; `ACT=1` runs Act; `BY` overrides §9 attribution (defaults to the project author). |
| `make flow CSV="<path>"` | **Batch**: one Plan session may brief several issues; they all build unattended, then you sign off the cheap-first queue. |
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
  template; changes to the generic machinery are tracked in
  [docs/template-feedback.md](docs/template-feedback.md) for propagation.
