"""requires_mod name-resolution gate (issue testbed-requires-mod-name-gate).

The testbed derives and pip-installs each addon's ``requires_mod`` via
``engine/scripts/lib/addon_python_deps.py`` (mapping PIL→Pillow for *install*)
but historically never validated that a declared name actually *resolves*. A
declared ``requires_mod`` value is the importable module name Gramps verifies
at runtime via ``importlib.util.find_spec`` — see ``gramps/gen/utils/
requirements.py`` ``Requirements.check_mod`` (``find_spec(module)`` on the
declared name). So an addon that declares the PyPI *distribution* name by
mistake (``requires_mod=["Pillow"]``) pip-installs fine, yet
``find_spec("Pillow")`` is ``None``, so Gramps silently marks the addon as
missing its dependency — and the testbed used to ship that undetected.

These tests drive the PRODUCTION gate (``addon_python_deps.unresolved_requires_mod``
and the ``--check-resolves`` CLI it backs), not a copy. They use a name that is
installed under a *different* import name (``"Pillow"``: the package is present
as ``PIL``, so ``find_spec("Pillow")`` is ``None`` — the exact Pillow/PIL trap)
to model "installs but does not import", and a stdlib name (``"json"``) for the
resolves case — both decided by the same ``find_spec`` Gramps uses, so the test
needs no network and no pip.

Stdlib + a temp-dir fixture only: no ``gi`` / ``gramps.gui`` import, so it runs
headless. This is a unit test of the shared CI library (sibling to
``test_lib_helpers.py``), not a per-addon ``<Addon>/tests/`` test.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB))

import addon_python_deps  # noqa: E402

# A real installed package whose IMPORT name differs from this DISTRIBUTION
# name: pip resolves "Pillow" and installs it, but it imports as "PIL", so
# find_spec("Pillow") is None. This is the production trap the gate must catch.
# Guard the assumption so the fixture stays honest across environments.
_INSTALLS_BUT_NOT_IMPORTABLE = "Pillow"
_IMPORTABLE = "json"  # stdlib, always resolves


class FixtureAssumptions(unittest.TestCase):
    def test_find_spec_models_the_pillow_trap(self) -> None:
        # The whole fixture rests on this: "Pillow" must NOT resolve (it is the
        # distribution name, not the import name) while a real module does.
        self.assertIsNone(
            importlib.util.find_spec(_INSTALLS_BUT_NOT_IMPORTABLE),
            f"{_INSTALLS_BUT_NOT_IMPORTABLE!r} unexpectedly resolves here; the "
            "fixture assumes it is installed only under its import name (PIL)",
        )
        self.assertIsNotNone(importlib.util.find_spec(_IMPORTABLE))


class RequiresModResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _addon(self, name: str, gpr_body: str) -> None:
        d = self.tmp / name
        d.mkdir()
        (d / f"{name}.gpr.py").write_text(gpr_body, encoding="utf-8")

    # --- the production function -----------------------------------------
    def test_wrong_name_is_reported_with_its_addon(self) -> None:
        # The repro from the brief: declaring the PyPI distribution name on the
        # addon's .gpr.py. It installs but find_spec(...) is None, so the gate
        # must flag it, naming the addon AND the bad declaration.
        self._addon(
            "EditExifMetadata",
            f'requires_mod = ["{_INSTALLS_BUT_NOT_IMPORTABLE}"]\n',
        )
        self.assertEqual(
            addon_python_deps.unresolved_requires_mod(str(self.tmp)),
            [("EditExifMetadata", _INSTALLS_BUT_NOT_IMPORTABLE)],
        )

    def test_resolvable_name_passes(self) -> None:
        # A declared name that find_spec resolves is clean — no false positive.
        self._addon("Good", f'requires_mod = ["{_IMPORTABLE}"]\n')
        self.assertEqual(addon_python_deps.unresolved_requires_mod(str(self.tmp)), [])

    def test_checks_raw_import_name_not_the_install_mapped_one(self) -> None:
        # PIL maps to Pillow for *install*, but the gate verifies the RAW
        # declared name ("PIL"), which is what Gramps imports — so a correct
        # PIL declaration must PASS even though the install union says "Pillow".
        self._addon("EditExifMetadata", 'requires_mod = ["PIL"]\n')
        self.assertIn("Pillow", addon_python_deps.requires_mod_union(str(self.tmp)))
        self.assertEqual(addon_python_deps.unresolved_requires_mod(str(self.tmp)), [])

    def test_addon_with_no_requires_mod_is_clean(self) -> None:
        self._addon("Plain", "register(GENERAL, id='x')\n")
        self.assertEqual(addon_python_deps.unresolved_requires_mod(str(self.tmp)), [])

    # --- the CLI the run-addon-unit.sh gate actually invokes -------------
    def _check_resolves_rc(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(LIB / "addon_python_deps.py"),
                "--check-resolves",
                str(self.tmp),
            ],
            capture_output=True,
            text=True,
        )

    def test_cli_exits_nonzero_and_names_the_addon_on_a_bad_declaration(self) -> None:
        self._addon(
            "EditExifMetadata",
            f'requires_mod = ["{_INSTALLS_BUT_NOT_IMPORTABLE}"]\n',
        )
        proc = self._check_resolves_rc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("EditExifMetadata", proc.stderr)
        self.assertIn(_INSTALLS_BUT_NOT_IMPORTABLE, proc.stderr)

    def test_cli_exits_zero_when_every_name_resolves(self) -> None:
        self._addon("Good", f'requires_mod = ["{_IMPORTABLE}"]\n')
        proc = self._check_resolves_rc()
        self.assertEqual(proc.returncode, 0, proc.stderr)


class ProductionGateIsWired(unittest.TestCase):
    """The run-addon-unit.sh CI flow must actually run the resolution gate and
    FAIL on a non-zero exit — guarding against the gate being defined but never
    invoked (the bug was a *missing* gate)."""

    RUNNER = (
        Path(__file__).resolve().parents[1] / "scripts" / "ubuntu" / "run-addon-unit.sh"
    )

    def test_runner_invokes_check_resolves_and_fails_on_it(self) -> None:
        src = self.RUNNER.read_text(encoding="utf-8")
        self.assertIn("--check-resolves", src)
        # The non-zero branch must set fail=1 so CI actually goes red.
        self.assertRegex(
            src,
            r"--check-resolves[\s\S]{0,200}?else\s*\n\s*fail=1",
            "run-addon-unit.sh must FAIL (fail=1) when --check-resolves exits "
            "non-zero",
        )


if __name__ == "__main__":
    unittest.main()
