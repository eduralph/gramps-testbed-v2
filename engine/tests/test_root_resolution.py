"""Regression guard: engine runners resolve their roots correctly and portably.

The gramps engine was ported into this harness from the `gramps-testbed`
reference repo, where the wrappers (a) resolved the repo root via
``git rev-parse --show-toplevel`` and (b) hardcoded the literal repo name
``gramps-testbed`` in docker-build and container paths. Neither holds here: this
instance is named differently and need not be a git repo. The port replaced both
with a ``pdca.toml`` marker-walk (matching ``pdca_harness.config._find_root``) and
``$ENGINE``/``$WORKSPACE``/``$TESTBED_NAME`` derivation.

This test pins that port so it cannot silently regress. For each engine wrapper it
**evaluates the script's own resolver block** in ``bash`` from an unrelated working
directory (substituting the real path for ``${BASH_SOURCE[0]}``) and asserts the
resolved roots, plus a structural check that the brittle patterns
(``git rev-parse``, a hardcoded ``gramps-testbed`` path literal, a fixed-depth
``../..`` walk) do not reappear in the resolver. Depth-agnostic: it asserts the
resolved *result*, so it keeps guarding wherever the engine is moved next.
"""

# ------------------------
# Python modules
# ------------------------
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

# engine/tests/this_file -> parents[2] is the repo root (the dir with pdca.toml).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Each engine wrapper and the roots its resolver must produce. Explicit (not
# globbed) so a newly added runner that forgets the robust resolution surfaces
# here as a missing-file failure, prompting the author to add it to the guard.
_RE = {  # the roots each kind of runner resolves
    "full": {
        "REPO_ROOT": str(REPO_ROOT),
        "ENGINE": str(REPO_ROOT / "engine"),
        "WORKSPACE": str(REPO_ROOT.parent),
        "TESTBED_NAME": REPO_ROOT.name,
    },
    "engine_ws": {
        "REPO_ROOT": str(REPO_ROOT),
        "ENGINE": str(REPO_ROOT / "engine"),
        "WORKSPACE": str(REPO_ROOT.parent),
    },
}
SPECS = {
    "engine/scripts/ubuntu/run-unit.sh": _RE["full"],
    "engine/scripts/ubuntu/run-addon-unit.sh": _RE["full"],
    "engine/scripts/ubuntu/run-verify.sh": _RE["engine_ws"],
    "engine/scripts/ubuntu/rebuild-image.sh": _RE["engine_ws"],
    "engine/scripts/ubuntu/clean-build.sh": _RE["engine_ws"],
    "engine/scripts/bootstrap-forks.sh": {
        "TESTBED": str(REPO_ROOT),
        "WORKSPACE": str(REPO_ROOT.parent),
    },
}

_ASSIGN = re.compile(r"^(REPO_ROOT|ENGINE|WORKSPACE|TESTBED_NAME|TESTBED)=")
_FIXED_DEPTH_WALK = re.compile(r"\.\./\.\.")


def _resolver_block(script: Path) -> str:
    """The script's root-resolution region: the `_find_repo_root` helper through
    the last root assignment. Isolating it keeps the structural checks off the
    rest of the script (e.g. the image tag legitimately contains 'gramps-testbed',
    and the docker invocation legitimately mentions /workspace/gramps)."""
    lines = script.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("_find_repo_root()"))
    end = max(i for i, ln in enumerate(lines) if _ASSIGN.match(ln))
    return "\n".join(lines[start : end + 1])


# ------------------------------------------------------------
#
# EngineRootResolutionTest
#
# ------------------------------------------------------------
class EngineRootResolutionTest(unittest.TestCase):
    """Every engine wrapper resolves its roots correctly, portably, git-free."""

    def test_all_wrappers_present(self) -> None:
        for rel in SPECS:
            with self.subTest(wrapper=rel):
                self.assertTrue(
                    (REPO_ROOT / rel).is_file(),
                    f"{rel} is missing -- update SPECS (and the guard) if it moved",
                )

    def test_resolver_is_marker_based_not_git_or_hardcoded(self) -> None:
        for rel in SPECS:
            block = _resolver_block(REPO_ROOT / rel)
            with self.subTest(wrapper=rel):
                self.assertIn(
                    "pdca.toml", block,
                    f"{rel}: root must be found via the pdca.toml marker",
                )
                self.assertNotIn(
                    "rev-parse", block,
                    f"{rel}: resolver must not depend on git (this instance may not be one)",
                )
                self.assertNotIn(
                    "gramps-testbed", block,
                    f"{rel}: resolver must not hardcode a repo name -- derive from the root",
                )
                self.assertIsNone(
                    _FIXED_DEPTH_WALK.search(block),
                    f"{rel}: reintroduced a fixed-depth `../..` walk -- the fragility the "
                    f"port removed; resolve via the pdca.toml marker instead",
                )

    @unittest.skipUnless(shutil.which("bash"), "bash required to evaluate the resolver")
    def test_resolver_yields_correct_roots(self) -> None:
        """Evaluate each script's real resolver lines from /tmp and check the roots."""
        for rel, expected in SPECS.items():
            script = REPO_ROOT / rel
            block = _resolver_block(script).replace(
                '"${BASH_SOURCE[0]}"', f'"{script}"'
            )
            names = list(expected)
            program = (
                "set -euo pipefail\n"
                + block + "\n"
                + "".join(f'printf "%s\\n" "${{{n}}}"\n' for n in names)
            )
            with self.subTest(wrapper=rel):
                result = subprocess.run(
                    ["bash", "-c", program],
                    cwd=os.environ.get("TMPDIR", "/tmp"),
                    capture_output=True, text=True,
                )
                self.assertEqual(
                    result.returncode, 0, f"{rel}: resolver failed:\n{result.stderr}"
                )
                got = dict(zip(names, result.stdout.splitlines()))
                for name, want in expected.items():
                    self.assertEqual(
                        os.path.realpath(got.get(name, "")),
                        os.path.realpath(want),
                        f"{rel}: {name} resolved to {got.get(name)!r}, expected {want!r}",
                    )


if __name__ == "__main__":
    unittest.main()
