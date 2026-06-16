"""Per-module addon-test wall clock (issue testbed-per-module-timeout).

``run-addon-unit.sh`` used to run a whole addon's suite in ONE
``python3 -m xmlrunner mod_a mod_b …`` invocation bounded only by the outer
whole-job ``timeout``. A single hanging module therefore consumed the entire job
budget; on expiry the container was killed wholesale, the log named no culprit, and
every not-yet-run module was lost. ``engine/scripts/lib/run_addon_modules.py`` now
runs each module in its own subprocess under a *per-module* timeout, killing and
**naming** a hung module while the **remaining modules still run**.

These tests are stdlib-only and GUI-import-free (no ``gi`` / ``gramps.gui``), so
they run headless. The hanging fixture is a real ``time.sleep`` test module driven
through the **production** command (``python3 -m xmlrunner <module> -o <out> -v``)
the helper issues — not a re-implementation of it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB))

import run_addon_modules  # noqa: E402

RUNNER = (
    Path(__file__).resolve().parents[1] / "scripts" / "ubuntu" / "run-addon-unit.sh"
)

# A test that hangs far longer than any per-module timeout this suite sets, and a
# trivially-passing sibling. Both are plain stdlib unittest — no GUI imports.
_HANG = """\
import time, unittest


class Hang(unittest.TestCase):
    def test_hang(self):
        time.sleep(120)
"""

_FAST = """\
import unittest


