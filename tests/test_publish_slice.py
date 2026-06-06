"""Offline slice for `pdca publish` — Check's contribution arm (stdlib unittest).

Drives `publish.publish(dry_run=True)` over a stub **COMPLETE** bundle with a stub
publisher leaf: proves the guard (accepted-only), the contribution-artifact
generation, the upstream-based branch naming, and that the dry run *plans* the
git/gh commands without pushing. No Claude, no git, no network.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from pdca_harness import publish, signoff, state
from pdca_harness.config import Config, LeafConfig

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def _cfg(root: Path) -> Config:
    """Stub leaves, no configured gates (T4 skipped → orchestration focus)."""
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=TEMPLATES,
        default_branch="main",
        tracker_system="mantis",
        tracker_url="https://example.org/bugs",
        issue_id_example="1",
        builder=LeafConfig(mode="stub"),
        reviewer=LeafConfig(mode="stub"),
        planner=LeafConfig(mode="stub", interactive=True),
        signoff=LeafConfig(mode="stub", interactive=True),
        publisher=LeafConfig(mode="stub", interactive=True),
        act=LeafConfig(mode="stub", interactive=True),
        gates_checks=[],
    )


def _bundle(cfg: Config, issue_id: str, *, brief_body: str, accepted: bool) -> Path:
    d = cfg.bundle(issue_id)
    d.mkdir(parents=True)
    (d / "brief.md").write_text(brief_body, encoding="utf-8")
    (d / "patch.diff").write_text("diff --git a/x b/x\n", encoding="utf-8")
    (d / "check-gates.json").write_text("{}", encoding="utf-8")
    shutil.copyfile(TEMPLATES / "SUMMARY.md.tpl", d / "SUMMARY.md")
    if accepted:
        signoff.record(d / "SUMMARY.md", action="accept", by="Tester", date="2026-06-05")
    return d


_FIX_BRIEF = (
    "- **Slug:** my-fix\n"
    # Parser-clean field form (`**Label**:` — colon OUTSIDE the bold). The
    # `**Label:**` form real briefs/templates use leaks the closing `**` into the
    # value (a tracked `parse_fields` bug); this fixture isolates publish.py's
    # branch/head logic from that so the head-owner assertion is meaningful.
    "- **Repo + branch target**: gramps-project/gramps @ maintenance/gramps61\n"
)


class PublishSlice(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _cfg(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_dry_run_plans_commands_and_writes_artifacts(self) -> None:
        d = _bundle(self.cfg, "PUB", brief_body=_FIX_BRIEF, accepted=True)
        self.assertEqual(state.state(d), state.COMPLETE)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = publish.publish(self.cfg, "PUB", dry_run=True, by="Tester", today="2026-06-05")
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        # the publisher stub wrote the two T4 artifacts
        self.assertTrue((d / "commit-msg.txt").exists())
        self.assertTrue((d / "pr-description.md").exists())
        # branch from UPSTREAM/<base>, the gramps fix/bug-<id>-<slug> convention
        self.assertIn("checkout -B fix/bug-PUB-my-fix upstream/maintenance/gramps61", out)
        self.assertIn("gh pr create", out)
        self.assertIn("--draft", out)
        # a dry run pushes nothing and records nothing
        self.assertFalse((d / "publish.json").exists())

    def test_refuses_unaccepted_bundle(self) -> None:
        d = _bundle(self.cfg, "NOPE", brief_body=_FIX_BRIEF, accepted=False)
        self.assertNotEqual(state.state(d), state.COMPLETE)  # AWAITING_SIGNOFF
        self.assertEqual(publish.publish(self.cfg, "NOPE", dry_run=True), 1)

    def test_enhancement_branch_category(self) -> None:
        body = (
            "- **Slug:** add-thing\n"
            "- **Kind:** enhancement (design proposal)\n"
            "- **Repo + branch target:** gramps-project/gramps @ master\n"
        )
        _bundle(self.cfg, "FEAT", brief_body=body, accepted=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            publish.publish(self.cfg, "FEAT", dry_run=True)
        self.assertIn("checkout -B enhancement/FEAT-add-thing upstream/master", buf.getvalue())

    def test_commit_stages_patch_added_files(self) -> None:
        """Regression (#23): the commit must stage patch-ADDED files (the new test),
        not only modified-tracked ones — `git apply` + `add --all` + `commit -F`,
        never `commit -aF` (whose `-a` silently drops a new file from the commit)."""
        _bundle(self.cfg, "ADD", brief_body=_FIX_BRIEF, accepted=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            publish.publish(self.cfg, "ADD", dry_run=True)
        out = buf.getvalue()
        self.assertIn("add --all", out)       # stages new files (the regression test)
        self.assertIn("commit -F", out)
        self.assertNotIn("commit -aF", out)   # the dropped-new-file bug must not return

    def test_pr_head_is_fork_owner_qualified(self) -> None:
        """Regression (#23): a fork-based PR's --head must be OWNER:BRANCH, else gh
        resolves the branch against the base repo (--repo) and fails 'Head ref must
        be a branch'. (No sibling checkout here, so the owner falls back to the base
        owner — the assertion is on the OWNER:BRANCH *shape*, not the value.)"""
        _bundle(self.cfg, "HEAD", brief_body=_FIX_BRIEF, accepted=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            publish.publish(self.cfg, "HEAD", dry_run=True)
        out = buf.getvalue()
        self.assertRegex(out, r"--head \S+:fix/bug-HEAD-my-fix\b")  # owner-qualified
        self.assertNotIn("--head fix/bug-HEAD-my-fix", out)         # never a bare branch

    def test_fork_owner_parses_origin_url(self) -> None:
        """`_fork_owner` extracts the GitHub owner from origin (ssh + https forms)."""
        for url, owner in (
            ("git@github.com:eduralph/gramps.git", "eduralph"),
            ("https://github.com/eduralph/gramps.git", "eduralph"),
            ("https://github.com/eduralph/gramps", "eduralph"),
        ):
            repo = Path(tempfile.mkdtemp())
            try:
                subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
                subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", url],
                               check=True)
                self.assertEqual(publish._fork_owner(repo), owner)
            finally:
                shutil.rmtree(repo, ignore_errors=True)
        self.assertEqual(publish._fork_owner(Path(tempfile.gettempdir()) / "nope"), "")


if __name__ == "__main__":
    unittest.main()
