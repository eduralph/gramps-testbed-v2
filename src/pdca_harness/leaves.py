"""The model leaves — the only points where a model is invoked (docs 03 §leaves).

The rest of the pipeline is deterministic code; models fill *artifacts*, never
decide control flow. There are six leaves across the cycle:

* **planner** (Plan, interactive) — the human feeds documents (e.g. a tracker CSV)
  and Claude writes ``brief.md``;
* **builder** (Do, headless) — reads ``brief.md``, writes ``patch.diff`` + the
  named test + ``build-notes.md``;
* **reviewer** (Check, headless) — advisory, decorrelated, writes ``check-review.md``;
* **signoff** (Check sign-off, interactive) — Claude reviews the result *with* the
  human and records the decision token;
* **publisher** (the publish step of Check, interactive) — for an ACCEPTED fix,
  writes the contribution artifacts (``commit-msg.txt`` + ``pr-description.md``) the
  deterministic ``publish`` step turns into a draft PR;
* **act** (Act, interactive) — reviews frozen cycles and proposes process deltas.

Two invariants live here and matter more than any prompt:

1. **Independence is a missing input.** The reviewer never sees ``build-notes.md``.
   In ``stub`` mode it simply isn't passed; in ``command`` mode the reviewer runs
   in a temp sandbox containing *only* the reviewer inputs, so the file is
   physically absent (a prompt instruction would not be enough).
2. **The builder cannot mark a PR ready.** Enforced by the ``builder`` subagent's
   tool scope + the ``builder_guard.py`` PreToolUse hook; the stub never does it.

``mode == "stub"`` writes offline placeholders (no Claude/TTY). ``mode ==
"command"`` runs the configured ``argv`` with the leaf's prompt appended, as a
subprocess in the working dir; ``interactive`` leaves inherit the terminal.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from . import act as act_mod
from . import brief
from . import progress
from .config import Config, LeafConfig

# build-notes.md is DELIBERATELY ABSENT from this list (independence contract).
REVIEWER_INPUTS = ["patch.diff", "brief.md", "check-gates.json"]

# The interactive sign-off leaf writes its decision here; the flow reads it and
# routes it through the C6-guarded signoff.record (never a model-written §9).
SIGNOFF_DECISION = "signoff-decision"
VALID_DECISIONS = frozenset({"accept", "iterate-do", "iterate-plan"})


# ----------------------------------------------------------------------------
# Subprocess invocation — the one place a leaf command is run.
# ----------------------------------------------------------------------------
def _invoke(leaf: LeafConfig, workdir: Path, prompt: str) -> None:
    """Run the leaf's configured command in ``workdir``, feeding it ``prompt``.

    Interactive leaves get the prompt as a *seed positional* (``claude "<prompt>"``)
    and inherit the parent terminal (a REPL); a non-zero exit (the human leaving
    the session) is not fatal. Headless leaves get the prompt on **stdin**, not as
    a trailing positional — a variadic option such as ``--allowedTools`` would
    otherwise swallow the prompt arg (claude then errors "Input must be provided…").
    """
    argv = list(leaf.argv)
    if leaf.interactive:
        subprocess.run(argv + [prompt], cwd=workdir)
        return
    # Headless: feed the prompt on stdin (a trailing positional would be swallowed
    # by a variadic --allowedTools) and tick a heartbeat, since `claude -p` prints
    # nothing until it finishes (minutes) and would otherwise look hung.
    rc, _ = progress.run_with_heartbeat(argv, cwd=workdir, input_text=prompt)
    if rc != 0:
        raise subprocess.CalledProcessError(rc, argv)


# ----------------------------------------------------------------------------
# Leaf 0 — Plan (planner, interactive): human feeds documents → writes brief.md.
# ----------------------------------------------------------------------------
def do_plan(d: Path, cfg: Config, csv: str | None = None) -> None:
    d.mkdir(parents=True, exist_ok=True)
    if cfg.planner.mode == "command":
        _invoke(cfg.planner, cfg.root, _plan_prompt(cfg, csv, d))
        return
    _stub_plan(d, cfg)


def _plan_prompt(cfg: Config, csv: str | None, d: Path) -> str:
    fix_tpl = cfg.templates_dir / "brief.md.tpl"
    geps_tpl = cfg.templates_dir / "design-proposal.md.tpl"
    issue_id = d.name.removeprefix("issue_")
    tracker_csv = csv or cfg.tracker_export_csv
    notes = d / "mantis-notes.json"

    # Source of truth = the tracker row for THIS issue, not a scan of the testbed.
    src_line = (
        f"The issue is {issue_id} on the {cfg.tracker_system or 'tracker'} "
        f"({cfg.tracker_url}/view.php?id={issue_id}). " if cfg.tracker_url
        else f"The issue is {issue_id}. "
    )
    csv_line = (
        f"Read the row for {issue_id} in the tracker export at '{tracker_csv}' FIRST — "
        "that row (summary / description / steps) is the authoritative statement of what "
        "to brief. " if tracker_csv else
        "Ask the human for the issue's tracker export or bug details. "
    )
    notes_line = (
        f"If {notes} exists, read it for the full comment thread. If you need the "
        f"discussion and it is absent, tell the human to run "
        f"`./engine/scripts/scrape-mantis.sh {issue_id}` (writes {notes}) and stop. "
    )
    citation_line = (
        "Cite the root cause against the gramps source with `git -C ../gramps log/show "
        "-- <file>` plus Read/Grep on ../gramps and ../addons-source — NEVER "
        "`cd ../gramps && git ...` (it trips a safety prompt; `git -C` is the safe idiom). "
        "Do NOT scan this testbed repo for issue information — the tracker is the source. "
    )
    return (
        "You are the Plan leaf of a PDCA cycle. " + src_line + csv_line + notes_line
        + citation_line
        + f"Together with the human, write brief.md in the bundle directory {d}. Default "
        f"to {fix_tpl} — it fits bug fixes AND ordinary new functionality. Use {geps_tpl} "
        "(a GEPS-style design proposal) ONLY for the exception: a change significant "
        "enough to warrant a proposal (major architecture / API / UX). Not every feature "
        "is a GEPS — when in doubt use the normal brief. Keep the parsed `- **Label:** "
        "value` field shape; resolve the repo + branch target per INTEGRATION §2. "
        "One bundle = one brief.md. Plan only."
    )


def _stub_plan(d: Path, cfg: Config) -> None:
    tpl = cfg.templates_dir / "brief.md.tpl"
    if tpl.exists():
        shutil.copyfile(tpl, d / "brief.md")
        return
    (d / "brief.md").write_text(
        "# Brief — stub\n\n"
        "- **Slug:** stub-issue\n"
        "- **Defect:** stub defect authored by the planner stub.\n"
        "- **Success criterion:** the stub test passes.\n"
        "- **Repo + branch target:** example-repo @ main\n"
        "- **Test file:** test_stub.py\n",
        encoding="utf-8",
    )


def do_plan_batch(cfg: Config, csv: str | None = None) -> None:
    """Batch Plan: ONE interactive session may brief several issues at once.

    The planner runs in the bundle root and creates an ``issue_<id>/brief.md`` per
    issue it and the human choose from the documents. The flow then discovers the
    new bundles and fans Do+Check over all of them (see ``flow.flow_batch``).
    """
    cfg.bundle_root.mkdir(parents=True, exist_ok=True)
    if cfg.planner.mode == "command":
        _invoke(cfg.planner, cfg.root, _plan_batch_prompt(cfg, csv))
        return
    _stub_plan_batch(cfg)


def _plan_batch_prompt(cfg: Config, csv: str | None) -> str:
    fix_tpl = cfg.templates_dir / "brief.md.tpl"
    geps_tpl = cfg.templates_dir / "design-proposal.md.tpl"
    tracker_csv = csv or cfg.tracker_export_csv
    src = f"the tracker export at '{tracker_csv}'" if tracker_csv \
        else "the input documents the human shares"
    return (
        "You are the Plan leaf of a PDCA cycle, in BATCH mode. With the human, read "
        f"{src} on the {cfg.tracker_system or 'tracker'} and decide which issues to brief "
        "— there may be SEVERAL. The tracker rows are the source of truth: do NOT scan "
        "this testbed repo for issue info, and cite gramps via `git -C ../gramps ...` "
        "(never `cd ../gramps && ...`). For EACH chosen issue create a bundle directory "
        f"`{cfg.bundle_root}/issue_<id>/` containing a brief.md — use the fitting "
        f"template: a bug fix → {fix_tpl}; a feature / enhancement → {geps_tpl}. Keep the "
        "parsed `- **Label:** value` field shape; `<id>` is the tracker id. One issue = "
        "one `issue_<id>/brief.md`. Plan only — do not implement."
    )


def _stub_plan_batch(cfg: Config) -> None:
    # Two bundles so the batch flow is exercised offline.
    for iid in ("BATCH1", "BATCH2"):
        d = cfg.bundle(iid)
        d.mkdir(parents=True, exist_ok=True)
        _stub_plan(d, cfg)


# ----------------------------------------------------------------------------
# Leaf 1 — Do (builder, headless): writes patch.diff + the test + build-notes.md.
# ----------------------------------------------------------------------------
def do_build(d: Path, cfg: Config) -> None:
    if cfg.builder.mode == "command":
        _invoke(cfg.builder, cfg.root, _build_prompt(d))
        return
    _stub_build(d, cfg)


def _build_prompt(d: Path) -> str:
    return (
        f"You are the Do builder. Read {d}/brief.md. Produce, in the bundle directory "
        f"{d}: (1) patch.diff — a unified diff against the brief's target branch; "
        "(2) the test file the brief names, red before the fix and green after; "
        "(3) build-notes.md — your rationale (withheld from the reviewer). Cite "
        "path:line on the target branch for every change. To check the test red→green "
        "use the engine runner ./engine/scripts/ubuntu/run-verify.sh (it has the "
        "display + dbus + AT-SPI env AND a timeout); do NOT hand-roll a `docker run` — "
        "it will hang forever on any test that imports a Gtk/GUI module. Do NOT push, "
        "open, or mark any PR ready."
    )


def _stub_build(d: Path, cfg: Config) -> None:
    test_rel = (brief.test_files(d / "brief.md") or [Path("test_stub.py")])[0]
    test_path = d / test_rel
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(
        "# Stub regression test shipped by the Do leaf (vertical slice).\n"
        "def test_placeholder():\n    assert True\n",
        encoding="utf-8",
    )
    (d / "patch.diff").write_text(
        "# Stub patch produced by the Do leaf for the vertical slice.\n"
        "# A real builder writes a unified diff here.\n"
        f"# (the shipped test is {test_rel})\n",
        encoding="utf-8",
    )
    (d / "build-notes.md").write_text(
        "# Build notes (builder rationale — withheld from the reviewer)\n\n"
        "Stub Do leaf. A real builder records here why this change, what was\n"
        "tried, and what was ruled out. The reviewer never sees this file.\n",
        encoding="utf-8",
    )


# ----------------------------------------------------------------------------
# Leaf 2 — Check reviewer (headless, decorrelated, advisory): check-review.md.
# ----------------------------------------------------------------------------
def reviewer_input_paths(d: Path) -> list[Path]:
    """The exact files the reviewer receives — build-notes.md is not among them."""
    return [d / name for name in REVIEWER_INPUTS]


_REVIEW_PROMPT = (
    "You are the Check reviewer — advisory, artifact-only, decorrelated from the "
    "builder. You have ONLY patch.diff, brief.md and check-gates.json in this "
    "directory (build-notes.md is deliberately withheld). Write check-review.md with "
    "per-item verdicts: PASS / FAIL / NEEDS-HUMAN. Re-derive evidence yourself; emit "
    "NEEDS-HUMAN for always-human items (fitness-to-purpose, ambiguous scope)."
)


def run_review(d: Path, cfg: Config) -> None:
    inputs = reviewer_input_paths(d)
    assert (d / "build-notes.md") not in inputs, "independence contract violated"

    if cfg.reviewer.mode == "command":
        _run_review_sandboxed(d, cfg)
        return
    _stub_review(d, cfg)


def _run_review_sandboxed(d: Path, cfg: Config) -> None:
    """Run the reviewer in a temp dir holding ONLY the reviewer inputs.

    This makes the independence contract mechanical, not prompt-based: with the
    reviewer's cwd containing no build-notes.md, the builder's framing cannot
    leak in even though the model has a Read tool. check-review.md is copied back.
    """
    with tempfile.TemporaryDirectory(prefix="pdca-review-") as tmp:
        sandbox = Path(tmp)
        for name in REVIEWER_INPUTS:
            src = d / name
            if src.exists():
                shutil.copy2(src, sandbox / name)
        _invoke(cfg.reviewer, sandbox, _REVIEW_PROMPT)
        produced = sandbox / "check-review.md"
        if produced.exists():
            shutil.copy2(produced, d / "check-review.md")


def _stub_review(d: Path, cfg: Config) -> None:
    # Model-decidable items the reviewer attempts (all PASS in the stub) plus the
    # always-human items it flags NEEDS-HUMAN by design (docs 04 §judgment cell).
    (d / "check-review.md").write_text(
        "# Cross-vendor reviewer (advisory, artifact-only)\n\n"
        f"Reviewer family: {cfg.reviewer.family or 'stub'}. "
        "Inputs: patch.diff, brief.md, check-gates.json (build-notes.md withheld).\n\n"
        "## Per-item verdicts\n"
        "- PASS — re-ran asserted evidence: stub red→green confirmed.\n"
        "- PASS — every cited path:line grounds on the target branch.\n"
        "- PASS — diff stays within one logical fix (model-decidable).\n"
        "- NEEDS-HUMAN — validation fitness-to-purpose: is this the right thing "
        "at all? (always-human by design)\n",
        encoding="utf-8",
    )


# ----------------------------------------------------------------------------
# Leaf 3 — Check sign-off (signoff, interactive): Claude + human reach the OK.
# ----------------------------------------------------------------------------
def run_signoff(d: Path, cfg: Config) -> None:
    if cfg.signoff.mode == "command":
        _invoke(cfg.signoff, cfg.root, _signoff_prompt(d))
        return
    _stub_signoff(d, cfg)


def _signoff_prompt(d: Path) -> str:
    return (
        f"You are the Check sign-off leaf. Review {d}/SUMMARY.md, {d}/patch.diff, "
        f"{d}/check-gates.md and {d}/check-review.md together with the human. Help "
        f"the human clear the §6 NEEDS-HUMAN items in {d}/SUMMARY.md (change "
        f"`- [ ]` to `- [x]` only with their explicit OK). Then write the agreed "
        f"decision as a single token — one of: {', '.join(sorted(VALID_DECISIONS))} — "
        f"into {d}/{SIGNOFF_DECISION}. Do not edit §9 yourself; the driver records it "
        "under a deterministic guard."
    )


def _stub_signoff(d: Path, cfg: Config) -> None:
    # Simulate the human clearing §6 and accepting, so the offline flow completes.
    summary = d / "SUMMARY.md"
    if summary.exists():
        text = summary.read_text(encoding="utf-8")
        summary.write_text(text.replace("- [ ]", "- [x]"), encoding="utf-8")
    (d / SIGNOFF_DECISION).write_text("accept\n", encoding="utf-8")


def signoff_decision(d: Path) -> str:
    """The token the sign-off leaf wrote, or "" if absent/invalid."""
    p = d / SIGNOFF_DECISION
    if not p.exists():
        return ""
    token = p.read_text(encoding="utf-8").strip()
    return token if token in VALID_DECISIONS else ""


# ----------------------------------------------------------------------------
# Leaf 4 — Act (act, interactive): review frozen cycles, suggest deltas if sensible.
# ----------------------------------------------------------------------------
def run_act(cfg: Config, date: str) -> None:
    if cfg.act.mode == "command":
        _invoke(cfg.act, cfg.root, _act_prompt(cfg, date))
        return
    _stub_act(cfg, date)


def _act_prompt(cfg: Config, date: str) -> str:
    entries = act_mod.index(cfg)
    index_md = act_mod.render_index(entries, act_mod.patterns(entries))
    return (
        "You are the Act leaf — cross-cycle process review. Below is the read-only "
        "index of frozen cycles and recurring signals. With the human, decide which "
        "process deltas (spec template / ruleset / gates / agent skills) are sensible "
        f"— suggest improvements ONLY if warranted. Append a dated entry for {date} to "
        "process/act-log.md, or state that no delta is warranted. Never re-decide a "
        "contribution's disposition.\n\n--- ACT INDEX ---\n" + index_md
    )


def _stub_act(cfg: Config, date: str) -> None:
    entries = act_mod.index(cfg)
    text = act_mod.scaffold_entry(entries, act_mod.patterns(entries), date=date)
    act_mod.append_entry(cfg, text)


# ----------------------------------------------------------------------------
# Leaf 5 — Publish (publisher, interactive): the closing work of Check. Writes the
# contribution artifacts (commit-msg.txt + pr-description.md) for an ACCEPTED fix;
# the deterministic `publish` step (publish.py) then branches/applies/commits/pushes
# and opens the DRAFT PR. The leaf writes prose only — it never pushes.
# ----------------------------------------------------------------------------
def run_publish(d: Path, cfg: Config) -> None:
    if cfg.publisher.mode == "command":
        _invoke(cfg.publisher, cfg.root, _publish_prompt(d, cfg))
        return
    _stub_publish(d, cfg)


def _publish_prompt(d: Path, cfg: Config) -> str:
    issue_id = d.name.removeprefix("issue_")
    target = brief.field(d / "brief.md", "repo + branch target", "target")
    pr_tpl = cfg.templates_dir / "pr-description.md.tpl"
    return (
        f"You are the Publish leaf — the closing work of Check. The fix for issue "
        f"{issue_id} is ACCEPTED; with the human, write TWO contribution artifacts in "
        f"{d}, following the project's doc 16 rules. Target: {target}. Read "
        f"{d}/brief.md + {d}/build-notes.md + {d}/patch.diff for content; cite gramps "
        f"via `git -C ../gramps` if needed.\n"
        f"1) {d}/commit-msg.txt — summary ≤70 chars, then a blank line, then the body "
        f"wrapped ≤80; the LAST line is the Mantis trailer `Fixes #{issue_id}` "
        f"(gramps CORE: the trailer goes in BOTH the commit and the PR body; "
        f"addons-source: reference the bug in the PR body only, NOT the commit). "
        f"Reference any other commit by its FULL hash. Keep `Fixes #{issue_id}` the "
        f"last line (the T4 gate enforces it); if you add a Co-Authored-By line, put "
        f"it ABOVE the trailer block.\n"
        f"2) {d}/pr-description.md — sections Root cause / Fix / Verified against / "
        f"Test, citing path:lines on the target branch, and reference #{issue_id} "
        f"(see {pr_tpl}).\n"
        "Write ONLY those two files. Do NOT push, branch, or open a PR — the driver's "
        "`pdca publish` does the branch/apply/commit/push/draft-PR after you finish."
    )


def _stub_publish(d: Path, cfg: Config) -> None:
    # Offline placeholders, deliberately doc-16/T4-shaped (summary ≤70, blank line,
    # body ≤80, `Fixes #<id>` last; PR body has the four sections + #<id>).
    issue_id = d.name.removeprefix("issue_")
    (d / "commit-msg.txt").write_text(
        f"Fix issue {issue_id} (stub contribution artifact)\n\n"
        "Stub commit body for the offline publish slice, wrapped under eighty\n"
        "characters so the T4 contribution gate validates it cleanly.\n\n"
        f"Fixes #{issue_id}\n",
        encoding="utf-8",
    )
    (d / "pr-description.md").write_text(
        "## Root cause\nstub.\n\n## Fix\nstub.\n\n## Verified against\n"
        "- path:1 — stub.\n\n## Test\nstub regression test.\n\n"
        f"References #{issue_id}\n",
        encoding="utf-8",
    )
