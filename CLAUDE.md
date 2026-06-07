# Gramps Testbed v2 — agent guidance

CI/CD harness for interface-testing Gramps and third-party addons via AT-SPI / dogtail

This project runs the **PDCA quality cycle** ([PCDA/quality-cycle.md](PCDA/quality-cycle.md),
the reference model). Repo-specific concretizations are in [docs/INTEGRATION.md](docs/INTEGRATION.md) —
read it for tracker, branch targets, fixtures, and the conformance ruleset.

## The driver

`pdca` advances a result bundle through the cycle (`pdca status`, `pdca run <id>`,
`pdca signoff <id> --accept`, `pdca publish <id>`), or runs it as one continuous
Claude-driven flow (`pdca flow <id> [--from-csv …] [--no-publish] [--act]`). State is
the files in `results/issue_<id>/`; nothing is hidden in a database.

The driver is deterministic — **no model decides control flow**. The cycle has the
four PDCA beats (Plan · Do · Check · Act); models are invoked only at the **six
leaves** across them — and the **Check beat holds three of those steps**:
- **Plan** — its steps: (optionally) scrape the bug's Mantis thread
  (`engine/scripts/scrape-mantis.sh`), then the planner leaf (interactive) authors
  `brief.md` from the tracker row + notes.
- **Do** — builder (headless): writes `patch.diff` + the test + `build-notes.md`.
- **Check** — its model steps are **review** (reviewer — headless, advisory),
  **sign-off** (signoff — interactive, captures the human's OK), and **publish**
  (publisher — interactive, drafts the commit/PR artifacts for an accepted fix; the
  deterministic `pdca publish` then opens the draft PR). Review, sign-off and publish
  are *steps within Check*, not beats of their own.
- **Act** — act (interactive): suggests process deltas across frozen cycles.

The leaves fill *artifacts*; the state transitions, the gates, the C6 accept-guard,
and the publish mechanics stay deterministic code. Each leaf is configurable in `pdca.toml` (`[leaves.*]`,
`mode = stub|command`, `interactive`); `PDCA_LEAVES_MODE=stub` forces the offline
placeholders for CI / `make`. In `pdca flow`, an accept continues to publish then
optional Act; `--no-publish` stops at COMPLETE.

## Do (the builder leaf) — your scope when implementing

- Read **`brief.md` only**. Produce `patch.diff`, the test the brief names, and
  `build-notes.md` (your rationale — withheld from the reviewer by the driver).
- The test must fail pre-fix and pass post-fix. Cite `path:line` on the target
  branch for every change.
- **STOP discipline:** you MAY push to a feature/draft branch and open a draft PR
  (useful for CI). You MUST NOT mark a PR ready or merge it — that is the human's
  sign-off step. This is enforced mechanically: the `builder` subagent
  (`.claude/agents/builder.md`) runs a PreToolUse hook
  (`.claude/hooks/builder_guard.py`) that blocks `gh pr ready` / `gh pr merge`.

## Check sign-off (human) — not the model's to perform

The driver assembles `SUMMARY.md` and stops at AWAITING_SIGNOFF. The human clears
§6 NEEDS-HUMAN, weighs the advisory review, and records §9. `pdca signoff
--accept` refuses while §6 has open items (C6). On an accept, **publish** (Check's
closing step) drafts the commit-msg + PR description and the driver opens a **draft
PR** — it never marks ready or merges; that stays the human's. `pdca publish <id>`
runs it standalone; `pdca flow` does it automatically on accept (`--no-publish` to skip).

## Act (human) — separate, cross-cycle

Process improvement (ruleset/template/gate/skill deltas) runs across frozen
bundles on a cadence, recorded in `process/act-log.md`. It never
re-decides a contribution's disposition.