class Fast(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(1 + 1, 2)
"""


class PerModuleTimeout(unittest.TestCase):
    """A hang is killed at the per-module timeout, named, and siblings still run."""

    PER_MODULE = 3.0  # seconds; the hang sleeps 120s, so a wait-out is unmistakable

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        # A fake addons-source package: <Addon>/tests/test_*.py, importable by the
        # dotted module path xmlrunner is given — mirrors the real layout.
        addon = self.tmp / "FakeAddon"
        tests = addon / "tests"
        tests.mkdir(parents=True)
        (addon / "__init__.py").write_text("", encoding="utf-8")
        (tests / "__init__.py").write_text("", encoding="utf-8")
        (tests / "test_hang.py").write_text(_HANG, encoding="utf-8")
        (tests / "test_fast.py").write_text(_FAST, encoding="utf-8")
        self.out = self.tmp / "out"
        self.out.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hang_is_killed_named_and_sibling_runs(self) -> None:
        # Hang FIRST, fast sibling SECOND: proves the sibling runs *after* the hang
        # is contained, not merely that an unrelated module ran.
        modules = ["FakeAddon.tests.test_hang", "FakeAddon.tests.test_fast"]
        start = time.monotonic()
        results = run_addon_modules.run_modules(
            modules, str(self.out), self.PER_MODULE, cwd=str(self.tmp)
        )
        elapsed = time.monotonic() - start

        # 1. The hang was KILLED at the per-module timeout, not waited out: the only
        #    sleep in play is 120s, so finishing in well under that proves the kill.
        self.assertLess(
            elapsed,
            60,
            "the whole run took too long — the hanging module was not killed at the "
            "per-module timeout",
        )

        # 2. The hang is reported BY NAME as a timeout (attributable), …
        self.assertEqual(
            results["FakeAddon.tests.test_hang"], run_addon_modules.TIMEOUT
        )
        timeout_xml = self.out / "TEST-FakeAddon.tests.test_hang-timeout.xml"
        self.assertTrue(
            timeout_xml.is_file(),
            "no named synthetic JUnit was written for the timed-out module",
        )
        self.assertIn("FakeAddon.tests.test_hang", timeout_xml.read_text("utf-8"))

        # 3. … and the REMAINING module still ran and passed.
        self.assertEqual(results["FakeAddon.tests.test_fast"], run_addon_modules.PASS)
        self.assertTrue(
            list(self.out.glob("*test_fast*.xml")),
            "the sibling module produced no JUnit — it did not run after the hang",
        )

    def test_cli_exit_code_signals_timeout(self) -> None:
        # The CLI the runner invokes returns 124 (GNU timeout convention) when a
        # module hangs, so run-addon-unit.sh can distinguish a hang from a plain fail.
        import os

        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            rc = run_addon_modules.main(
                [
                    "--timeout",
                    str(self.PER_MODULE),
                    "-o",
                    str(self.out),
                    "FakeAddon.tests.test_hang",
                    "FakeAddon.tests.test_fast",
                ]
            )
        finally:
            os.chdir(cwd)
        self.assertEqual(rc, run_addon_modules.EXIT_TIMEOUT)

    def test_all_passing_exits_zero(self) -> None:
        results = run_addon_modules.run_modules(
            ["FakeAddon.tests.test_fast"],
            str(self.out),
            self.PER_MODULE,
            cwd=str(self.tmp),
        )
        self.assertEqual(results["FakeAddon.tests.test_fast"], run_addon_modules.PASS)
        self.assertEqual(
            run_addon_modules._exit_code(results), run_addon_modules.EXIT_OK
        )


class RunnerWiresPerModuleTimeout(unittest.TestCase):
    """The production runner must route the per-module loop through the helper.

    A structural guard: if a future edit reverts to a single batched
    ``xmlrunner "${modules[@]}"`` (no per-module wall clock) or drops the
    timeout-naming, these turn red.
    """

    def test_runner_calls_the_per_module_helper(self) -> None:
        src = RUNNER.read_text(encoding="utf-8")
        self.assertIn(
            "run_addon_modules.py",
            src,
            "run-addon-unit.sh must drive the per-module loop through "
            "run_addon_modules.py",
        )
        self.assertRegex(
            src,
            r"run_addon_modules\.py[^\n]*\n[^\n]*--timeout \"\$MODULE_TIMEOUT\"",
            "run-addon-unit.sh must pass a per-module --timeout to the helper",
        )

    def test_runner_no_longer_batches_all_modules(self) -> None:
        src = RUNNER.read_text(encoding="utf-8")
        self.assertNotRegex(
            src,
            r"python3 -m xmlrunner \"\$\{modules\[@\]\}\"",
            "the per-addon loop must not run all modules in one unbounded xmlrunner "
            "invocation — that is the whole-batch hang this fix removes",
        )

    def test_runner_names_the_timed_out_module_in_the_summary(self) -> None:
        src = RUNNER.read_text(encoding="utf-8")
        self.assertRegex(
            src,
            r"rc.*-eq 124",
            "run-addon-unit.sh must special-case the helper's 124 (timeout) exit "
            "to attribute the hang",
        )
        self.assertIn(
            "module-timeout:",
            src,
            "run-addon-unit.sh must extract the helper's `module-timeout:` lines to "
            "name the culprit in the addon summary",
        )


class RunnerBashCBodyQuoting(unittest.TestCase):
    """The per-addon loop runs inside a single-quoted `bash -c '…'` body; a bare
    apostrophe anywhere in it closes that quote early and bash exits before any test
    runs (testbed #127 — the module-timeout `sed '…'` did exactly that, dead T3-addon-unit
    since 8b11013). Guard: the body carries no bare apostrophe and parses with `bash -n`."""

    def _body(self) -> tuple[str, list[int]]:
        """The `bash -c '…'` body (with `'\\''` un-escaped) + any bare-apostrophe line nos."""
        lines = RUNNER.read_text(encoding="utf-8").splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "bash -c '")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("' ||"))
        body_lines = lines[start + 1 : end]
        # a bare ' is any apostrophe left after removing the legal '\'' escape sequence
        bare = [start + 2 + j for j, l in enumerate(body_lines) if "'" in l.replace("'\\''", "")]
        return "\n".join(body_lines).replace("'\\''", "'"), bare

    def test_body_has_no_bare_apostrophe(self) -> None:
        _, bare = self._body()
        self.assertEqual(bare, [], f"bare apostrophe(s) in the bash -c body at line(s) {bare} "
                                   "— they close the single-quoted body early (testbed #127)")

    @unittest.skipUnless(shutil.which("bash"), "bash required")
    def test_body_parses(self) -> None:
        body, _ = self._body()
        r = subprocess.run(["bash", "-n", "-c", body], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"bash -c body does not parse:\n{r.stderr}")


if __name__ == "__main__":
    unittest.main()
