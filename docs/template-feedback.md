# Template feedback log

> This instance (`gramps-testbed-v2`) is copier-rendered from the PDCA-harness
> template (the sibling `pdca-harness` repo). The **harness machinery** is
> template-managed, so improvements made here are really changes to the template
> and must be fed back upstream. This file is the propagation log: every
> template-bound change, its upstream target, and an apply note. Instance-only
> changes (the gramps engine, gramps config values) are listed at the end so the
> boundary is explicit.
>
> **This log is itself instance-local** — do not feed it back. Feeding the deltas
> into `pdca-harness/` is a human step (separate repo); the entries below make it
> mechanical. Rendering rule: files under `template/src/**` and `template/tests/**`
> copy **verbatim** (no `.jinja`); config/docs/agents are `.jinja`.

## Goals & intent (the human's instructions — verbatim, then resolved)

What was asked for (Eduard, this session):

> "the driver needs to open claude cli (configurable) for the generation of
> planning documents and for the signoff process where it is fed with documents.
> the whole process must be one continuous flow. for the initial planning a human
> feeds in documents (e.g. CSV file) to claude. at the end of the process, claude
> reviews the results together with the human and gets the ok. the act phase
> claude reviews the results and suggests improvements if sensible."

> "any changes to the template must be fed back to the original template, so I
> need documentation of that." (→ this log exists because of this instruction.)

Resolved into decisions (the three forks I asked about):
- **Scope:** the *full* flow now — Plan + Do + Check + interactive sign-off + Act
  under one orchestrator (`pdca flow`), not a staged increment.
- **Plan intake:** an *interactive* Claude session seeded with the human's
  documents (the CSV), not a headless batch generator — "a human feeds documents
  to Claude" was read literally.
- **Interactivity split:** the human-in-the-loop touch points (**Plan, Sign-off,
  Act**) hand the terminal to a seeded Claude REPL; **Do and the reviewer stay
  headless** (autonomous, write-a-doc).

The over-arching design constraint I held throughout: *configurable Claude at the
leaves, but the **driver's control flow stays model-free*** — state transitions,
gates, and the C6 accept-guard are deterministic code. "Claude-driven" means the
leaves are model-filled, not that a model decides what runs next. This is the line
the template must keep when it grows from two leaves to five.

## Change set — "continuous Claude-driven flow" (5 model leaves)

