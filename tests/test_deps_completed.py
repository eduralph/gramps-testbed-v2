"""Offline slice: dependency resolution must find a prereq archived in ``completed/``.

A finished prerequisite moved to ``results/completed/`` must still satisfy an active
dependent's ``Depends on:`` — otherwise the batch aborts (the ``issue_820-review-nits`` →
archived ``820-build-toolchain-coverage`` crash). In the wave model (template v0.43) the dep
resolution lives in :mod:`waves` (``check_dep_graph`` / ``compute_waves``) and
:func:`flow._runnable`; all three plus :func:`merged.is_merged` must treat a completed/ prereq
as satisfied via :meth:`Config.find_bundle`, while a genuinely-missing prereq still blocks.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from pdca_harness import flow, merged, signoff, state, waves
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
        # Regression: this raised ValueError before find_bundle (the 820 crash), now in waves.
        waves.check_dep_graph(self.cfg, [self.dep])  # must not raise

    def test_compute_waves_with_completed_prereq(self) -> None:
        # The archived prereq is out-of-batch + COMPLETE, so it imposes no ordering: the
        # dependent computes into a single wave instead of aborting.
        wv = waves.compute_waves(self.cfg, [self.dep])
        self.assertEqual([[p.name for p in w] for w in wv], [["issue_DEP"]])

    def test_runnable_with_completed_prereq(self) -> None:
        # _runnable must see the archived prereq as COMPLETE (via find_bundle) and keep the
        # dependent, not skip it as "prerequisite not COMPLETE".
        self.assertEqual(flow._runnable(self.cfg, [self.dep]), [self.dep])

    def test_missing_prereq_still_blocks(self) -> None:
        bad = self.cfg.bundle("BAD")
        bad.mkdir(parents=True)
        (bad / "brief.md").write_text(
            "- **Slug:** b\n- **Depends on:** GHOST\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            waves.check_dep_graph(self.cfg, [bad])

    def test_is_merged_resolves_completed_prereq(self) -> None:
        (self.cfg.bundle_root / "completed" / "issue_PREQ" / "publish.json").write_text(
            '{"pr_url": "https://x/pull/1"}', encoding="utf-8")
        with mock.patch("pdca_harness.merged.subprocess.run",
                        return_value=SimpleNamespace(
                            returncode=0, stdout='{"state": "MERGED"}', stderr="")):
            self.assertTrue(merged.is_merged(self.cfg, "PREQ"))


if __name__ == "__main__":
    unittest.main()
