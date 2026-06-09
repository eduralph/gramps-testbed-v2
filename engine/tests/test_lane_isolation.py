"""Regression guard: the gate runners scope their per-version target worktrees to
the in-driver concurrency lane (docs 09).

Under a worker pool (``[driver].lanes`` / ``PDCA_LANES`` > 1) the driver pins each
worker to a slot and exposes it as ``$PDCA_LANE``; per the pdca.toml contract a gate
that touches a shared mutable resource outside its bundle MUST name it by that slot.
The gramps gates patch the per-version worktrees ``$WORKSPACE/gramps-6.{0,1}`` (and
``addons-source-6.{0,1}``, ``gramps-<ver>-essential``) — shared across the one
workspace — so two concurrent lanes would otherwise collide on the same checkout (the
refuse-on-dirty guard would trip as a loud backstop). Each runner now derives
``LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"`` and appends it to every per-version path,
so lane K patches its own ``gramps-6.1-lane$K``. Serial runs (no ``$PDCA_LANE``) get an
empty suffix → the bare worktrees, byte-for-byte unchanged.

Two checks, both stdlib-only and Docker-free:

1. **Behavioural** — evaluate each script's *real* ``LANE_SFX=`` definition (grepped
   from the file, anchor-drift style like test_root_resolution) and assert the suffix
   it yields for unset / 0 / 2.
2. **Structural** — every per-version worktree *assignment* in the runners includes
   ``$LANE_SFX``, so a new path can't silently re-introduce the cross-lane collision.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

# engine/tests/this_file -> parents[2] is the repo root (the dir with pdca.toml).
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = {
    name: REPO_ROOT / "engine/scripts/ubuntu" / name
    for name in ("run-verify.sh", "run-addon-unit.sh", "run-addon-interface.sh")
}

_LANE_DEF = re.compile(r'^\s*LANE_SFX="\$\{PDCA_LANE:\+-lane\$PDCA_LANE\}"\s*$', re.M)

# A per-version worktree assignment: one of the path vars set to $WORKSPACE/gramps-…
# or $WORKSPACE/addons-source-… with a version segment (the bare primary "$WORKSPACE/
# gramps" has no '-' and is the intentional serial dev fallback, not lane-scoped).
_PATH_ASSIGN = re.compile(
    r'(?:gramps_dir|repo|ess|GRAMPS_DIR|ADDONS_DIR)='
    r'(?:"?\$\{gramps_override:-)?"?\$WORKSPACE/(?:gramps|addons-source)-'
)


def _lane_def_line(script: Path) -> str:
    m = _LANE_DEF.search(script.read_text())
    assert m, f"{script.name}: no LANE_SFX definition found"
    return m.group(0).strip()


@unittest.skipUnless(shutil.which("bash"), "bash required to evaluate the suffix")
class LaneSuffixContractTest(unittest.TestCase):
    """Each runner's own LANE_SFX definition yields the lane-scoped suffix."""

    def _suffix(self, script: Path, lane: str | None) -> str:
        # Eval the script's verbatim LANE_SFX= line, then echo it — the real logic.
        env_line = "" if lane is None else f'export PDCA_LANE={lane}\n'
        program = env_line + _lane_def_line(script) + '\nprintf "%s" "$LANE_SFX"\n'
        res = subprocess.run(["bash", "-c", program], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def test_serial_is_bare(self) -> None:
        for name, script in SCRIPTS.items():
            self.assertEqual(self._suffix(script, None), "",
                             f"{name}: serial run (no PDCA_LANE) must yield no suffix")

    def test_lane_zero_and_two(self) -> None:
        for name, script in SCRIPTS.items():
            self.assertEqual(self._suffix(script, "0"), "-lane0", name)
            self.assertEqual(self._suffix(script, "2"), "-lane2", name)


class LanePathStructureTest(unittest.TestCase):
    """Every per-version worktree assignment applies $LANE_SFX — no bare path can
    re-introduce the cross-lane collision the suffix exists to prevent."""

    def test_every_versioned_worktree_assignment_is_lane_scoped(self) -> None:
        for name, script in SCRIPTS.items():
            body = script.read_text()
            self.assertTrue(_LANE_DEF.search(body), f"{name}: missing LANE_SFX definition")
            offenders = [
                ln for ln in body.splitlines()
                if _PATH_ASSIGN.search(ln) and "$LANE_SFX" not in ln
            ]
            self.assertEqual(
                offenders, [],
                f"{name}: per-version worktree path(s) not scoped by $LANE_SFX — "
                f"two concurrent lanes would patch the same checkout:\n  "
                + "\n  ".join(offenders),
            )


if __name__ == "__main__":
    unittest.main()