| # | Instance path | Upstream target | Kind | What to feed back |
|---|---|---|---|---|
| 1 | `src/pdca_harness/config.py` | `template/src/pdca_harness/config.py` | verbatim | `LeafConfig.interactive: bool`; `Config.planner/signoff/act` fields; `Config.author` (default §9 sign-off attribution, read from `[project].author`); `leaf()` reads `interactive`; three env overrides — `PDCA_LEAVES_MODE` (force all leaf modes), `PDCA_GATES_MODE=stub` (stub gates), and `PDCA_BUNDLE_ROOT` (redirect bundles, so `rehearse` can't collide with the real `results/`). **Apply verbatim** (no project-specific content). |
| 2 | `src/pdca_harness/leaves.py` | `template/src/pdca_harness/leaves.py` | verbatim | `_invoke(leaf, workdir, prompt)` (interactive vs headless); new `do_plan` / `run_signoff` / `run_act` + their stubs; sandboxed `_run_review_sandboxed` (independence enforced by a temp dir with only the reviewer inputs); `SIGNOFF_DECISION` / `signoff_decision()`. **Apply verbatim.** |
| 3 | `src/pdca_harness/flow.py` (NEW) | `template/src/pdca_harness/flow.py` (NEW) | verbatim | The whole orchestrator: `flow()` = Plan→Do→Check→sign-off→Act with the C6 guard and iterate loop. **Add as a new verbatim file.** |
| 4 | `src/pdca_harness/cli.py` | `template/src/pdca_harness/cli.py` | verbatim | `import … flow`; the `flow` subparser (`--from-csv`, `--act`, `--by`); the `_flow()` handler; dispatch line. **Apply verbatim.** |
| 5 | `tests/test_flow_slice.py` (NEW) | `template/tests/test_flow_slice.py` (NEW) | verbatim | Offline flow slice + C6 guard + iterate-then-complete + act-on-complete. **Add as a new verbatim file.** |
| 6 | `.claude/agents/planner.md` (NEW) | `template/.claude/agents/planner.md.jinja` (NEW) | **jinja** | New Plan-leaf agent. **Genericize on feed-back:** replace the literal "Gramps Testbed v2" in `description:` with `{{ project_name }}` (match `builder.md.jinja`). |
| 7 | `.claude/agents/signoff.md` (NEW) | `template/.claude/agents/signoff.md.jinja` (NEW) | **jinja** | New sign-off-leaf agent. Same genericize note as #6. |
| 8 | `.claude/agents/act.md` (NEW) | `template/.claude/agents/act.md.jinja` (NEW) | **jinja** | New Act-leaf agent. Same genericize note as #6. |
| 9 | `pdca.toml` `[leaves.*]` **structure** | `template/pdca.toml.jinja` | **jinja** | Feed back: the `interactive` field; `[leaves.planner]` / `[leaves.signoff]` / `[leaves.act]` stanzas; the headless builder argv (`-p --agent builder --permission-mode acceptEdits --allowedTools …`). Parameterize family/argv by the existing copier `*_family` vars. **Do NOT feed back** the instance's reviewer→claude fallback (template keeps the codex/decorrelated default) — see #R below. |
| 10 | `CLAUDE.md` (driver §) | `template/CLAUDE.md.jinja` | **jinja** | The "two leaves" → "five leaves" rewrite + `pdca flow` + `PDCA_LEAVES_MODE`. Keep any project tokens as `{{ … }}`. |
| 11 | `docs/quality-cycle/03-cycle-automation.md` (note) | `template/PCDA/quality-cycle/03-cycle-automation.md` | copy | The "Continuous-flow extension" blockquote. **Note path move:** instance `docs/quality-cycle/` ↔ template `PCDA/quality-cycle/`. (Authoritative source is the project wiki — re-vendor there too.) |
| 12 | `Makefile` | `template/Makefile` (NEW) | verbatim | Generic harness front-door. Targets: `flow ID=… [CSV=…] [ACT=1] [BY=…]` (the live cycle), `rehearse ID=…` (offline dry-run via `PDCA_LEAVES_MODE=stub PDCA_GATES_MODE=stub`), `setup` (permission config), `status`, `cli ARGS=…`, `install` (venv console script), `test`/`check`. Genericize the gramps-flavored comments on feed-back; all targets are generic. |
| 13 | `README.md` (NEW) | `template/README.md.jinja` (NEW, optional) | **jinja** | Quick-start + command reference for running the cycle. Mostly generic (the `make` commands); the gramps specifics (CSV, engine, branch rules) are instance-only — genericize with `{{ project_name }}`/placeholders if added to the template. |

### Batch-planning extension (one Plan session → several issues)
Folded into the same files (feed back together):
- `leaves.py`: `do_plan_batch(cfg, csv)` runs the planner in the **bundle root** so
  it can create `issue_<id>/brief.md` per chosen issue; `_stub_plan_batch` makes two
  bundles for offline tests.
- `flow.py`: `flow_batch(cfg, …)` = Plan-all → build-all (unattended) → cheap-first
  sign-off via `queue.awaiting_signoff` → Act once; shares `_signoff_and_apply` /
  `_plan_if_unplanned` with single `flow`; bounded by `max_passes`.
- `cli.py`: `flow` `issue_id` is now `nargs="?"` — omit it + pass `--from-csv` to
  batch; prints `{id: state}` + an `N/M complete` tally.
- `.claude/agents/planner.md.jinja`: the "one issue or several (batch)" paragraph.
- `Makefile`: `flow` accepts `CSV` without `ID` (batch); a `batch IDS="…"` target drives
  specific already-briefed bundles by id; usage updated.
- `tests/test_flow_slice.py`: `test_batch_plans_many_and_completes_all`,
  `test_batch_iterate_then_complete`, `test_batch_resumes_existing_without_new_briefs`,
  `test_batch_nothing_to_do_returns_empty`.

**Make `flow_batch` RESUMABLE (a live-run fix worth feeding back).** It first only
drove bundles *created in that Plan session* (`after − before`), so re-running
`flow --from-csv` to pick a batch back up failed with "Plan produced no new briefs"
(non-zero exit) even though briefs were sitting in flight. Now it drives **every
non-COMPLETE / non-UNPLANNED bundle** (this session's + any already in flight), and
`cli._flow` treats an empty result as **success (exit 0)** with a clear "nothing to
do" message — so a re-run resumes instead of erroring. Lesson for the template: a
batch/continuous driver must be **idempotently resumable** (state-derived work set),
not scoped to one invocation's freshly-created artifacts.

### Design-proposal (GEPS) extension — feature work as a richer Plan artifact
Two insights: (1) a GEPS maps onto **Plan** (author the design with Claude), not a
new work-kind — Do still implements (patch + tests) and Check is the **regular gated
check**, so there is NO `kind` switch, no gate-profile, no skipped gates. (2) The
GEPS template is the **exception**, not the route for every feature — most new
functionality uses the normal brief; the planner reserves the design proposal for
changes significant enough to warrant one (major architecture / API / UX). The only
gap was the Plan-stage template. Feed back together:
- `templates/design-proposal.md.tpl` (NEW) → `template/templates/design-proposal.md.tpl`
  (verbatim; **genericize** the "features target `master` (INTEGRATION §2)" line —
  the branch rule is per-project). The template keeps the driver-parsed
  `- **Label:** value` fields (Do reads them) and adds the design prose sections.
- `src/pdca_harness/assemble.py` → `template/src/pdca_harness/assemble.py` (verbatim):
  §1 now renders `Defect / goal:` with a `defect → goal` fallback, so a feature
  brief shows its Goal instead of a blank Defect.
- `leaves.py` (#2): the planner prompts (`_plan_prompt`, `_plan_batch_prompt`) now
  offer both templates — fix → `brief.md.tpl`, feature → `design-proposal.md.tpl`.
- `.claude/agents/planner.md.jinja` (#6): the "pick the template that fits" guidance.
- `docs/INTEGRATION.md.jinja` §6: flip the design-proposal template from `[planned]`
  to `[built]` and reference `templates/design-proposal.md.tpl` (note the canonical
  GEPS still lives upstream on the wiki; the cycle produces the draft + Do spec).
- `tests/test_flow_slice.py` (#5): `DesignProposalBrief` — the template keeps the
  parsed fields and a feature brief flows to AWAITING_SIGNOFF rendering its Goal.

### Live-run fixes (first real `pdca flow` surfaced three)
- **Headless prompt via stdin** (`leaves.py` `_invoke`, #2): a trailing positional
  prompt is **swallowed by the variadic `--allowedTools`**, so `claude -p` errors
  "Input must be provided…". Headless leaves now pass the prompt on **stdin**
  (`subprocess.run(argv, input=prompt, text=True, check=True)`); interactive leaves
  keep the seed positional. *This was a real crash on the first run — must feed back.*
- **`.claude/settings.json` allow-list** → `template/.claude/settings.json`: the
  shipped settings had no `allow`, so every read Bash (`ls`, `cat`, …) prompted
  during the interactive Plan session. Added a read/inspect allow-list (Read/Grep/
  Glob/Edit/Write + `Bash(ls|cat|grep|find|git log|python3|…:*)`) and kept
  `gh pr ready/merge` under `ask` (belt-and-braces with `builder_guard.py`).
- **Interactive agents end the session** (`planner.md` / `signoff.md` / `act.md`
  `.jinja`, #6): each now states it is one beat of an automated flow — it must NOT
  tell the human to run `pdca` commands, and must conclude + say to exit (Ctrl-D /
  `/quit`) so the driver continues. (The first run's planner told the human to run
  `pdca run 13636`, which is wrong inside `pdca flow`.)
- **Per-beat progress + shared heartbeat** (`src/pdca_harness/driver.py`,
  `progress.py` (NEW), `leaves.py`, `gates.py` → verbatim): `driver.advance` prints
  `→ <bundle>: Do — builder writing patch.diff…` / `Check — gates…` / `reviewer…` /
  `assembling SUMMARY…`. The heartbeat lives once in **`progress.run_with_heartbeat`**
  (ticks `… still working (NmSSs elapsed) — <label>` every 15s) and is shared by the
  headless leaves (`leaves._invoke`, prompt on stdin) **and** the gates
  (`gates._run_one`, which also announces `· gate <id>…` and still captures output
  for the evidence line). A headless `claude -p` and a Docker-backed gate both
  produce **no output for minutes**, so without this the flow looks hung and the
  human kills a working job. Insight: the leaf's `--allowedTools` also gates what
  the headless builder can do — too narrow (no `Grep`/`Glob`/read Bash) and it
  crawls; the `settings.json` allow-list above is what unblocks it.

- **`builder_guard` hook path was relative → blocked ALL Bash** (`.claude/agents/builder.md`
  `.jinja`, #6): the PreToolUse hook was `python3 .claude/hooks/builder_guard.py`. The
  builder's Bash cwd is the **bundle dir** (`results/issue_<id>/`), so the relative path
  resolved there, did not exist, and the failing hook returned **exit 2 → every Bash
  call blocked** for the whole Do session. Effect: the builder couldn't `grep`/`git
  blame`/run the test, so Do took ~10 min (line-by-line reads) and red→green was
  *argued, not observed*. Fix: root it — `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/builder_guard.py"`.
  *High-value, must feed back* — the bug exists verbatim in the template. (Surfaced by
  the builder itself, which honored STOP discipline and flagged it instead of
  neutralising the guard — the cycle working as intended.)

- **Leaves run from the project root, not the bundle dir** (`leaves.py`, #2): the
  bundle-writing leaves (`do_plan`/`do_plan_batch`/`do_build`/`run_signoff`) used to
  run with `cwd = the bundle dir` (`results/issue_<id>/`). That made the bundle the
  Claude *workspace*, so an interactive leaf hit a **"trust this folder?"** prompt
  (new dir) **plus a permission prompt for every file/dir outside it** (`templates/`,
  `docs/`, the gramps source) — no allow-list fixes that, it's a workspace-boundary
  thing. Now they run with `cwd = cfg.root` (the already-trusted project, which
  contains `templates/`/`docs/`/`results/`) and the **prompt names the bundle by
  absolute path**. Also fixes headless Do being unable to read project files outside
  the bundle. `planner.md.jinja` updated to match. *High-value, must feed back.*
- **`make setup`** (`Makefile`): one-command permission setup — writes the
  machine-local `.claude/settings.local.json` granting Claude read of the workspace
  and the sibling repos it patches. Generic target; the *paths* it writes are
  instance-specific (don't feed those back, only the target).

### Validation output enumerates the full 5/5/1 (`gates.py` → verbatim)
The check-gates output used to show only the *configured* gate rows + three
judgment placeholders. It now always renders the complete **5/5/1** (5 correctness
C1–C5 · 5 conformance T1–T5 · 1 validation), grouped into Correctness / Conformance
/ Validation sections: `_assemble_matrix` overlays each configured gate onto its
element (matched by `tier`); uncovered *gate* elements show `(no gate configured)`,
inputs (C1/C3) show their artifact, and the judgment cells (C5/T5/validation) show
`reviewer + human`. `overall` is still driven only by gating gates. Generic harness
logic, no gramps content — **must feed back** (`template/src/pdca_harness/gates.py`).

### #R — reviewer decorrelation (deliberately NOT fed back as-is)
This instance flips `[leaves.reviewer]` to `family="claude"` (`--agent reviewer`)
so the live flow runs end-to-end with Claude alone — the documented same-vendor
**fallback**. The template's default must stay **cross-vendor** (codex /
`AGENTS.md`), since decorrelation is a Check property (INTEGRATION §4). Feed back
only the `interactive=false` field and command-mode wiring for the reviewer, not
the claude argv.

### Plan-stage friction fixes (targeted, tracker-aware planner) — template-bound
A live `pdca flow` showed the Plan leaf scanning the testbed repo for issue info and
hitting permission prompts. The **generic** fixes (feed back):
- `src/pdca_harness/leaves.py` `_plan_prompt` / `_plan_batch_prompt` (verbatim): the
  prompt now names the **issue id** (derived from the bundle dir), the **tracker
  coordinates** (`cfg.tracker_system`/`tracker_url`), the **CSV row to read first**,
  a **notes-file convention**, and tells the planner to **cite via `git -C <repo>`,
  never `cd <repo> && git`** and **not to scan the harness repo**. The Plan leaf
  should be handed *where work comes from*, not left to guess.
- `src/pdca_harness/config.py` (verbatim): `Config.tracker_export_csv`, from
  `[tracker].export_csv` — the default tracker export the planner reads without
  `--from-csv`.
- `.claude/agents/planner.md` → `template/.claude/agents/planner.md.jinja` (jinja):
  the "tracker is the source of truth / `git -C` / read notes if present" guidance.
  Genericize the gramps/Mantis specifics.
- `.claude/settings.json` (jinja): add `Bash(git -C:*)` to `allow` — the safe
  sibling-repo idiom (a bare `Bash(git …)` rule does NOT match `cd … && git …`, and
  the latter trips Claude Code's "cd-before-git can run hooks" prompt). Insight worth
  a template note: prefer `git -C` over `cd && git` everywhere.
- **Trust is not settable from project settings.** `make setup` writes permissions
  (`.claude/settings.local.json`) but folder *trust* lives in the global
  `~/.claude.json` (`projects[<path>].hasTrustDialogAccepted`). The template's setup
  + README should say so plainly (one-time accept), not imply setup suppresses it.

### Publish — Check's contribution arm (closing work of Check) — template-bound
The cycle went quiet at COMPLETE; a `pdca publish <id>` step now contributes the
accepted fix as a **draft PR** — the *closing work of Check*, not a new beat. Generic
machinery (feed back):
- `src/pdca_harness/publish.py` (NEW, verbatim): the deterministic mechanics —
  guard (accepted-only), run the contribution leaf if artifacts missing, run the
  configured **T4** gate (must pass), then branch from `upstream/<base>` → `git apply`
  → commit → push → `gh pr create --draft` → STOP; record `publish.json`. Never codes
  ready/merge. The T4 check is found generically via `cfg.gates_checks` (tier `T4`), so
  it's decoupled from any one project's checker.
- `src/pdca_harness/leaves.py` (verbatim): a sixth leaf — `run_publish` /
  `_publish_prompt` / `_stub_publish` (the stub writes doc-16/T4-valid artifacts).
- `src/pdca_harness/config.py` (verbatim): `Config.publisher`; `cli.py` (verbatim):
  the `publish` subcommand; `Makefile` (verbatim): the `publish` target;
  `tests/test_publish_slice.py` (NEW, verbatim).
- `.claude/agents/publisher.md` → `template/.claude/agents/publisher.md.jinja` (jinja):
  reuses the `builder_guard.py` hook (block ready/merge); `templates/commit-msg.txt.tpl`
  (NEW). Genericize the gramps/doc-16 specifics.
Two insights worth carrying: (a) **the T4 gate's inputs (`commit-msg.txt` /
`pr-description.md`) only exist once you publish** — before that T4 is correctly N/A;
publishing is what makes T4 a *real* check. (b) The split holds: the **leaf writes the
prose**, **deterministic code does the git/PR mechanics** — and the mechanics stop at a
**draft PR** (ready/merge is the human's sign-off disposition).

### PDCA vocabulary — exactly four beats; steps live within beats — template-bound
A maintainer correction worth propagating to the template's prose: **the cycle has
exactly four beats (Plan · Do · Check · Act); never coin extra beats.** Review,
sign-off and publish are *steps within Check*; scrape and brief are *steps within
Plan*. A beat can have internal structure (Check also runs the 5/5/1 matrix), but the
model leaves (planner/builder/reviewer/signoff/publisher/act) are invocation
touchpoints, not beats. Feed back the wording fixes:
- `template/CLAUDE.md.jinja`: describe **Check as one beat with three model steps**
  (review / sign-off / publish), and Plan as scrape→brief — not a flat list that reads
  as extra beats.
- `template/.claude/agents/signoff.md.jinja`: "the Check sign-off **beat**" → "the
  sign-off **step** of the Check beat". Drop any "Check-closing" / coined-beat labels
  in `publisher.md.jinja`, and in `leaves.py` (verbatim) docstrings/comments.
- `template/PCDA/quality-cycle/*` (if any instance-rendered copy): keep beats and steps
  distinct. **Guard for the template:** don't let a new leaf/step's name imply a beat.

### Post-batch improvements (a live batch surfaced four) — mostly template-bound
A real multi-issue batch run surfaced four gaps; three are generic and feed back.

- **Reviewer always emits the full 5/5/1 verdict table.** The review prompt asked for
  "per-item verdicts" but didn't mandate completeness, so the human-facing overview
  was present on some bundles, missing on others. Fix is in the reviewer, not in
  assembly (we want the verdicts to *live in* `check-review.md`, not be synthesized):
  - `src/pdca_harness/gates.py` (verbatim): `canonical_elements()` — a public accessor
    for the 11 `_FIVE_FIVE_ONE` rows, so the reviewer table is single-sourced with the
    matrix the gates assemble.
  - `src/pdca_harness/leaves.py` (verbatim): `_REVIEW_PROMPT` now mandates one
    `| Item | Verdict | Basis |` row per element (PASS/FAIL/NEEDS-HUMAN/N/A); `_stub_review`
    emits that same complete table (offline parity).
  - `src/pdca_harness/assemble.py` (verbatim): `_needs_human` now lifts NEEDS-HUMAN from
    **table rows** as well as legacy `- NEEDS-HUMAN` bullets, order-preserving + deduped —
    so §6 fills regardless of the reviewer's shape.
  - `.claude/agents/reviewer.md.jinja` (jinja): the "always emit the complete table"
    section. *Generic lesson:* a judgment artifact the human reads each cycle should be
    **mandated complete**, not left to the model's discretion.

- **`batch` runs the full cycle, ending at Act** (was: parked at sign-off). `batch` is
  now `flow` seeded by ids with no Plan beat — same machinery, same endpoint:
  - `src/pdca_harness/flow.py` (verbatim): extract `_drive_and_act(cfg, bundles, …)` (the
    multi-pass build-all → cheap-first sign-off → Act-once body) shared by `flow_batch`
    (Plan-seeded) and the new `flow_ids(cfg, ids, …)` (id-seeded). **Batch sign-off must
    record all decisions before applying any** — `_signoff_and_apply(..., apply_now=False)`
    in the sweep, so an `iterate-do` doesn't rebuild mid-queue and interrupt review of the
    rest; the next pass's build-all applies every iteration together. (`apply_now=True`
    stays the default for single-issue `flow`.)
  - `src/pdca_harness/cli.py` (verbatim): `_batch` calls `flow.flow_ids(..., do_act=…)`
    instead of park-and-queue; the `batch` subparser gains `--no-act` / `--by`.
  - `Makefile` (verbatim): the `batch` target gains `NOACT` / `BY`; it's now interactive
    (sign-off/Act), like `flow`. *Generic lesson:* "drive several to done" and "drive
    several to a parked queue" are the same loop with a different endpoint — share it.

- **Transparent heartbeat (Tier 1 + 2): show *what* a leaf/gate is doing**, not just
  that time passed (verbatim across `progress.py`, `leaves.py`, `gates.py`):
  - `progress.py`: `run_with_heartbeat(..., status=Callable[[],str]|None)` appends a
    per-tick snapshot; `bundle_activity(watch_dir, expected)` reports each artifact
    (`name ✓ <size>` / `name —`), file-write staleness (`last write 12s ago`, soft
    `⚠ no writes 6m`), and a running `grampstest-` test container (`running test (2m)`).
    Best-effort — a probe exception can never break the run.
  - `leaves.py`: `_invoke(..., label=, status=)`; `do_build` watches the bundle,
    `_run_review_sandboxed` the sandbox. `gates.py`: `_run_one` watches the bundle/cwd.
  - `tests/test_progress.py` (NEW, verbatim). *Note:* the container name filter
    (`grampstest-`) is gramps-flavored — parameterize it when genericizing, or drop
    Tier 2 from the template default and keep Tier 1 (artifacts + staleness), which is
    project-agnostic.

- **C4-verify now covers addon fixes** (`engine/scripts/ubuntu/run-verify.sh`,
  **instance-only** — see Instance-only below). *Generic lesson worth carrying even
  though the script isn't:* a per-fix verify gate must cover **every target kind the
  project contributes to** (here core *and* addons — different checkout, test-name
  convention, run env), not just the primary repo. The gate read the brief's target to
  branch. A template's verify-gate skeleton should make "what am I patching/running"
  pluggable rather than hard-code one repo.

## Instance-only — do NOT feed back
- The gramps **branch convention** (`fix/bug-<id>-<slug>` / `enhancement/<id>-<slug>`)
  and the `repo_spec → ../<sibling>` resolution baked into `publish.py` are
  gramps/fork-layout specific; a template should make the branch pattern + the
  repo→checkout mapping configurable.
- `engine/scripts/mantis_notes.py` + `scrape-mantis.sh` (Playwright/Chrome Mantis
  scraper) and the `[tracker].export_csv` **value** — gramps/Mantis specific. The
  *mechanism* of passing a tracker export + a notes file to the planner is generic
  (above); the scraper and the CSV path are not.
- `engine/**` (the gramps verification engine) and `engine/tests/**`.
- `pdca.toml`: the gramps gate rows (`[[gates.checks]]` T3-unit, **C4-verify**, etc.)
  and any gramps-specific argv **values**; only the leaf *schema* (#9) is template-bound.
- `docs/INTEGRATION.md` gramps content; `results/**` bundles; `test-results/**`.
- The reviewer→claude fallback value (#R).
- **C4-verify** (`engine/scripts/ubuntu/run-verify.sh` + the gating bundle-scoped
  `[[gates.checks]]` row): the per-fix red→green gate — apply `patch.diff`, run only
  the test, assert green-with-fix / red-with-the-production-change-reverted. It is
  *gramps-specific* (Docker, gramps paths), so instance-only. **No harness change was
  needed** — the bundle-scoped gate mechanism (`scope="bundle"`, `$PDCA_BUNDLE`
  exported by `gates.py`) already supported it. The companion insight *is* worth the
  template's attention though: a **whole-suite gate can't gate a single fix** if the
  tree has any pre-existing failure — so T3-unit was set `gating = false` (advisory)
  and C4-verify made the gating correctness check. Templates should not ship a
  whole-suite runtime gate as `gating = true` by default.
- **T1/T2/T4 conformance checkers** (`engine/conformance/{t1_structure,t2_shape,
  t4_contribution,gate}.py` + `engine/tests/test_conformance.py` + their three
  `[[gates.checks]]` rows): the structure / shape / contribution tiers, mechanized
  from **wiki doc 16** ("Addon Development — Rules"), which is the foundation of the
  whole T1–T4 ladder (each MUST cites `doc16:LINE`). Doc 16 is *gramps addon policy*,
  so the checkers and rows are **instance-only**. **No harness change was needed** —
  again the existing `scope="bundle"` mechanism (the dispatcher derives the target
  from `$PDCA_BUNDLE/patch.diff`) and the `gates.py` 5/5/1 overlay-by-`tier` (#158,
  already template-bound) carried it. Two insights worth the template's attention:
  (a) **conformance tiers should be advisory by default** for the same reason as the
  runtime baseline — they audit *pre-existing* contributed code the current fix did
  not introduce, so gating on legacy non-conformance is wrong; promote per-tier once
  the targeted artifacts are clean. (b) The **tier names in `gates.py`'s 5/5/1 want a
  one-line provenance pointer** to whatever each downstream project's normative
  ruleset is (here doc 16) — the matrix is generic, but every instance should be able
  to cite its tiers back to a written source, which is exactly what makes a gate
  auditable. A copier `conformance_ruleset_ref` hint string would make that explicit.
- **Interface (GUI/dogtail) test tier** (`engine/interface/` suite + `engine/scripts/
  ubuntu/run-interface.sh` + the `T3-interface` `[[gates.checks]]` row + the
  `test_root_resolution.py` spec for the new runner): a headless AT-SPI/dogtail suite
  run under Xvfb. Entirely *gramps GUI* specific, so **instance-only**. **No harness
  change was needed** — the repo-scoped advisory-gate mechanism already carried it.
  Insight worth the template's attention: an interface/E2E tier is best wired
  **advisory and scoped to a smoke test**, not the full suite — the full suite mixes
  green tests with reproductions of *unmerged* upstream bugs, so a whole-suite gate is
  a characterization, not a pass/fail signal. The smoke ("does the app start") is the
  per-checkout health gate. (This run also surfaced a real GUI-startup bug in the
  gramps fork checkout — tracked as testbed issue #1 — which is exactly what an
  advisory interface gate is for.)

## Design insights & gotchas (for the template maintainer)

Non-obvious things learned building this — port the *reasoning*, not just the diff:

0. **Every containerized test run needs a timeout, and the builder must use the
   project runner — not a hand-rolled `docker run`.** A live batch run hung for 20+
   minutes: the Do builder assembled its own `docker run … xvfb-run python3 -m
   unittest <gui-addon-test>` (no D-Bus / no AT-SPI), so the Gtk-importing test
   blocked forever — and nothing killed it. Two template-bound fixes: (a) every test
   runner wraps `docker run` in `timeout --kill-after=30 "$GRAMPS_TEST_TIMEOUT"` +
   a named container it `docker kill`s on timeout, so a hung test FAILS the run
   instead of blocking the cycle (the run-*.sh impl is instance-only, but the
   *requirement* is generic — feed it back as a runner convention); (b) the
   **builder agent** (`builder.md.jinja`) + the `_build_prompt` seed steer Do to the
   project's runner (which provides the display/bus env + the timeout) and forbid a
   bare `docker run` (verbatim, template-bound). Lesson: leaves that "just run the
   test" must be pointed at the hardened runner, never left to improvise the harness.


1. **Reviewer independence becomes a sandbox in command mode.** The "reviewer
   never sees `build-notes.md`" contract was enforced by *omission* (the stub just
   didn't pass the file). A real Claude reviewer runs in the bundle dir with a
   `Read` tool, so `build-notes.md` sitting there would leak the builder's framing
   — a prompt "don't read it" is not enforcement. Fix: `_run_review_sandboxed`
   copies *only* the three reviewer inputs into a temp dir, runs the reviewer
   there, copies `check-review.md` back. **Independence is now physical, not
   polite.** Any future leaf with a withholding contract needs the same treatment.

2. **The model proposes the sign-off; the driver records it.** The interactive
   sign-off leaf does NOT write §9 — it writes a one-token `signoff-decision` file
   and (with the human) checks §6 boxes. The flow reads that token and routes it
   through the existing `signoff.record`, which enforces C6 (no accept while §6 is
   open). This keeps the *guard* deterministic even though the *decision* is made
   in a model+human session. Trusting the model to write a valid §9 directly would
   have put the accept-gate inside the model — exactly what the invariant forbids.

3. **Flipping leaves to `command` breaks offline determinism** (CI, `make`,
   anything that ran on stub leaves). The `PDCA_LEAVES_MODE` env override exists to
   restore it: one switch forces every leaf to stub regardless of `pdca.toml`. This
   is generic and belongs in the template — without it, the shipped tests can't run
   the driver without a live model. (`make`'s self-test sets `PDCA_LEAVES_MODE=stub`.)

4. **Interactive vs headless is a TTY decision, not a different mechanism.** Both
   are `subprocess.run(argv, cwd=…)`. Interactive = no `-p`, *don't capture stdio*
   (the child inherits the parent terminal → a seeded REPL), and a non-zero exit
   (human ^C) is non-fatal. Headless = `-p`, `check=True`. The only per-leaf state
   is the `interactive` bool + the argv. Confirmed CLI shapes (claude-code-guide):
   headless `claude -p "<prompt>" --agent X --permission-mode acceptEdits
   --allowedTools …` *does* write files; interactive `claude "<prompt>"` seeds the
   REPL. Gotcha: interactive needs a real TTY — it won't work from a captured CI
   subprocess, which is *why* those leaves stub out under `PDCA_LEAVES_MODE=stub`.

5. **Iteration is native to the loop, not a special case.** `iterate-plan` lands
   the bundle at `UNPLANNED` (brief versioned) → the loop re-opens Plan; `iterate-do`
   lands at `PLANNED` → the loop rebuilds. The orchestrator just re-reads state at
   the top each pass and applies the recorded transition with one `run_issue`. A
   `max_iters` bound prevents a pathological accept-less cycle from spinning.

6. **The planner stub must be self-contained.** It falls back to a minimal inline
   brief when `templates/brief.md.tpl` is absent, so the offline flow slice needs
   no fixtures. Keep that — it's what lets `test_flow_slice.py` run a *from-empty*
   bundle (planner authors the brief) with zero setup.

7. **Decorrelation is a real tension, surfaced not resolved.** The user's "Claude
   everywhere" and the Check reviewer's "different vendor from the builder" pull
   against each other. The instance takes the documented same-vendor *fallback* so
   the demo runs on Claude alone; the **template default must stay codex** (see #R).
   Worth a copier question someday: "reviewer vendor — same as builder (simpler) or
   decorrelated (stronger)?" so the tradeoff is chosen at render time, explicitly.

8. **`builder_guard.py` still applies to the headless builder.** `claude -p --agent
   builder` loads project settings (not `--bare`), so the PreToolUse hook keeps
   blocking `gh pr ready/merge`. Do not pass `--bare` to the builder leaf or the
   STOP discipline silently disappears.

## How to apply (suggested)
For verbatim files (#1–5, #12): copy the instance file over its
`template/…` counterpart and re-run the template's tests. For jinja files
(#6–11): port the change by hand into the `.jinja`, swapping project literals for
copier variables, then render a throwaway project (`copier copy`) and run
`make check` in it to confirm. I have **not** edited `pdca-harness/` — that's left
to you per STOP discipline.
