# Repository integration — Gramps Testbed v2

> What Gramps Testbed v2 provides to plug into the generic PDCA cycle (see
> [quality-cycle.md](quality-cycle.md)). This is the project's answer to the
> "which / where / how" questions the generic model deliberately leaves open.
> It does **not** restate the cycle. Conflict rule: generic wins on cycle
> *shape*; this integration wins on *instantiation*.
>
> Concretizations below are carried over from the gramps-testbed reference repo
> (`CLAUDE.md`, `scripts/`, `triage/`, `dev-tooling/`). Items still marked
> **TODO** or **[planned]** are genuinely not yet established for *this* repo —
> mostly the bits that need the sibling forks bootstrapped here.
> Maintained by Act (append changes; don't silently rewrite).

## 1. Tracker integration
- **System / URL:** mantis (MantisBT) — https://gramps-project.org/bugs
- **Issue-ID format:** `13418` (integer; zero-padded `0013418` in CSV exports)
- **Cross-link form (commit/PR → tracker):** gramps core PRs use the `p:gramps:nnnn:`
  shorthand; addons-source PRs use the full GitHub URL / upstream's auto-link
  keywords (no shorthand for non-gramps repos). Inside a Mantis note, `#nnnn`
  refers to **another Mantis ticket**, not a GitHub PR.
- **Status → disposition mapping:** Mantis statuses (new / acknowledged / confirmed /
  assigned / feedback / resolved) → cycle Plan-time (`confirmed` → fixable,
  `feedback` → needs-info) and Check-time (`resolved` set on merge). The Mantis
  **project area** ("Gramps 6.0", "Gramps 5.2", master-only) drives the branch
  target (see §2).
- **Per-release field updated on a fix:** "Fixed in version".
- **Comment voice / template:** `templates/tracker-comment.md.tpl`. (Reference repo
  scrapes Mantis via `triage/scripts/mantis_notes.py` — a Mantis-specific scraper
  is required at this role; a different tracker needs its own.)

## 2. Branch-target rules
- **Per-area branch map:**
  - gramps **core** fixes *and* code-cleanup PRs → `maintenance/gramps61` (current
    production branch), **not** `master`.
  - **addon** fixes → `maintenance/gramps60` (addons production); maintainer
    cherry-picks forward to gramps61.
  - **testbed itself** → `main`.
  - Only genuinely new-feature core work targets `master`.
- **Override convention:** a maintainer's explicit base-branch request in the PR
  review thread beats the default.
- **Cross-version cherry-pick rules:** addons are picked forward gramps60 → gramps61
  by the maintainer. Cherry-picking is a **correctness** check, not a git-conflict
  check — "applies cleanly" is *not* "remains correct"; verify against the target
  branch's related code (including files the patch doesn't touch).
- **Master-vs-maintenance rule:** `master` is feature-only; fixes ride the current
  maintenance branch and forward-merge from there so they reach users sooner
  (gramps-testbed `CLAUDE.md` §"Upstream fix workflow").

## 3. Reproduction fixtures and runners
> **Engine layout (this instance):** the gramps verification engine lives under
> `engine/` here — the reference repo's `agent-work/scripts/` + top-level `docker/`
> were consolidated into one namespace on integration. Paths below are
> `engine/scripts/…`. **Ported so far: `run-unit.sh` only** (the T3-unit vertical
> slice, wired live in `pdca.toml`). The other runners are described from the
> reference repo and are **not yet ported** here.
- **Canonical fixture path:** `example.gramps`.
- **Reproduction runner(s) + commands:**
  - GUI / dogtail (AT-SPI): `./engine/scripts/ubuntu/run-interface.sh` *(not yet ported)*
  - Visible manual QA: `./engine/scripts/ubuntu/run-manual.sh` *(not yet ported)*
  - Inside the container the suite is `GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"`.
- **Verification runner (test suite):**
  - Core unit: `./engine/scripts/ubuntu/run-unit.sh` **(ported, live)**
  - Addon unit: `./engine/scripts/ubuntu/run-addon-unit.sh [addon ...]` *(not yet ported)* (empty = all addons
    with `tests/test_*.py`; loaded via dotted path `<Addon>.tests.<module>`)
  - Windows (MSYS2 UCRT64): `./engine/scripts/windows/run-unit.sh`, `./engine/scripts/windows/run-addon-unit.sh` *(not yet ported)*
