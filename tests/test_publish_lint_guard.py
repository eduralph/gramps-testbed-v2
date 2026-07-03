"""Offline slice for the pre-publish lint guard (stdlib unittest).

The T2-lint Check gate (black + mypy) is re-run by ``publish.publish`` as a
pre-push guard so a lint-dirty bundle — including one accepted before the gate
existed — never opens an upstream PR that fails CI. This exercises the guard's
exit-code policy directly (``publish._lint_passes``) and end-to-end through a
dry-run publish, using a stub gate ``cmd`` (a bare ``exit N``) instead of the
real Docker runner. No Claude, no git, no Docker, no network.

Policy under test (run-lint.sh exit codes):
  0  → clean               → publish proceeds
  1  → lint-dirty          → publish BLOCKS
  2  → setup/infra problem → warn, publish proceeds (Check gate is primary)
  77 → no core .py to lint → publish proceeds
"""

from __future__ import annotations

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pdca_harness import publish, signoff, state
from pdca_harness.config import Config, LeafConfig

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"

_FIX_BRIEF = (
    "- **Slug:** my-fix\n"
    "- **Repo + branch target:** example-org/example-repo @ main\n"
)


def _lint_check(cmd: str) -> dict:
    """A [[gates.checks]] row for the T2-lint gate with a stub ``cmd``."""
    return {
        "id": publish.LINT_GATE_ID,
        "tier": "T2",
        "label": "black + mypy clean (stub)",
        "cmd": cmd,
        "gating": True,
        "scope": "bundle",
        "target": "core",
    }


def _cfg(root: Path, gates_checks=None) -> Config:
    stub = LeafConfig(mode="stub", interactive=True)
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=TEMPLATES,
        default_branch="main",
        tracker_system="github",
        tracker_url="https://example.org/issues",
        issue_id_example="1",
        builder=LeafConfig(mode="stub"),
        reviewer=LeafConfig(mode="stub"),
        planner=stub,
        signoff=stub,
        publisher=stub,
        act=stub,
        gates_checks=gates_checks or [],
    )


def _bundle(cfg: Config, issue_id: str) -> Path:
    """A COMPLETE (accepted) bundle with the contribution artifacts already present
    (so publish skips the publisher leaf and reaches the lint guard)."""
    d = cfg.bundle(issue_id)
    d.mkdir(parents=True)
    (d / "brief.md").write_text(_FIX_BRIEF, encoding="utf-8")
    (d / "patch.diff").write_text("diff --git a/x b/x\n", encoding="utf-8")
    (d / "check-gates.json").write_text("{}", encoding="utf-8")
    (d / "commit-msg.txt").write_text("Fix my thing\n\nFixes #1\n", encoding="utf-8")
    (d / "pr-description.md").write_text("## Fix\n\nFixes #1\n", encoding="utf-8")
    shutil.copyfile(TEMPLATES / "SUMMARY.md.tpl", d / "SUMMARY.md")
    signoff.record(d / "SUMMARY.md", action="accept", by="Tester", date="2026-06-05")
    return d


class LintGuardPolicy(unittest.TestCase):
    """`publish._lint_passes` blocks ONLY on a confirmed lint failure (exit 1)."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _passes(self, cmd: str) -> bool:
        cfg = _cfg(self.tmp, gates_checks=[_lint_check(cmd)])
        d = cfg.bundle("1")
        d.mkdir(parents=True, exist_ok=True)
        with redirect_stderr(io.StringIO()):
            return publish._lint_passes(cfg, d)

    def test_clean_passes(self) -> None:
        self.assertTrue(self._passes("exit 0"))

    def test_dirty_blocks(self) -> None:
        self.assertFalse(self._passes("echo 'T2-lint: black=FAIL'; exit 1"))

    def test_infra_problem_warns_but_passes(self) -> None:
        # exit 2 (e.g. a missing worktree) cannot confirm dirtiness → do NOT block.
        self.assertTrue(self._passes("echo 'worktree missing' 1>&2; exit 2"))

    def test_unverifiable_passes(self) -> None:
        # exit 77 (no core .py to lint) → nothing to enforce.
        self.assertTrue(self._passes("echo 'PDCA-UNVERIFIABLE'; exit 77"))

    def test_no_gate_configured_passes(self) -> None:
        cfg = _cfg(self.tmp, gates_checks=[])
        d = cfg.bundle("1")
        d.mkdir(parents=True, exist_ok=True)
        self.assertTrue(publish._lint_passes(cfg, d))


class PublishHonoursLintGuard(unittest.TestCase):
    """End-to-end: a dry-run publish blocks on a lint-dirty bundle, proceeds clean."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_publish_refuses_lint_dirty_before_pushing(self) -> None:
        cfg = _cfg(self.tmp, gates_checks=[_lint_check("echo 'black=FAIL'; exit 1")])
        d = _bundle(cfg, "DIRTY")
        self.assertEqual(state.state(d), state.COMPLETE)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = publish.publish(cfg, "DIRTY", dry_run=True, by="Tester", today="2026-06-05")
        self.assertEqual(rc, 1)
        # It stopped at the guard: no branch/PR was even planned, and it said why.
        self.assertNotIn("gh pr create", out.getvalue())
        self.assertIn("lint gate FAILED", err.getvalue())
        self.assertFalse((d / "publish.json").exists())

    def test_publish_proceeds_when_lint_clean(self) -> None:
        cfg = _cfg(self.tmp, gates_checks=[_lint_check("exit 0")])
        _bundle(cfg, "CLEAN")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = publish.publish(cfg, "CLEAN", dry_run=True, by="Tester", today="2026-06-05")
        self.assertEqual(rc, 0)
        # Got past the guard and planned the draft PR.
        self.assertIn("gh pr create", out.getvalue())
        self.assertIn("--draft", out.getvalue())

    def test_publish_proceeds_when_lint_unverifiable(self) -> None:
        # exit 77 (no core .py — e.g. a prose/manifest-only patch) must not block.
        cfg = _cfg(self.tmp, gates_checks=[_lint_check("echo 'PDCA-UNVERIFIABLE'; exit 77")])
        _bundle(cfg, "PROSE")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = publish.publish(cfg, "PROSE", dry_run=True, by="Tester", today="2026-06-05")
        self.assertEqual(rc, 0)
        self.assertIn("gh pr create", out.getvalue())


if __name__ == "__main__":
    unittest.main()
