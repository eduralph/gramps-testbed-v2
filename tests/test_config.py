"""Config.bundle id-normalisation (stdlib unittest).

Regression for #70: an id passed *with* a leading ``issue_`` (e.g. a bundle dir
name fed back into the driver) must resolve to the same directory as the bare
id, never a doubled ``issue_issue_<id>``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pdca_harness.config import Config, LeafConfig

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def _cfg(root: Path) -> Config:
    stub = LeafConfig(mode="stub")
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=TEMPLATES,
        default_branch="main",
        tracker_system="github",
        tracker_url="https://example.org/issues",
        issue_id_example="1",
        builder=stub,
        reviewer=stub,
        planner=stub,
        signoff=stub,
        publisher=stub,
        act=stub,
        gates_checks=[],
    )


class TestBundlePrefix(unittest.TestCase):
    def test_bare_and_prefixed_ids_resolve_same(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = _cfg(Path(t))
            self.assertEqual(cfg.bundle("13418"), cfg.bundle("issue_13418"))
            self.assertEqual(cfg.bundle("13418").name, "issue_13418")

    def test_prefixed_id_is_not_doubled(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = _cfg(Path(t))
            # the exact #70 shape: id already carries the prefix
            self.assertEqual(
                cfg.bundle("issue_skip-bsddb-tests-linux").name,
                "issue_skip-bsddb-tests-linux",
            )

    def test_issue_only_stripped_as_prefix_not_mid_name(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = _cfg(Path(t))
            # 'reissue_5' does not start with 'issue_' -> left intact
            # (the old str.replace would have corrupted it to 're5')
            self.assertEqual(cfg.bundle("reissue_5").name, "issue_reissue_5")


if __name__ == "__main__":
    unittest.main()
