"""Regression guard: run-verify.sh selects a fork verification base (issue #96).

An addon bundle whose brief declares `- **Verification base:** <remote>/<branch>`
verifies against a DEDICATED `addons-source-<ver>-fork` worktree (the fork's open PR
branch), single-leg, instead of the full clean matrix against the shared per-version
worktrees. The base-selection logic lives in a marked, self-contained block in
run-verify.sh; this test extracts that block (the same approach
`test_verify_classification` uses for the patch-classification helpers) and evaluates
its real functions under bash — no Docker — against fixture briefs.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

# engine/tests/this_file -> parents[2] is the repo root (the dir with pdca.toml).
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "engine/scripts/ubuntu/run-verify.sh"

_BEGIN = "# --- fork base selection"
_END = "# --- end fork base selection ---"


def _block() -> str:
    """The script's fork-base-selection block (the real functions), verbatim."""
    lines = SCRIPT.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(_BEGIN))
    end = next(i for i, ln in enumerate(lines) if ln.startswith(_END))
    return "\n".join(lines[start : end + 1])


def _run(env_setup: str, call: str) -> str:
    """Source the extracted block with `env_setup`, run `call`, return stripped stdout."""
    script = f"set -u\n{env_setup}\n{_block()}\n{call}\n"
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


class ForkLegs(unittest.TestCase):
    def test_fork_bundle_runs_its_single_version_leg(self) -> None:
        self.assertEqual(_run("MODE=addon; TARGET_VER=6.0; FORK_REF=origin/feature/x", "_fork_legs"), "6.0")

    def test_plain_addon_runs_the_full_matrix(self) -> None:
        self.assertEqual(_run("MODE=addon; TARGET_VER=6.0; FORK_REF=", "_fork_legs"), "6.0 6.1")

    def test_core_runs_its_target_version_only(self) -> None:
        self.assertEqual(_run("MODE=core; TARGET_VER=6.1; FORK_REF=", "_fork_legs"), "6.1")


class AddonRepo(unittest.TestCase):
    def test_fork_base_selects_the_fork_worktree(self) -> None:
        self.assertEqual(
            _run("WORKSPACE=/ws; LANE_SFX=; FORK_REF=origin/feature/x", "_addon_repo 6.0"),
            "/ws/addons-source-6.0-fork",
        )

    def test_clean_base_selects_the_shared_worktree(self) -> None:
        self.assertEqual(
            _run("WORKSPACE=/ws; LANE_SFX=; FORK_REF=", "_addon_repo 6.0"),
            "/ws/addons-source-6.0",
        )

    def test_lane_suffix_is_preserved_on_the_fork_worktree(self) -> None:
        self.assertEqual(
            _run("WORKSPACE=/ws; LANE_SFX=-lane2; FORK_REF=origin/x", "_addon_repo 6.1"),
            "/ws/addons-source-6.1-fork-lane2",
        )


class ParseForkRef(unittest.TestCase):
    def _parse(self, brief_body: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(brief_body)
            path = f.name
        self.addCleanup(os.unlink, path)
        return _run("", f"_parse_fork_ref {path}")

    def test_field_present(self) -> None:
        self.assertEqual(
            self._parse("- **Verification base:** origin/feature/ci-cd-pipeline-upstream\n"),
            "origin/feature/ci-cd-pipeline-upstream",
        )

    def test_field_with_backticks(self) -> None:
        self.assertEqual(self._parse("- **Verification base:** `origin/feature/x`\n"), "origin/feature/x")

    def test_field_absent_is_empty(self) -> None:
        self.assertEqual(
            self._parse("- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60\n"),
            "",
        )


if __name__ == "__main__":
    unittest.main()
