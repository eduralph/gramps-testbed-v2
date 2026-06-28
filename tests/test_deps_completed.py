"""Offline slice: dependency resolution must find a prereq archived in ``completed/``.

A finished prerequisite moved to ``results/completed/`` must still satisfy an active
dependent's ``Depends on:`` — otherwise ``_check_dep_graph`` aborts the whole batch (the
``issue_820-review-nits`` → archived ``820-build-toolchain-coverage`` crash). Proves
``Config.find_bundle`` resolves completed/ (and falls back to the active path for a missing
id), and that ``_check_dep_graph`` / ``_deps_met`` / ``merged.is_merged`` treat a completed/
prereq as satisfied while a genuinely-missing prereq still blocks.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from pdca_harness import flow, merged, signoff, state
from pdca_harness.config import Config, LeafConfig

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def _cfg(root: Path) -> Config:
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=TEMPLATES,
        default_branch="main",
        tracker_system="mantis",
        tracker_url="",
        issue_id_example="1",
        builder=LeafConfig(mode="stub"),
        reviewer=LeafConfig(mode="stub"),
    )


def _complete_bundle(d: Path) -> None:
    """A COMPLETE bundle (brief + patch + gates + accepted SUMMARY), as state.state reads it."""
    d.mkdir(parents=True)
    (d / "brief.md").write_text("- **Slug:** s\n", encoding="utf-8")
    (d / "patch.diff").write_text("diff --git a/x b/x\n", encoding="utf-8")
    (d / "check-gates.json").write_text("{}", encoding="utf-8")
    shutil.copyfile(TEMPLATES / "SUMMARY.md.tpl", d / "SUMMARY.md")
    signoff.record(d / "SUMMARY.md", action="accept", by="T", date="2026-06-28")


class DepsInCompleted(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _cfg(self.tmp)
        # Prereq is COMPLETE but archived to completed/ (not in the active results/).
        _complete_bundle(self.cfg.bundle_root / "completed" / "issue_PREQ")
        # Active dependent declaring `Depends on: PREQ`.
        self.dep = self.cfg.bundle("DEP")
        self.dep.mkdir(parents=True)
        (self.dep / "brief.md").write_text(
            "- **Slug:** d\n- **Depends on:** PREQ\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_find_bundle_resolves_completed_then_active(self) -> None:
        self.assertEqual(self.cfg.find_bundle("PREQ"),
                         self.cfg.bundle_root / "completed" / "issue_PREQ")
        self.assertEqual(state.state(self.cfg.find_bundle("PREQ")), state.COMPLETE)
        # A genuinely-missing id resolves to its canonical ACTIVE path (so it still blocks).
        self.assertEqual(self.cfg.find_bundle("NOPE"), self.cfg.bundle("NOPE"))

    def test_check_dep_graph_accepts_completed_prereq(self) -> None:
        # Regression: this raised ValueError before find_bundle (the 820 crash).
        flow._check_dep_graph(self.cfg, [self.dep])  # must not raise

    def test_deps_met_with_completed_prereq(self) -> None:
        self.assertTrue(flow._deps_met(self.cfg, self.dep, set(), set()))

    def test_missing_prereq_still_blocks(self) -> None:
        bad = self.cfg.bundle("BAD")
        bad.mkdir(parents=True)
        (bad / "brief.md").write_text(
            "- **Slug:** b\n- **Depends on:** GHOST\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            flow._check_dep_graph(self.cfg, [bad])

    def test_is_merged_resolves_completed_prereq(self) -> None:
        (self.cfg.bundle_root / "completed" / "issue_PREQ" / "publish.json").write_text(
            '{"pr_url": "https://x/pull/1"}', encoding="utf-8")
        with mock.patch("pdca_harness.merged.subprocess.run",
                        return_value=SimpleNamespace(
                            returncode=0, stdout='{"state": "MERGED"}', stderr="")):
            self.assertTrue(merged.is_merged(self.cfg, "PREQ"))

    def test_stacks_on_archived_parent_is_not_admitted(self) -> None:
        # `Stacks on` needs the parent's LIVE published branch (resolved via cfg.bundle by
        # _stack_base_branch / worktree._target), so an archived parent must NOT be admitted
        # — otherwise the dependent runs but the stack consumers can't find its branch (#264
        # review). PREQ is COMPLETE-but-archived, so the stack readiness check stays False.
        (self.cfg.bundle_root / "completed" / "issue_PREQ" / "publish.json").write_text(
            '{"branch": "fix/preq", "pr_url": "https://x/pull/1"}', encoding="utf-8")
        self.assertFalse(flow._prereq_published(self.cfg, "PREQ"))
        stk = self.cfg.bundle("STK")
        stk.mkdir(parents=True)
        (stk / "brief.md").write_text(
            "- **Slug:** s\n- **Stacks on:** PREQ\n", encoding="utf-8")
        self.assertFalse(flow._deps_met(self.cfg, stk, set(), set()))


if __name__ == "__main__":
    unittest.main()
