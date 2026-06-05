"""Publish — the **closing work of Check**: contribute an accepted fix as a draft PR.

Publishing is NOT a new PDCA beat. Check already owns the gates (including T4
contribution conformance) and the human sign-off; turning the accepted fix into a
draft pull request whose upstream CI the human weighs is the *contribution arm of
the same beat*. Once a bundle is accepted at sign-off (``state.COMPLETE``), this:

    contribution leaf → commit-msg.txt + pr-description.md     (the T4 gate's inputs)
    → T4 gate (must pass)
    → branch from upstream/<base> → git apply → commit → push → ``gh pr create --draft``
    → STOP.

STOP discipline: it never marks a PR ready or merges — that stays the human's
sign-off disposition. The mechanics are deterministic ``git``/``gh`` subprocesses
(no model decides control flow); the prose is written by the *publisher* leaf.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from . import brief, leaves, state
from .config import Config

COMMIT_MSG = "commit-msg.txt"
PR_BODY = "pr-description.md"


def publish(
    cfg: Config,
    issue_id: str,
    *,
    dry_run: bool = False,
    open_pr: bool = True,
    by: str = "",
    today: str | None = None,
) -> int:
    """Contribute an accepted bundle's fix as a draft PR. Return a process code."""
    d = cfg.bundle(issue_id)
    today = today or datetime.date.today().isoformat()

    # Guard — publish is Check's CLOSING act: only on an accepted bundle.
    s = state.state(d)
    if s != state.COMPLETE:
        print(f"publish: {d.name} is {s}, not COMPLETE — accept it at sign-off first",
              file=sys.stderr)
        return 1

    # Resolve the target from the brief (the contribution's where).
    repo_spec, base, slug = _resolve_target(d)
    if not repo_spec or not base:
        print(f"publish: brief has no usable 'Repo + branch target' "
              f"(got repo={repo_spec!r} base={base!r})", file=sys.stderr)
        return 1

    # Artifacts the T4 gate needs — write them with the publisher leaf if absent.
    if not ((d / COMMIT_MSG).is_file() and (d / PR_BODY).is_file()):
        print("publish: drafting contribution artifacts "
              f"({COMMIT_MSG} / {PR_BODY})…", file=sys.stderr)
        leaves.run_publish(d, cfg)
    if not ((d / COMMIT_MSG).is_file() and (d / PR_BODY).is_file()):
        print(f"publish: {COMMIT_MSG} / {PR_BODY} still missing — aborting", file=sys.stderr)
        return 1

    # T4 contribution gate — the artifacts MUST pass before anything is pushed.
    if not _t4_passes(cfg, d):
        print(f"publish: T4 contribution gate FAILED on {COMMIT_MSG} / {PR_BODY} — "
              "fix them and retry", file=sys.stderr)
        return 1

    branch = _branch_name(d, slug)
    summary_line = (d / COMMIT_MSG).read_text(encoding="utf-8").splitlines()[0]
    repo = (cfg.root.parent / repo_spec.split("/")[-1]).resolve()  # ../gramps etc.

    git = lambda *a: ["git", "-C", str(repo), *a]
    steps = [
        git("fetch", "upstream"),
        git("checkout", "-B", branch, f"upstream/{base}"),
        git("apply", str((d / "patch.diff").resolve())),
        git("commit", "-aF", str((d / COMMIT_MSG).resolve())),
        git("push", "-u", "origin", branch),
    ]
    pr_cmd = ["gh", "pr", "create", "--draft", "--repo", repo_spec, "--base", base,
              "--head", branch, "--title", summary_line,
              "--body-file", str((d / PR_BODY).resolve())]

    if dry_run:
        print(f"publish --dry-run — {d.name} → draft PR on {repo_spec} ({branch} → {base}):")
        for c in steps + ([pr_cmd] if open_pr else []):
            print("  " + " ".join(shlex.quote(x) for x in c))
        return 0

    # Real run: mutate the sibling fork — guard it is present and clean first.
    rc = _check_repo(repo)
    if rc != 0:
        return rc

    for c in steps:
        print("→ " + " ".join(c[3:]))  # drop the `git -C <repo>` prefix in the echo
        if subprocess.run(c).returncode != 0:
            hint = " (patch may not apply against upstream/%s — rebase the fix)" % base \
                if c[3] == "apply" else ""
            print(f"publish: step failed: {' '.join(c)}{hint}", file=sys.stderr)
            return 1

    pr_url = ""
    if open_pr:
        print("→ gh pr create --draft …")
        r = subprocess.run(pr_cmd, capture_output=True, text=True)
        out = (r.stdout or "").strip()
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            print("publish: branch pushed, but `gh pr create` failed — "
                  "open the draft PR by hand", file=sys.stderr)
        else:
            print(out)
            pr_url = out.splitlines()[-1] if out else ""

    (d / "publish.json").write_text(json.dumps({
        "branch": branch, "pr_url": pr_url, "base": base, "repo": repo_spec,
        "by": by or _signoff_by(d) or cfg.author or "unknown", "date": today,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"\nDraft PR prepared on {repo_spec} ({branch} → {base}).")
    if pr_url:
        print(f"  {pr_url}\n  watch CI:  gh pr checks {pr_url} --watch")
    print("  STOP: review CI, then mark it ready / merge yourself — the human's step.")
    return 0


# ----------------------------------------------------------------------------
def _resolve_target(d: Path) -> tuple[str, str, str]:
    """``(repo_spec, base_branch, slug)`` from the brief, e.g.
    ``("gramps-project/gramps", "maintenance/gramps61", "uimanager-…")``."""
    bp = d / "brief.md"
    target = brief.field(bp, "repo + branch target", "repo + branch", "target")
    repo_spec, _, base = target.partition("@")
    slug = brief.field(bp, "slug") or d.name.removeprefix("issue_")
    return repo_spec.strip(), base.strip(), _slugify(slug)


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.strip().lower()).strip("-")


def _branch_name(d: Path, slug: str) -> str:
    """``fix/bug-<id>-<slug>`` (the gramps convention), or ``enhancement/<id>-<slug>``
    when the brief's kind/disposition marks a feature."""
    issue_id = d.name.removeprefix("issue_")
    kind = brief.field(d / "brief.md", "kind", "disposition hint").lower()
    if any(k in kind for k in ("enhanc", "feature", "new-feature", "proposal")):
        return f"enhancement/{issue_id}-{slug}"
    return f"fix/bug-{issue_id}-{slug}"


def _t4_passes(cfg: Config, d: Path) -> bool:
    """Run every configured T4-tier gate over the bundle. No T4 gate → nothing to
    enforce (True). Keeps publish decoupled from any one project's checker."""
    t4 = [c for c in cfg.gates_checks if c.get("tier") == "T4"]
    if not t4:
        return True
    env = {**os.environ, "PDCA_BUNDLE": str(d)}
    for chk in t4:
        r = subprocess.run(chk.get("cmd", ""), shell=True, cwd=cfg.root, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print((r.stdout or r.stderr).strip(), file=sys.stderr)
            return False
    return True


def _check_repo(repo: Path) -> int:
    """The sibling fork must exist, be clean, and have upstream + origin remotes."""
    if not (repo / ".git").exists():
        print(f"publish: sibling checkout not found: {repo} "
              "(run engine/scripts/bootstrap-forks.sh)", file=sys.stderr)
        return 1
    porcelain = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                               capture_output=True, text=True).stdout.strip()
    if porcelain:
        print(f"publish: {repo} has uncommitted changes — clean it first:\n{porcelain}",
              file=sys.stderr)
        return 1
    remotes = subprocess.run(["git", "-C", str(repo), "remote"],
                             capture_output=True, text=True).stdout.split()
    for r in ("upstream", "origin"):
        if r not in remotes:
            print(f"publish: {repo} has no '{r}' remote "
                  "(run engine/scripts/bootstrap-forks.sh)", file=sys.stderr)
            return 1
    return 0


_BY_RE = re.compile(r"^- By / date:\s*(.+?)\s*/", re.MULTILINE)


def _signoff_by(d: Path) -> str:
    """The name from §9 'By / date', for the publish record."""
    summary = d / "SUMMARY.md"
    if not summary.exists():
        return ""
    m = _BY_RE.search(summary.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""
