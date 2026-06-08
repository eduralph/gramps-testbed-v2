"""Unit tests for the T3 baseline diff (``engine/conformance/t3_baseline.py``).

The wrapper turns a whole-suite runner's red into "new or known?" by diffing the
run against a checked-in baseline manifest (testbed issue #7). These tests exercise
the pure core — JUnit parsing + the classify() decision — with synthetic fixtures
(no Docker), and assert the three shipped manifests load and that their documented
run-level signatures match the evidence the act-log recorded.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

CONF = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(CONF))

import t3_baseline  # noqa: E402

_SUITE = """<?xml version="1.0"?>
<testsuite name="s" tests="3">
  <testcase classname="pkg.Mod" name="test_ok"/>
  <testcase classname="pkg.Mod" name="test_bad"><failure message="boom">x</failure></testcase>
  <testcase classname="pkg.Other" name="test_err"><error message="kaboom">y</error></testcase>
</testsuite>
"""


class ParseJunit(unittest.TestCase):
    def test_collects_failures_and_errors_only(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        (tmp / "r.xml").write_text(_SUITE, encoding="utf-8")
        got = t3_baseline.parse_junit(tmp)
        self.assertEqual(
            got, {"pkg.Mod::test_bad": "failure", "pkg.Other::test_err": "error"}
        )

    def test_missing_dir_is_empty(self) -> None:
        self.assertEqual(t3_baseline.parse_junit(Path("/no/such/dir")), {})

    def test_recurses_into_per_addon_subdirs(self) -> None:
        # run-addon-unit.sh writes JUnit one level down (test-results/<addon>/*.xml);
        # a non-recursive glob missed them, so addon-unit reds were never parsed and
        # surfaced only as an unattributable "no parsed failures" delta (issue_8653).
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        sub = tmp / "DeepConnectionsGramplet"
        sub.mkdir()
        (sub / "TEST-x.xml").write_text(_SUITE, encoding="utf-8")
        got = t3_baseline.parse_junit(tmp)
        self.assertEqual(
            got, {"pkg.Mod::test_bad": "failure", "pkg.Other::test_err": "error"}
        )


class Classify(unittest.TestCase):
    MANIFEST = {
        "known_failures": [{"id": "pkg.Mod::test_bad", "type": "failure"}],
        "run_level_signatures": [
            {"regex": "core dumped", "match": "core dumped", "cause": "x", "tracking": "y"}
        ],
    }

    def test_green_passes(self) -> None:
        v = t3_baseline.classify({}, 0, "Ran 5 tests OK", self.MANIFEST)
        self.assertEqual(v["verdict"], "green")
        self.assertEqual(v["exit_code"], 0)

    def test_known_per_test_failure_is_baseline(self) -> None:
        v = t3_baseline.classify({"pkg.Mod::test_bad": "failure"}, 1, "FAILED", self.MANIFEST)
        self.assertEqual(v["verdict"], "baseline")
        self.assertEqual(v["exit_code"], 0)

    def test_new_failure_is_delta(self) -> None:
        v = t3_baseline.classify({"pkg.New::test_z": "failure"}, 1, "FAILED", self.MANIFEST)
        self.assertEqual(v["verdict"], "delta")
        self.assertEqual(v["exit_code"], 1)
        self.assertIn("pkg.New::test_z", v["summary"])

    def test_run_level_signature_is_baseline(self) -> None:
        # No parsed failures (the runner crashed before XML), non-zero exit, but a
        # known run-level signature explains it → matches baseline.
        v = t3_baseline.classify({}, 134, "Trace/breakpoint trap (core dumped)", self.MANIFEST)
        self.assertEqual(v["verdict"], "baseline")
        self.assertEqual(v["exit_code"], 0)

    def test_unexplained_nonzero_is_delta(self) -> None:
        v = t3_baseline.classify({}, 2, "some other unexpected failure", self.MANIFEST)
        self.assertEqual(v["verdict"], "delta")
        self.assertEqual(v["exit_code"], 1)

    def test_cleared_baseline_red_reported_when_green(self) -> None:
        v = t3_baseline.classify({}, 0, "Ran 5 tests OK", self.MANIFEST)
        self.assertEqual(v["cleared"], ["pkg.Mod::test_bad"])


class ShippedManifests(unittest.TestCase):
    """Seeded baselines load and recognise their documented evidence."""

    # Manifests that carry a documented run-level signature for a standing red.
    CASES = {
        "run-unit": "… Trace/breakpoint trap (core dumped)",
        "run-interface": "AttributeError: ... _Glade__dirname ... _ErrorHolder",
    }
    # The addon matrix manifests test each branch against its MATCHING core, so the
    # old version-mismatch red is gone — they're expected green-baseline (no signature).
    MATRIX = ("run-addon-unit-60", "run-addon-unit-61")

    def test_each_manifest_loads_and_matches_its_signature(self) -> None:
        for stem, evidence in self.CASES.items():
            path = t3_baseline.BASELINE_DIR / f"{stem}.json"
            with self.subTest(manifest=stem):
                self.assertTrue(path.is_file(), f"missing manifest {path}")
                m = t3_baseline.load_manifest(path)
                self.assertTrue(m.get("run_level_signatures"),
                                f"{stem}: no run_level_signatures seeded")
                # A nonzero run emitting the documented evidence matches the baseline.
                v = t3_baseline.classify({}, 1, evidence, m)
                self.assertEqual(v["verdict"], "baseline",
                                 f"{stem}: documented evidence should match baseline")

    def test_addon_matrix_manifests_load_clean(self) -> None:
        for stem in self.MATRIX:
            path = t3_baseline.BASELINE_DIR / f"{stem}.json"
            with self.subTest(manifest=stem):
                self.assertTrue(path.is_file(), f"missing manifest {path}")
                m = t3_baseline.load_manifest(path)
                # Matched core → no standing red; a green run is green-baseline.
                self.assertEqual(m.get("known_failures", []), [])
                self.assertEqual(t3_baseline.classify({}, 0, "OK", m)["verdict"], "green")


class UpdateManifest(unittest.TestCase):
    def test_update_preserves_non_ascii(self) -> None:
        # --update used the default ensure_ascii=True, so it escaped the readable
        # notes/targets (em-dash, ×) to \uXXXX every time it ran (run-addon-unit-60).
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        path = tmp / "m.json"
        path.write_text(
            '{"note": "addon × core — matched", '
            '"run_level_signatures": [], "known_failures": []}',
            encoding="utf-8",
        )
        t3_baseline._update_manifest(path, "run-x.sh", {})
        raw = path.read_text(encoding="utf-8")
        self.assertIn("×", raw)
        self.assertIn("—", raw)
        self.assertNotIn("\\u2014", raw)  # the em-dash must not be escaped


if __name__ == "__main__":
    unittest.main()
