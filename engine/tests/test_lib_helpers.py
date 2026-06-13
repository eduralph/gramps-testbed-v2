"""Unit tests for the engine lib helpers (stdlib only, synthetic fixtures).

`addon_python_deps` and `junit_coverage` are pure scanners — exercised here with
tiny in-memory fixtures so the tests are fast and need no addons-source checkout.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "lib"
CONF = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(CONF))

import addon_python_deps  # noqa: E402
import addon_system_deps  # noqa: E402
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


class AddonSatisfiability(unittest.TestCase):
    """Platform-aware all-skip tolerance (issue testbed-honest-skip).

    A wholly-skipped addon suite is *honest* iff it FAILs only when coverage was
    actually lost — the addon's declared system deps ARE packaged on this
    platform, yet every test skipped — and is tolerated iff a declared
    ``requires_gi`` / ``requires_exe`` has no package here. ``addon_system_deps``
    is the single authority on platform satisfiability; ``run-addon-unit.sh``
    consults it at the all-skip branch.
    """

    SCRIPT = LIB / "addon_system_deps.py"
    RUNNER = (
        Path(__file__).resolve().parents[1] / "scripts" / "ubuntu" / "run-addon-unit.sh"
    )

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _addon(self, name: str, gpr_body: str) -> Path:
        d = self.tmp / name
        d.mkdir()
        (d / f"{name}.gpr.py").write_text(gpr_body, encoding="utf-8")
        return d

    # --- the predicate itself --------------------------------------------
    def test_unsatisfiable_when_declared_gi_has_no_package(self) -> None:
        # PlaceCoordinateGramplet's exact case: GeocodeGlib maps to None on every
        # platform (install: False), so an all-skip here is an EXPECTED skip.
        d = self._addon(
            "PlaceCoordinateGramplet", 'requires_gi = [("GeocodeGlib", "1.0")]\n'
        )
        self.assertFalse(addon_system_deps.addon_satisfiable_on(str(d), "ubuntu"))
        # Platform-aware, not addon-specific: still unsatisfiable on the windows lane.
        self.assertFalse(addon_system_deps.addon_satisfiable_on(str(d), "windows"))

    def test_unsatisfiable_when_declared_dep_is_unmapped(self) -> None:
        # A namespace with no map row at all is unsatisfiable (cannot be provided).
        d = self._addon("Mystery", 'requires_gi = [("NoSuchNamespace", "9.9")]\n')
        self.assertFalse(addon_system_deps.addon_satisfiable_on(str(d), "ubuntu"))

    def test_unsatisfiable_when_declared_exe_has_no_package(self) -> None:
        d = self._addon("NeedsTool", 'requires_exe = ["no_such_binary"]\n')
        self.assertFalse(addon_system_deps.addon_satisfiable_on(str(d), "ubuntu"))

    def test_satisfiable_when_every_declared_dep_maps(self) -> None:
        # GooCanvas -> gir1.2-goocanvas-2.0 and dot -> graphviz both map on ubuntu,
        # so an all-skip here is genuine coverage loss and must still FAIL.
        d = self._addon(
            "GraphView",
            'requires_gi = [("GooCanvas", "2.0")]\nrequires_exe = ["dot"]\n',
        )
        self.assertTrue(addon_system_deps.addon_satisfiable_on(str(d), "ubuntu"))
        self.assertTrue(addon_system_deps.addon_satisfiable_on(str(d), "windows"))

    def test_satisfiable_when_addon_declares_no_system_deps(self) -> None:
        d = self._addon("PurePython", "register(GENERAL, id='x')\n")
        self.assertTrue(addon_system_deps.addon_satisfiable_on(str(d), "ubuntu"))

    # --- runner-level: the exact predicate call run-addon-unit.sh makes ----
    # At the all-skip branch the runner does, on the ubuntu platform:
    #   if python3 addon_system_deps.py --satisfiable <dir> --platform ubuntu
    #   then  fail=1   (deps available, suite skipped -> genuine coverage loss)
    #   else  tolerate (expected platform skip)
    # so exit 0 == "FAIL the all-skip" and exit 1 == "tolerate it".
    def _cli_satisfiable_rc(self, addon_dir: Path) -> int:
        return subprocess.run(
            [
                sys.executable,
                str(self.SCRIPT),
                "--satisfiable",
                str(addon_dir),
                "--platform",
                "ubuntu",
            ]
        ).returncode

    def test_runner_tolerates_unsatisfiable_all_skip(self) -> None:
        d = self._addon(
            "PlaceCoordinateGramplet", 'requires_gi = [("GeocodeGlib", "1.0")]\n'
        )
        # exit 1 -> runner's `if … ; then fail; else tolerate` takes the else: SKIP.
        self.assertEqual(self._cli_satisfiable_rc(d), 1)

    def test_runner_fails_satisfiable_all_skip(self) -> None:
        d = self._addon("GraphView", 'requires_gi = [("GooCanvas", "2.0")]\n')
        # exit 0 -> runner's then-branch: fail=1 (genuine coverage loss FAILs).
        self.assertEqual(self._cli_satisfiable_rc(d), 0)

    def test_runner_routes_all_skip_through_the_predicate(self) -> None:
        # The production all-skip branch must consult the satisfiability predicate
        # and FAIL only on the satisfiable (exit-0) leg — not unconditionally.
        src = self.RUNNER.read_text(encoding="utf-8")
        self.assertRegex(
            src,
            r"--satisfiable[^\n]*--platform ubuntu; then\s*\n\s*fail=1",
            "run-addon-unit.sh all-skip branch must FAIL only when the addon is "
            "satisfiable on the platform (exit 0 -> fail=1)",
        )
        self.assertRegex(
            src,
            r"else\s*\n\s*summary_lines\+=\([^\n]*SKIP[^\n]*unsatisfiable",
            "run-addon-unit.sh must tolerate (SKIP) the all-skip when deps are "
            "unsatisfiable on the platform",
        )


if __name__ == "__main__":
    unittest.main()
