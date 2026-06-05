# Repository integration — Gramps Testbed v2

> What Gramps Testbed v2 provides to plug into the generic PDCA cycle (see
> [quality-cycle.md](../PCDA/quality-cycle.md)). This is the project's answer to the
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
- **Default export the planner reads:** `pdca.toml [tracker].export_csv` (a Mantis
  CSV export). Run without `--from-csv`, the Plan leaf reads **only the row for the
  issue id** from this file (it does not scan the testbed repo); `--from-csv`
  overrides it. Re-export from Mantis to refresh.
- **Full-thread context (optional):** `./engine/scripts/scrape-mantis.sh <id>` writes
  `results/issue_<id>/mantis-notes.json` (the scraped comment thread); the planner
  reads it if present, else offers the command. Host-side, manual — see §9.
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
- **Comment voice / template:** `templates/tracker-comment.md.tpl`. The Mantis
  scraper is ported at `engine/scripts/mantis_notes.py` (+ `scrape-mantis.sh`) — a
  Mantis-specific scraper is required at this role; a different tracker needs its own.

## 2. Branch-target rules
Normative source: wiki **doc 16 §Contributor workflow** (`doc16:111-115`), the
vendored ruleset; each target carries its auditable origin per doc 16
§Conventions. Verified against the sibling checkouts: gramps is on
`maintenance/gramps61` (v6.1.0), addons-source `origin/HEAD → maintenance/gramps60`.
- **Per-area branch map:**
  - gramps **core** fixes *and* code-cleanup PRs → `maintenance/gramps61` (the
    current production branch), forward-merged to `master` — **not** `master`
    directly. (`doc16:113`; jralls on gramps#2298.)
  - **addon** fixes (`addons-source`) → `maintenance/gramps60` (addons production);
    the maintainer cherry-picks forward to gramps61. (`doc16:112`; Gary Griffin on
    addons-source PR 915, 2026-05-24.)
  - **testbed itself** → `main`.
  - Only genuinely new-feature core work targets `master`.
- **Branch from `upstream/<base>`, not the fork's tracking copy** — fork bases
  drift (e.g. gramps PRs 2315/2316 carried a stray `AGENTS.md` from the fork).
  (`doc16:115`.)
- **Override convention:** a maintainer's explicit base-branch request on the PR
  wins over the default. (`doc16:114`; e.g. Nick-Hall on gramps#2299.)
- **Cross-version cherry-pick rules:** addons are picked forward gramps60 → gramps61
  by the maintainer. Cherry-picking is a **correctness** check, not a git-conflict
  check — "applies cleanly" is *not* "remains correct"; verify against the target
  branch's related code (including files the patch doesn't touch).
- **Master-vs-maintenance rule:** `master` is feature-only; fixes ride the current
  maintenance branch and forward-merge from there so they reach users sooner.
  (`doc16:113`.)

## 3. Reproduction fixtures and runners
> **Engine layout (this instance):** the gramps verification engine lives under
> `engine/` here — the reference repo's `agent-work/scripts/` + top-level `docker/`
> were consolidated into one namespace on integration. **Ported & wired:**
> `ubuntu/run-unit.sh` (T3-unit), `ubuntu/run-addon-unit.sh` (T3-addon-unit),
> `ubuntu/run-verify.sh` (C4-verify, gating), `ubuntu/run-interface.sh`
> (T3-interface smoke, advisory) + the interface suite at `engine/interface/`,
> the image helpers `ubuntu/{rebuild-image,clean-build}.sh`, and the
> `scripts/lib/` helpers — all live in `pdca.toml`. **Not yet ported:** the manual
> QA runner and the Windows variants (described below from the reference repo).
> (`engine/scripts/run-verify.sh` is the *generic template skeleton*, not the
> gramps gate — the wired C4 gate is `ubuntu/run-verify.sh`.)
- **Canonical fixture path:** `example.gramps`.
- **Reproduction runner(s) + commands:**
  - GUI / dogtail (AT-SPI): `./engine/scripts/ubuntu/run-interface.sh [pattern]` **(ported, advisory)** —
    runs `engine/interface/test_*.py` headless under Xvfb + dbus + `at-spi-bus-launcher`;
    the suite + `base.py` harness + `data/` fixtures were ported to `engine/interface/`.
    The plumbing is verified end-to-end (gramps launches, AT-SPI queried, JUnit XML
    emitted); the **full suite is a mix of green tests and reproductions of unmerged
    upstream bugs** (e.g. `test_bug_0014100_*` → Mantis 14100 / gramps#2322), so it is
    an advisory characterization, not a clean gate. The `T3-interface` gate runs only
    `test_smoke.py` (the per-checkout GUI health check).
  - Visible manual QA: `./engine/scripts/ubuntu/run-manual.sh` *(not yet ported — host-display launcher, not a gate)*
  - Inside the container the suite is `GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"`.
- **Verification runner (test suite):**
  - Per-fix C4 gate (red→green): `./engine/scripts/ubuntu/run-verify.sh` **(ported, gating)** —
    applies the bundle's `patch.diff` and runs *only* its test (`$PDCA_BUNDLE`).
  - Core unit: `./engine/scripts/ubuntu/run-unit.sh` **(ported, advisory baseline)**
  - Addon unit: `./engine/scripts/ubuntu/run-addon-unit.sh [addon ...]` **(ported, advisory)** (empty = all addons
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

**The T1–T4 ladder is founded on wiki doc 16** —
[`wiki/pages/05 - Addon development/16-guidelines.md`](../wiki/pages/05%20-%20Addon%20development/16-guidelines.md),
titled "Addon Development — Rules", written in RFC-2119 MUST/SHOULD/MAY. Its
sections *are* the tiers: §Structure / §Source location → **T1**, §Coding style
→ **T2**, §Runtime / §Testing → **T3**, §Contributor workflow / §Verification
before commit / §Commit messages / §Mantis trailers → **T4**. The
`engine/conformance/{t1_structure,t2_shape,t4_contribution}.py` checkers
mechanize the statically-decidable **MUST** rules, each citing its rule back to
`doc16:LINE` (doc 16 §Conventions requires every rule be auditable to source).

| Tier | Written ruleset | Home | Single-sourced command | Status |
|---|---|---|---|---|
| T1 structure | doc 16 §Structure / §Source location (folder==id, `gramps_target_version`, `fname`, no `__init__.py`, no injected imports) | `engine/conformance/t1_structure.py` | `python3 ./engine/conformance/gate.py T1` (audits the addon the patch touches) | [built — advisory `T1-structure`, bundle-scoped] |
| T2 shape | doc 16 §Coding style (GPL header MUST; no diagnostic `print()`); `black --check` is a separate formatter gate | `engine/conformance/t2_shape.py` | `python3 ./engine/conformance/gate.py T2` | [built — advisory `T2-shape`, bundle-scoped; type-hint/docstring/`cb_` SHOULDs left to reviewer judgment] |
| T3 runtime | doc 16 §Runtime / §Testing; gramps test suite (stdlib `unittest`) | local Docker mirror + upstream CI | `./engine/scripts/ubuntu/run-unit.sh` ; `./engine/scripts/ubuntu/run-addon-unit.sh` | [built — both ported & wired (advisory `T3-unit` / `T3-addon-unit`); lib helpers + image helpers ported. The addon-unit catalog/sysdeps sub-gates skip until their tests are ported] |
| T4 contribution | doc 16 §Commit messages + §Mantis trailers + §Contributor-workflow PR-body rules (commit/PR conventions, §8) | `engine/conformance/t4_contribution.py` | `python3 ./engine/conformance/gate.py T4` (validates the bundle's `commit-msg.txt` / `pr-description.md`) | [built — advisory `T4-contribution`, bundle-scoped] |
| T5 judgment | reviewer contract below | Check reviewer + sign-off | (model) | [planned] |

- **Why advisory (gating = false):** T1/T2/T4 audit the *touched* contribution and
  surface doc-16 violations as evidence for the reviewer + human, but do not gate
  on legacy addon state the contribution did not introduce (many shipped addons
  predate parts of doc 16). A core-only patch is **N/A** for T1/T2; a bundle with
  no commit/PR wrapper is N/A for T4. Promote a tier to gating once the targeted
  addons are conformance-clean. The per-fix correctness gate stays **C4-verify**.

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
- **Enforcement mechanism:** human review + the advisory T1/T2/T4 conformance
  gates (`engine/conformance/`, doc-16-founded — §4); fork pre-commit hooks
  (`black` / `ruff` / `ast.parse`, plus `mypy` on the gramps fork) catch
  structure/shape upstream. The commit-message / Mantis-trailer checks are
  **built** (T4, `t4_contribution.py`); a git commit-msg *hook* wrapper is the
  only Tier-4 piece still greenfield.

## 9. Repo-specific scripts and tooling
List every project-specific script the cycle invokes (role → path + invocation + status).

| Role | Path | Invocation | Status |
|---|---|---|---|
| Tracker scrape | `engine/scripts/mantis_notes.py` + `scrape-mantis.sh` | `./engine/scripts/scrape-mantis.sh <id>` → `results/issue_<id>/mantis-notes.json` (Playwright + system Chrome; one-time manual login; host-side, not in the Docker image) | [ported — Plan-stage context; the planner reads the notes if present] |
| Handoff / brief generator | `triage/scripts/make_handoff.py` | merge CSV export + notes → per-issue briefs | [not ported — superseded by the interactive **planner** leaf, which briefs from the CSV directly at Plan] |
| Fork bootstrap | `engine/scripts/bootstrap-forks.sh` | clone gramps + addons-source forks as siblings, set `upstream` | [ported — root via pdca.toml marker, git-free] |
| Repro / verification runners | `engine/scripts/ubuntu/run-*.sh`, `engine/scripts/windows/run-*.sh` | unit / addon-unit / verify / interface / manual | [partial — `ubuntu/{run-unit,run-addon-unit,run-verify,run-interface,rebuild-image,clean-build}.sh` + `lib/` + the `engine/interface/` suite ported; manual + windows pending] |
| Per-fix correctness gate (C4) | `engine/scripts/ubuntu/run-verify.sh` | bundle-scoped: applies `patch.diff`, runs only its test, asserts red-without-fix / green-with-fix | [built — GATING; validated red→green] |
| PR verification | `scripts/verify-pr.sh` | `./scripts/verify-pr.sh <org/repo> <PR#> [--watch]` (poll checks) | [not ported — reference-repo tooling; absent here] |
| Conformance analyzers | `dev-tooling/{pyright,semgrep}/`, `dev-tooling/pre-commit/install.sh` | core shape/flow analyzers + fork hooks | [not ported — absent here; T1/T2 conformance gates (`engine/conformance/`) now cover structure/shape statically] |
| Driver | `src/pdca_harness/` | `pdca run <id>` ; `pdca flow <id>` | [built — five model leaves wired (`[leaves.*] mode = "command"`); `pdca flow` runs the continuous Plan→Do→Check→sign-off→Act cycle] |
| Act tooling (L4) | `src/pdca_harness/act.py` | `pdca act-index`, `pdca act-log --date <d>` | [built] |
| Gates (single-sourced) | `pdca.toml` `[[gates.checks]]` | `pdca gates [<id>] [--working-tree]` | [built — C4-verify + `T3-unit`/`T3-addon-unit`/`T3-interface` (GUI smoke) + `T1-structure`/`T2-shape`/`T4-contribution` (doc-16-founded, advisory, `engine/conformance/`) live; per-fix interface-level C4 staged] |
| Conformance checkers (doc 16) | `engine/conformance/{t1_structure,t2_shape,t4_contribution}.py` + `gate.py` | `python3 ./engine/conformance/gate.py {T1\|T2\|T4}` (bundle-scoped) | [built — §4 ladder; each MUST rule cites `doc16:LINE`; tested in `engine/tests/test_conformance.py`] |
| Reviewer config | `AGENTS.md` + `.claude/agents/reviewer.md` | (model leaf) | [built — contract + `[leaves.reviewer] mode = "command"` wired; this instance runs the same-vendor `family = "claude"` fallback (decorrelated codex is the template default — see §4 and template-feedback #R)] |
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
