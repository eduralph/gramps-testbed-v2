"""Unit tests for the engine lib helpers (stdlib only, synthetic fixtures).

`addon_python_deps` and `junit_coverage` are pure scanners — exercised here with
tiny in-memory fixtures so the tests are fast and need no addons-source checkout.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "lib"
CONF = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(CONF))

import addon_python_deps  # noqa: E402
import junit_coverage  # noqa: E402
import synth_junit  # noqa: E402
import t3_baseline  # noqa: E402


class AddonPythonDeps(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _addon(self, name: str, gpr_body: str) -> None:
        d = self.tmp / name
        d.mkdir()
        (d / f"{name}.gpr.py").write_text(gpr_body, encoding="utf-8")

    def test_union_across_gpr_files(self) -> None:
        self._addon("AddonA", 'requires_mod = ["svgwrite", "networkx"]\n')
        self._addon("AddonB", 'requires_mod = ["networkx", "psycopg2"]\n')
        self.assertEqual(
            addon_python_deps.requires_mod_union(str(self.tmp)),
            ["networkx", "psycopg2", "svgwrite"],  # sorted union, deduped
        )

    def test_tolerant_of_non_literal(self) -> None:
        # A non-literal requires_mod is skipped, not fatal.
        self._addon("X", "requires_mod = [SOME_CONSTANT]\n")
        self._addon("Y", 'requires_mod = ["dbf"]\n')
        self.assertEqual(addon_python_deps.requires_mod_union(str(self.tmp)), ["dbf"])

    def test_empty_when_no_declarations(self) -> None:
        self._addon("Z", "register(GENERAL, id='z')\n")
        self.assertEqual(addon_python_deps.requires_mod_union(str(self.tmp)), [])

    def test_import_name_mapped_to_pip_distribution(self) -> None:
        # requires_mod holds the IMPORT name (doc 16 §Runtime: "PIL", not "Pillow");
        # the union maps it to the pip DISTRIBUTION so `pip install` resolves
        # (`pip install PIL` fails; the package is Pillow). issue_8653.
        self._addon("EditExifMetadata", 'requires_mod = ["PIL"]\n')
        self.assertEqual(
            addon_python_deps.requires_mod_union(str(self.tmp)), ["Pillow"]
        )


class SynthJunit(unittest.TestCase):
    """A collection crash (0 tests, no XML) becomes an attributable JUnit error."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_crash_is_parseable_and_named(self) -> None:
        log = self.tmp / "_run.log"
        log.write_text("Traceback …\nException: GraphViz is required\n", encoding="utf-8")
        out = synth_junit.write_crash(str(self.tmp), "GraphView", 1, str(log))
        self.assertTrue(out.is_file())
        # t3_baseline.parse_junit (flat glob) now sees the crash, named by addon.
        self.assertEqual(
            t3_baseline.parse_junit(self.tmp),
            {"GraphView.collection::import_or_collection": "error"},
        )


class JunitCoverage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sums_tests_and_skipped(self) -> None:
        (self.tmp / "a.xml").write_text('<testsuite tests="5" skipped="2"></testsuite>')
        (self.tmp / "b.xml").write_text('<testsuites><testsuite tests="3" skipped="1"/></testsuites>')
        self.assertEqual(junit_coverage.coverage(str(self.tmp)), (8, 3))

    def test_all_skipped_is_visible(self) -> None:
        # The reason this helper exists: tests == skipped (an all-skipped run).
        (self.tmp / "s.xml").write_text('<testsuite tests="8" skipped="8"/>')
        self.assertEqual(junit_coverage.coverage(str(self.tmp)), (8, 8))

    def test_ignores_unparseable(self) -> None:
        (self.tmp / "bad.xml").write_text("not xml <<<")
        self.assertEqual(junit_coverage.coverage(str(self.tmp)), (0, 0))


if __name__ == "__main__":
    unittest.main()
