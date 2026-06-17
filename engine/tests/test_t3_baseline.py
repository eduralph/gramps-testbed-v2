"""Unit tests for the T3 baseline diff (``engine/conformance/t3_baseline.py``).

The wrapper turns a whole-suite runner's red into "new or known?" by diffing the
run against a checked-in baseline manifest (testbed issue #7). These tests exercise
the pure core — JUnit parsing + the classify() decision — with synthetic fixtures
(no Docker), and assert the three shipped manifests load and that their documented
run-level signatures match the evidence the act-log recorded.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CONF = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(CONF))

import t3_baseline  # noqa: E402


def _git_repo(path: Path) -> None:
    """A minimal committed git repo at *path* (no network, no user config leak)."""
    run = lambda *a: subprocess.run(
        ["git", "-C", str(path), *a], check=True, capture_output=True
    )
    run("init", "-q")
    run("config", "user.email", "t@t")
    run("config", "user.name", "t")
    run("config", "commit.gpgsign", "false")
    (path / "f.txt").write_text("x", encoding="utf-8")
    run("add", "-A")
    run("commit", "-q", "-m", "init")

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

    def test_parsed_failure_with_matching_signature_is_baseline(self) -> None:
        # issue #13: a whole-run crash that surfaces BOTH as a parsed per-test error
        # AND as a known run-level signature must classify as baseline, not a spurious
        # delta — the per-test parse must not shadow the run-level signature.
        v = t3_baseline.classify(
            {"setUpClass (interface.test_smoke.SmokeTest)": "error"},
            1,
            "AttributeError: ... _Glade__dirname ... Trace/breakpoint trap (core dumped)",
            self.MANIFEST,
        )
        self.assertEqual(v["verdict"], "baseline")
        self.assertEqual(v["exit_code"], 0)
        self.assertIn("under that failure mode", v["summary"])

    def test_unexplained_nonzero_is_delta(self) -> None:
        v = t3_baseline.classify({}, 2, "some other unexpected failure", self.MANIFEST)
        self.assertEqual(v["verdict"], "delta")
        self.assertEqual(v["exit_code"], 1)

    def test_cleared_baseline_red_reported_when_green(self) -> None:
        v = t3_baseline.classify({}, 0, "Ran 5 tests OK", self.MANIFEST)
        self.assertEqual(v["cleared"], ["pkg.Mod::test_bad"])


class RunRunnerClearsResults(unittest.TestCase):
    """``_run_runner`` clears ``test-results/`` before invoking the runner, so a runner
    that writes no XML (or bails early without clearing) can never have a previous
    capture's reds attributed to it (#94). Without the clear, the stale XML survives and
    ``parse_junit`` reports the prior gate's failures against this one."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        # Point the module's RESULTS_DIR at our scratch dir for the duration of the test.
        self._orig = t3_baseline.RESULTS_DIR
        t3_baseline.RESULTS_DIR = self.tmp / "test-results"
        self.addCleanup(setattr, t3_baseline, "RESULTS_DIR", self._orig)
        t3_baseline.RESULTS_DIR.mkdir(parents=True)
        # A previous capture's JUnit, left behind by a runner that bailed early.
        (t3_baseline.RESULTS_DIR / "stale.xml").write_text(_SUITE, encoding="utf-8")

    def _runner_that_writes_nothing(self) -> str:
        # A trivial runner that produces NO JUnit (mimics the early-bail "nothing to run").
        path = self.tmp / "noop-runner.sh"
        path.write_text("#!/bin/sh\necho 'nothing to run'\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
        return str(path)

    def test_stale_results_cleared_before_runner(self) -> None:
        self.assertTrue((t3_baseline.RESULTS_DIR / "stale.xml").exists())
        rc, _ = t3_baseline._run_runner(self._runner_that_writes_nothing(), [])
        self.assertEqual(rc, 0)
        # The stale XML is gone, so this runner's parse can only be its own (empty).
        self.assertFalse((t3_baseline.RESULTS_DIR / "stale.xml").exists())
        self.assertEqual(t3_baseline.parse_junit(t3_baseline.RESULTS_DIR), {})


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


class TreeState(unittest.TestCase):
    def test_reports_ref_sha_and_clean(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        _git_repo(tmp)
        st = t3_baseline.tree_state(tmp)
        self.assertIsNotNone(st)
        self.assertTrue(st["sha"])
        self.assertFalse(st["dirty"])

    def test_dirty_when_uncommitted_changes(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        _git_repo(tmp)
        (tmp / "f.txt").write_text("changed", encoding="utf-8")
        self.assertTrue(t3_baseline.tree_state(tmp)["dirty"])

    def test_non_git_dir_is_none(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        self.assertIsNone(t3_baseline.tree_state(tmp))


class TreeDrift(unittest.TestCase):
    REC = {"ref": "detached", "sha": "abc1234", "dirty": False}

    def test_no_recorded_tree_no_warning(self) -> None:
        self.assertIsNone(t3_baseline.tree_drift(None, self.REC))

    def test_exact_clean_match_no_warning(self) -> None:
        self.assertIsNone(t3_baseline.tree_drift(self.REC, dict(self.REC)))

    def test_sha_mismatch_warns(self) -> None:
        cur = {"ref": "fix/x", "sha": "def5678", "dirty": False}
        msg = t3_baseline.tree_drift(self.REC, cur)
        self.assertIn("drift", msg)
        self.assertIn("abc1234", msg)
        self.assertIn("def5678", msg)

    def test_dirty_warns_even_if_sha_matches(self) -> None:
        cur = {"ref": "detached", "sha": "abc1234", "dirty": True}
        msg = t3_baseline.tree_drift(self.REC, cur)
        self.assertIn("dirty", msg)

    def test_missing_tested_tree_warns(self) -> None:
        msg = t3_baseline.tree_drift(self.REC, None)
        self.assertIn("not a git checkout", msg)


class UpdateStampsTree(unittest.TestCase):
    def test_update_records_baseline_tree(self) -> None:
        import json

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        path = tmp / "m.json"
        tree = {"ref": "detached", "sha": "abc1234", "dirty": False}
        t3_baseline._update_manifest(path, "run-x.sh", {}, tree=tree)
        m = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(m["baseline_tree"], tree)


class WriteRunnerLog(unittest.TestCase):
    """A delta persists the raw runner output into the bundle so an opaque exit is
    diagnosable (issue #117); green/baseline and no-bundle write nothing."""

    DELTA = {"verdict": "delta", "exit_code": 1, "summary": "DELTA: …"}
    GREEN = {"verdict": "green", "exit_code": 0, "summary": "green"}
    OUTPUT = "runner stderr line 1\nTraceback …\nexit 2\n"

    def _bundle(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        return tmp

    def test_delta_writes_log_with_exact_output(self) -> None:
        b = self._bundle()
        name = t3_baseline.write_runner_log(str(b), "t3-run-addon-unit-60.log",
                                            self.OUTPUT, self.DELTA)
        self.assertEqual(name, "t3-run-addon-unit-60.log")
        self.assertEqual((b / name).read_text(encoding="utf-8"), self.OUTPUT)

    def test_green_writes_nothing(self) -> None:
        b = self._bundle()
        self.assertIsNone(
            t3_baseline.write_runner_log(str(b), "t3-x.log", self.OUTPUT, self.GREEN))
        self.assertEqual(list(b.iterdir()), [])

    def test_no_bundle_writes_nothing(self) -> None:
        # $PDCA_BUNDLE unset (CI working-tree re-gate) → nothing to persist.
        self.assertIsNone(
            t3_baseline.write_runner_log(None, "t3-x.log", self.OUTPUT, self.DELTA))

    def test_opaque_exit_delta_summary_gets_pointer(self) -> None:
        # End-to-end shape: the unexplained-nonzero delta summary, with the pointer
        # the caller appends — the human now has a file to read, not just the signature.
        v = t3_baseline.classify({}, 2, "weird crash, no JUnit", {})
        self.assertEqual(v["verdict"], "delta")
        b = self._bundle()
        log = t3_baseline.write_runner_log(str(b), "t3-run-addon-unit-60.log",
                                           "weird crash, no JUnit", v)
        v["summary"] += f" — raw runner output: {log}"
        self.assertIn("raw runner output: t3-run-addon-unit-60.log", v["summary"])


if __name__ == "__main__":
    unittest.main()