- **Platform variants:** Linux containerized (Docker) is the full matrix; Windows
  MSYS2 UCRT64 covers unit + addon-unit only; **interface tests are Linux-only**
  (AT-SPI/dogtail doesn't port — a UIA driver would be needed). Addon test-file
  prefixes select platform: `test_*.py` (all), `test_linux_*.py` /
  `test_windows_*.py` (platform-only), `test_integration_*.py` (Linux-only, DB-backed).
- **What counts as a successful repro:** JUnit XML under `test-results/<addon>/`;
  interface failures drop screenshots in `artifacts/screenshots/`. A valid repro =
  the regression test is **red before** the fix and **green after**.

## 4. Conformance ruleset (answers the validation-tooling matrix for this repo)
For each tier: the written ruleset it consumes, its **home**, and the
**single-sourced command** the driver and CI both run.

| Tier | Written ruleset | Home | Single-sourced command | Status |
|---|---|---|---|---|
| T1 structure | gramps CONTRIBUTING + fork pre-commit config | fork-local pre-commit hooks | `pre-commit run --all-files` (`black --check`, `ast.parse`) | [partial — built for forks] |
| T2 shape | `ruff` E9/F63/F7/F82; `dev-tooling/semgrep/rules/` | fork pre-commit + dev-tooling mirror | `semgrep --config dev-tooling/semgrep/rules/` ; `ruff check` | [partial] |
| T3 runtime | gramps test suite (stdlib `unittest`) | local Docker mirror + upstream CI | `./engine/scripts/ubuntu/run-unit.sh` ; `./engine/scripts/ubuntu/run-addon-unit.sh` | [partial — `run-unit.sh` ported & wired live as the `T3-unit` gate; `run-addon-unit.sh` not yet ported] |
| T4 contribution | addon-dev guidelines (doc 16); commit/PR conventions (§8) | fork PR CI + human review | `./scripts/verify-pr.sh <org/repo> <PR#>` | [partial] |
| T5 judgment | reviewer contract below | Check reviewer + sign-off | (model) | [planned] |

- **Reviewer family (cross-vendor, ≠ builder):** codex — config `AGENTS.md`
  (decorrelated path); `.claude/agents/reviewer.md` is a same-vendor fallback with
  execute-only tool scope (no write to the fix).
- **Builder family:** claude — `.claude/agents/builder.md` [built], with the
  ready-mark block enforced by the `.claude/hooks/builder_guard.py` PreToolUse hook.
- **Project-defined human-only items** (reviewer emits NEEDS-HUMAN by design):
  fitness-to-purpose ("is this the right thing at all", always human); ambiguous
  branch-target choice; cherry-pick correctness across maintenance branches; any
  change touching the upstream public API surface. Note: Family-B **core** analyzer
  findings (pyright / semgrep in `dev-tooling/`) are **advisory** in CI but a hard
  zero-FP gate in pre-commit — they are not addon conformance.

## 5. Upstream-isn't-ahead routine
- **What "upstream" is:** `gramps-project/gramps` (core), `gramps-project/addons-source`
  (addons), `gramps-project/addons` (read-only publish target). Forks are owned by
  `FORK_OWNER` (default `eduralph`), distinct from the testbed owner (`Ralphovi`);
  the `upstream` remote is configured by `engine/scripts/bootstrap-forks.sh`.
- **Search routine + tokenization gotchas:** search by **affected file path**, not
  bug-ID or keyword — anchoring on paths catches side-effect fixes that keyword/ID
  searches miss. GitHub tokenization caveat: `latex in:title` does **not** match
  "Latexdoc".
- **Merged-history check command:**
  - addons: `git log upstream/maintenance/gramps60 -- <Addon>/`
  - core: `git log upstream/maintenance/gramps61 -- <path>` (also check `master`)
  - plus a closed/rejected-PR search across `gramps-project/*` by the file path.

## 6. Brief and design-proposal templates
- **Brief template:** `templates/brief.md.tpl`. (Reference repo's scaffolder set:
  `SUMMARY.md.tpl`, `exit-brief.md.tpl`, `increment-brief.md.tpl` under `triage/`.)
- **Design-proposal template:** `templates/design-proposal.md.tpl` [built] — a
  GEPS-style Plan artifact, **reserved** for changes significant enough to warrant a
  proposal (major architecture / API / UX). Most work — fixes *and* ordinary new
  functionality — uses the normal brief; not every feature is a GEPS. When it does
  apply, the GEPS *is* the Plan beat (authored interactively with the planner leaf);
  Do then implements it and Check runs the regular gated check, so it is a richer
  brief, not a separate track. Features target `master` (§2). The canonical GEPS
  still lives upstream on the wiki; this produces the draft + the spec Do reads.
- **Required project-specific frontmatter/sections:** the triage verdict and the
  Mantis project area (the latter drives the §2 branch target).

## 7. Bundle and act-log paths
- **Bundle root + ID format:** `results/issue_<mantis-id>/` (reference repo groups
  these under `triage/batches/<batch>/results/issue_<id>/`).
- **Act log path:** `process/act-log.md`
- **Versioned briefs on iterate-to-Plan:** `brief.vN.md` in the bundle (default)

## 8. Committing and PR conventions
- **Commit-message format:** past-tense one-line subject; body explains the *why*,
  not just the *what*; trailer
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. A
  "Verified against" reference cites `path:lines` against the **target branch**
  (no SHA unless cross-branch/historical); the commit that *caused* a bug gets an
  explicitly-labelled line **with** its SHA.
- **PR description format:** Root cause / Fix / Verified against / Test (see
  `templates/pr-description.md.tpl`). The PR body MUST reference the Mantis issue
  using upstream's auto-link keywords.
- **Enforcement mechanism:** human review today; fork pre-commit hooks
  (`black` / `ruff` / `ast.parse`, plus `mypy` on the gramps fork) catch
  structure/shape; commit-msg hook [planned] (Tier 4 greenfield).

## 9. Repo-specific scripts and tooling
List every project-specific script the cycle invokes (role → path + invocation + status).

| Role | Path | Invocation | Status |
|---|---|---|---|
| Tracker scrape | `triage/scripts/mantis_notes.py` | scrape Mantis comment threads → `triage/notes/issue_<id>.json` | [built] |
| Handoff / brief generator | `triage/scripts/make_handoff.py` | merge CSV export + notes → per-issue briefs | [built] |
| Fork bootstrap | `engine/scripts/bootstrap-forks.sh` | clone gramps + addons-source forks as siblings, set `upstream` | [ported — root via pdca.toml marker, git-free] |
| Repro / verification runners | `engine/scripts/ubuntu/run-*.sh`, `engine/scripts/windows/run-*.sh` | unit / addon-unit / interface / manual | [partial — `ubuntu/run-unit.sh` ported] |
| Per-fix correctness gate (C4) | `engine/scripts/ubuntu/run-verify.sh` | bundle-scoped: applies `patch.diff`, runs only its test, asserts red-without-fix / green-with-fix | [built — GATING; validated red→green] |
| PR verification | `scripts/verify-pr.sh` | `./scripts/verify-pr.sh <org/repo> <PR#> [--watch]` (poll checks) | [built] |
| Conformance analyzers | `dev-tooling/{pyright,semgrep}/`, `dev-tooling/pre-commit/install.sh` | core shape/flow analyzers + fork hooks | [partial] |
| Driver | `src/pdca_harness/` | `pdca run <id>` | [built — stub leaves] |
| Act tooling (L4) | `src/pdca_harness/act.py` | `pdca act-index`, `pdca act-log --date <d>` | [built] |
| Gates (single-sourced) | `pdca.toml` `[[gates.checks]]` | `pdca gates [<id>] [--working-tree]` | [built — `T3-unit` live via `engine/scripts/ubuntu/run-unit.sh`; addon-unit/interface/T1-T2 rows staged] |
| Reviewer config | `AGENTS.md` + `.claude/agents/reviewer.md` | (model leaf) | [built — contract; wire command mode] |
| Builder subagent | `.claude/agents/builder.md` + `.claude/hooks/builder_guard.py` | (model leaf) | [built — ready-mark blocked] |

## 10. Maintainer and governance
- **Who reviews:** Eduard Ralph (solo; `Ralphovi` / `eduralph` across the forks). No
  team review.
- **Ready-mark gate:** Eduard opens fork PRs as **draft**, re-reads with fresh eyes,
  and marks ready himself; the builder commits and stops — no push / PR-open /
  ready-mark without explicit instruction (mechanically enforced by
  `.claude/hooks/builder_guard.py`).
- **External-contribution flow differences:** contributions reach upstream via fork
  PRs; the testbed's own `main` is branch-protected (PR required, no force-push,
  conversation-resolution required).
- **MAINTAINERS file:** none.

## 11. Per-repo P-/D-/C-/A- extensions
None today. Prefix convention for this repo is `gramps-testbed-v2-` (e.g.
`gramps-testbed-v2-C7`). Add repo-prefixed rules that *tighten or add to* a generic
rule — never weaken one — as running cycles surface them.

## Optional — testing platform matrix
A fix is "verified" only against the platforms its test actually ran on:
Linux/Docker covers unit + addon-unit + interface; Windows MSYS2 UCRT64 covers
unit + addon-unit; interface coverage on Windows is open (no AT-SPI port).
`SUMMARY.md` §7 must be honest about which of these a given fix exercised.
