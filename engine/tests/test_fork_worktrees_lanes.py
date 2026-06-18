"""Regression guard: fork verification-base worktrees are lane-aware (issue #137).

A fork-based addon bundle (brief declares `Verification base: <remote>/<branch>`, #96)
runs its C4 gate against `addons-source-<ver>-fork$LANE_SFX`. Under the worker pool / a
separate-terminal lane that path is `…-fork-lane$K`, so `make fork-worktrees` must build
the per-lane copies — and the runner's missing-worktree message must name `make
fork-worktrees` for a `-fork-lane*` path, not the generic worktrees target. Both checks
are Docker-free.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = REPO_ROOT / "Makefile"
RUN_VERIFY = REPO_ROOT / "engine/scripts/ubuntu/run-verify.sh"


def _recipe(target: str) -> str:
    """The recipe lines (tab-indented) of a Makefile target."""
    lines = MAKEFILE.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(f"{target}:"))
    body: list[str] = []
    for ln in lines[start + 1:]:
        if ln.startswith("\t"):
            body.append(ln)
        elif ln.strip() == "":
            continue  # blank line inside a recipe block (rare) — keep scanning
        else:
            break
    return "\n".join(body)


class ForkWorktreesLaneAware(unittest.TestCase):
    """`make fork-worktrees LANES=N` builds the `-lane*` copies, like the other targets."""

    def test_fork_worktrees_has_the_lanes_loop(self) -> None:
        recipe = _recipe("fork-worktrees")
        self.assertIn("$(LANES)", recipe, "fork-worktrees ignores LANES")
        self.assertIn("-lane$$k", recipe, "fork-worktrees builds no per-lane sfxs")
        self.assertIn("-fork$$sfx", recipe, "fork-worktrees path is not lane-suffixed")

    def test_mirrors_the_other_worktree_targets(self) -> None:
        # The pattern fork-worktrees now follows is the one worktrees/essential-worktrees
        # already use; if those lose it this assumption is wrong.
        for target in ("worktrees", "essential-worktrees"):
            self.assertIn("-lane$$k", _recipe(target), f"{target} lost its LANES loop")

    def test_dry_run_emits_lane_paths(self) -> None:
        # `make -n` expands the recipe without touching git: lane0/lane1 fork paths appear.
        out = subprocess.run(
            ["make", "-n", "fork-worktrees", "LANES=2"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("-lane$k", out.stdout, "dry-run shows no lane suffix expansion")


class RunVerifyForkGlob(unittest.TestCase):
    """The missing-worktree case routes a `-fork-lane*` path to `make fork-worktrees`."""

    def _fork_case_pattern(self) -> str:
        # Extract the real case-arm glob from run-verify.sh (everything before its `)`),
        # so this test exercises the shipped pattern, not a hand-copied one.
        for ln in RUN_VERIFY.read_text().splitlines():
            if "fork worktree" in ln and "missing" in ln:
                return ln.split(")", 1)[0].strip()
        raise AssertionError("fork missing-worktree case arm not found in run-verify.sh")

    def _routes_to(self, path: str) -> str:
        pat = self._fork_case_pattern()
        # Inline the pattern into the case source so `|` stays alternation (a `|` arriving
        # via a variable would be a literal, not an alternation separator).
        prog = f'case "{path}" in\n  {pat}) echo FORK;;\n  *) echo OTHER;;\nesac\n'
        r = subprocess.run(["bash", "-c", prog], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def test_lane_fork_path_routes_to_fork_message(self) -> None:
        self.assertEqual(self._routes_to("addons-source-6.0-fork-lane0"), "FORK")

    def test_bare_fork_path_still_routes_to_fork_message(self) -> None:
        self.assertEqual(self._routes_to("addons-source-6.0-fork"), "FORK")

    def test_non_fork_lane_path_routes_to_generic(self) -> None:
        # A plain (non-fork) addon lane worktree must NOT hit the fork arm.
        self.assertEqual(self._routes_to("addons-source-6.0-lane0"), "OTHER")


if __name__ == "__main__":
    unittest.main()
