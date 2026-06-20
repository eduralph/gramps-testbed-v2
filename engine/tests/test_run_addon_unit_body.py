"""Regression guard: run-addon-unit.sh runs its container body via a QUOTED HEREDOC.

The whole addon-unit logic runs inside one container shell body. It used to be inlined
as ``bash -c '<single-quoted body>'`` — a form the FIRST literal apostrophe in the body
closes, truncating the script so bash exits before any test runs (testbed #127), and
``t3_baseline`` then sees a non-zero exit with no parsed JUnit (issue #159). The body was
kept apostrophe-free only by convention.

The fix builds the body as a quoted heredoc (``read -d '' ADDON_UNIT_BODY <<'EOF'``) and
runs ``bash -c "$ADDON_UNIT_BODY"`` — the same mechanism run-verify.sh's ``INNER`` uses.
The body reaching the container is byte-identical; a literal apostrophe can no longer
break it. These checks lock that in (offline; the behavioral run is Docker, out of band).
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "engine/scripts/ubuntu/run-addon-unit.sh"


class RunAddonUnitBodyStructure(unittest.TestCase):
    def setUp(self) -> None:
        self.body = SCRIPT.read_text()

    def test_body_built_as_quoted_heredoc(self) -> None:
        self.assertIn("read -r -d '' ADDON_UNIT_BODY <<'ADDON_UNIT_EOF'", self.body)
        self.assertIn("\nADDON_UNIT_EOF\n", self.body)
        self.assertIn('bash -c "$ADDON_UNIT_BODY"', self.body)

    def test_no_inline_single_quoted_bash_c_body(self) -> None:
        # The fragile opener (a lone `  bash -c '` line introducing an inline body) is gone.
        self.assertNotIn("\n  bash -c '\n", self.body,
                         "the container body must not be inlined as bash -c '<single-quoted>'")

    def test_whole_script_parses(self) -> None:
        rc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(rc.returncode, 0, rc.stderr)


@unittest.skipUnless(shutil.which("bash"), "bash required")
class HeredocApostropheSafety(unittest.TestCase):
    """The mechanism itself: a quoted heredoc body carrying a literal apostrophe survives,
    where the old single-quoted-inline form would have broken. Demonstrated on a minimal
    body so it does not depend on the container environment."""

    def _run(self, program: str) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", "-c", program], capture_output=True, text=True)

    def test_apostrophe_in_heredoc_body_survives(self) -> None:
        # A body line with a single-quoted sed (a bare apostrophe) — the exact thing that
        # broke the old inline form. Via the heredoc it round-trips and runs fine.
        prog = (
            "set -euo pipefail\n"
            "read -r -d '' BODY <<'EOF' || true\n"
            "echo \"x\" | sed 's/x/ok/'\n"
            "EOF\n"
            'bash -c "$BODY"\n'
        )
        res = self._run(prog)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "ok")


if __name__ == "__main__":
    unittest.main()
