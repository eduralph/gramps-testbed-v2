"""Unit tests for the heartbeat status probe (stdlib unittest — no deps).

`progress.bundle_activity` turns a watched directory into the one-line snapshot the
heartbeat appends each tick (artifacts present, file-write staleness, a running test
container). The container probe is stubbed so these tests don't depend on Docker.
Run from the project root:  PYTHONPATH=src python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from pdca_harness import progress


class BundleActivity(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self._orig = progress._running_test_container
        progress._running_test_container = lambda: ""  # no container by default

    def tearDown(self) -> None:
        progress._running_test_container = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_artifacts_present_and_absent(self) -> None:
        (self.tmp / "patch.diff").write_text("x" * 2048, encoding="utf-8")
        s = progress.bundle_activity(self.tmp, ("patch.diff", "build-notes.md"))
        self.assertIn("patch.diff ✓ 2.0KB", s)
        self.assertIn("build-notes.md —", s)  # not written yet

    def test_fresh_write_shows_seconds(self) -> None:
        (self.tmp / "patch.diff").write_text("x", encoding="utf-8")
        self.assertRegex(progress.bundle_activity(self.tmp), r"last write \d+s ago")

    def test_quiet_dir_warns(self) -> None:
        f = self.tmp / "old.txt"
        f.write_text("x", encoding="utf-8")
        old = time.time() - 400  # >5 min
        os.utime(f, (old, old))
        self.assertIn("⚠ no writes", progress.bundle_activity(self.tmp))

    def test_running_container_suppresses_staleness(self) -> None:
        progress._running_test_container = lambda: "3m"
        f = self.tmp / "old.txt"
        f.write_text("x", encoding="utf-8")
        old = time.time() - 400
        os.utime(f, (old, old))
        s = progress.bundle_activity(self.tmp)
        self.assertIn("running test (3m)", s)
        self.assertNotIn("no writes", s)  # the container IS the activity

    def test_probe_never_raises_on_missing_dir(self) -> None:
        self.assertEqual(progress.bundle_activity(self.tmp / "does-not-exist"), "")

    def test_compact_duration(self) -> None:
        self.assertEqual(progress._compact_duration("2 minutes ago"), "2m")
        self.assertEqual(progress._compact_duration("About a minute ago"), "1m")
        self.assertEqual(progress._compact_duration("45 seconds ago"), "45s")
        self.assertEqual(progress._compact_duration(""), "")


if __name__ == "__main__":
    unittest.main()
