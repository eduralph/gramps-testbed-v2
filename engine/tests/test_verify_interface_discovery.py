"""Regression guard: run-verify-interface.sh discovers a bundle's committed GUI repro.

The C4-verify-interface gate (#157) proves a fix at the GUI level by running the bug's
committed AT-SPI/dogtail repro — ``engine/interface/test_bug_<id>_<slug>.py``, NOT shipped
in ``patch.diff`` — RED on the unpatched worktree and GREEN on the patched one. The gate
derives the repro from the bundle id (``results/issue_<id>``). Two real traps it must clear:

  * the filename's bug number is ZERO-PADDED (``test_bug_0013864_*``) while the bundle id is
    not (``13864``), so a naive ``test_bug_${id}_*`` glob finds nothing; and
  * a missing repro must route to ``PDCA-UNVERIFIABLE`` (exit 77 → §6 NEEDS-HUMAN under the
    C6 accept-guard), never a hard fail or a silent pass.

This evaluates the script's *real* ``_bundle_id`` / ``_find_repro`` helpers (extracted from
the script, exactly like test_verify_classification.py evaluates run-verify.sh's helpers),
plus structural checks that the soundness guards (exit-77 on no-repro, red-before-green with
no mid-run un-apply, the skipped-red→unverifiable guard) stay in the script.

NOTE: these are *mechanical* checks — they prove discovery + structure only. The actual
red→green GUI behavior (Xvfb/at-spi bring-up, the repro failing unpatched and passing
patched, the editable-install liveness across legs) is verified by an out-of-band Docker run
(``PDCA_BUNDLE=… ./engine/scripts/ubuntu/run-verify-interface.sh``), not here.
"""

# ------------------------
# Python modules
# ------------------------
import os
import shutil
import subprocess
import unittest
from pathlib import Path

# engine/tests/this_file -> parents[2] is the repo root (the dir with pdca.toml).
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "engine/scripts/ubuntu/run-verify-interface.sh"
_PATH = os.environ.get("PATH", "/usr/bin:/bin")

_BEGIN = "# --- interface repro discovery helpers"
_END = "# --- end interface repro discovery helpers ---"


def _helpers_block() -> str:
    """The script's ``_bundle_id`` / ``_find_repro`` helper region, verbatim."""
    lines = SCRIPT.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(_BEGIN))
    end = next(i for i, ln in enumerate(lines) if ln.startswith(_END))
    return "\n".join(lines[start : end + 1])


@unittest.skipUnless(shutil.which("bash"), "bash required to evaluate the helpers")
class InterfaceReproDiscoveryTest(unittest.TestCase):
    """The real run-verify-interface.sh helpers parse the id and find the repro."""

    def setUp(self) -> None:
        self._tmpdir = __import__("tempfile").TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        (self.tmp / "interface").mkdir()

    def _run(self, body: str) -> subprocess.CompletedProcess:
        program = "set -euo pipefail\n" + _helpers_block() + "\n" + body
        return subprocess.run(
            ["bash", "-c", program],
            capture_output=True, text=True,
            env={"TMP": str(self.tmp), "PATH": _PATH},
        )

    def _touch(self, name: str) -> None:
        (self.tmp / "interface" / name).touch()

    def test_id_parsed_from_bundle_dir(self) -> None:
        res = self._run('_bundle_id /x/results/issue_13864')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "13864")

    def test_glob_matches_zero_padded_repro(self) -> None:
        # The padding trap: id 13864 (unpadded) must find test_bug_0013864_* (padded).
        self._touch("test_bug_0013864_dashboard_column_crash.py")
        res = self._run('_find_repro 13864 "$TMP"')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            res.stdout.strip(),
            str(self.tmp / "interface/test_bug_0013864_dashboard_column_crash.py"),
        )

    def test_no_repro_returns_empty(self) -> None:
        # No file → no output (NOT one blank line — that would mis-read as a single match).
        res = self._run('_find_repro 13864 "$TMP"')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "")
        self.assertEqual(res.stdout, "", "empty match must emit nothing, not a blank line")

    def test_multiple_repros_listed(self) -> None:
        # Two repros for one id → both lines (the script treats >1 as ambiguous → exit 77).
        self._touch("test_bug_0013864_dashboard_column_crash.py")
        self._touch("test_bug_13864_other_repro.py")
        res = self._run('_find_repro 13864 "$TMP"')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(len(res.stdout.split()), 2)

    def test_trailing_underscore_bounds_the_numeric_run(self) -> None:
        # id 1386 must NOT match 0013864 (the trailing `_` bounds the number).
        self._touch("test_bug_0013864_dashboard_column_crash.py")
        res = self._run('_find_repro 1386 "$TMP"')
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "")


class InterfaceVerifyScriptStructureTest(unittest.TestCase):
    """The soundness guards must stay in the script."""

    def setUp(self) -> None:
        self.body = SCRIPT.read_text()

    def test_no_repro_is_unverifiable_not_fail(self) -> None:
        # The 0-match and ambiguous-match cases declare PDCA-UNVERIFIABLE + exit 77, so a
        # missing repro routes to §6 NEEDS-HUMAN, not a hard fail or a silent pass.
        self.assertIn("PDCA-UNVERIFIABLE:", self.body)
        self.assertIn("exit 77", self.body)
        self.assertGreaterEqual(
            self.body.count("PDCA-UNVERIFIABLE:"), 3,
            "the no-id, no-repro, ambiguous-repro and skipped-red cases each declare unverifiable",
        )

    def test_skipped_red_leg_is_unverifiable(self) -> None:
        # A repro that SKIPPED on the unpatched tree (e.g. a missing locale) exits 0; that
        # must NOT read as red-PASS — it routes to unverifiable. The guard must be present.
        self.assertIn("red_is_unverifiable", self.body)
        self.assertIn("SKIPPED", self.body)
        # the guard counts JUnit skips against total tests (no-test or all-skipped → unverifiable)
        self.assertIn("skipped", self.body)

    def test_red_runs_before_green_with_no_mid_run_unapply(self) -> None:
        # Red (unpatched) must precede the `git apply`, which must precede green (patched);
        # there is no revert between the legs (green is the last leg; the EXIT trap cleans up).
        red = self.body.index("run_repro red")
        apply_ = self.body.index("apply \"$PATCH\"")
        green = self.body.index("run_repro green")
        self.assertLess(red, apply_, "red leg must run before the patch is applied")
        self.assertLess(apply_, green, "green leg must run after the patch is applied")

    def test_advisory_repro_not_shipped_in_patch(self) -> None:
        # Discovery is from engine/interface, not from patch.diff (the load-bearing asymmetry).
        self.assertIn("_find_repro", self.body)
        self.assertIn("engine/interface/test_bug", self.body)


if __name__ == "__main__":
    unittest.main()
