"""Regression guard: dropping a manifest row takes its essential worktree with it.

`make essential-worktrees` derives the versions it (re)builds from
`engine/essential-fixes.tsv`. Dropping a row therefore does not rebuild that
version — it stops visiting it, even under `REBUILD=1`. The worktree an earlier
run created survives as a stale verification base: upstream + a fix that is no
longer essential, on a commit nothing refreshes (testbed PR #327, Codex review).

`prune-essential-worktrees.sh` closes that: it removes every
`gramps-<ver>-essential*` worktree — main line and lane copies — whose version the
manifest no longer declares, and deletes the matching `testbed/essential-gramps<tag>`
branch. These cases drive the real script against a real git repo with real
worktrees, since `git worktree remove` and the branch cleanup are the parts that
can silently no-op.
"""

# ------------------------
# Python modules
# ------------------------
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

# engine/tests/this_file -> parents[2] is the repo root (the dir with pdca.toml).
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "engine/scripts/lib/prune-essential-worktrees.sh"

_ROW_61 = "6.1\tf4f94f34db\theadless-ut-segfault\tlazy LinkTag colour"
_ROW_60 = "6.0\tdeadbeef12\tsome-other-fix\tanother essential fix"
_HEADER = "# Essential fixes.\n# Columns: version <TAB> commit <TAB> slug <TAB> desc\n"


def _git(*args: str, cwd: Path) -> str:
    """Run git, raising with stderr attached on failure."""
    out = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "HOME": str(cwd)},
    )
    return out.stdout.strip()


class PruneEssentialWorktreesTest(unittest.TestCase):
    """The manifest decides which essential worktrees may exist."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ws = Path(self._tmp.name)
        self.manifest = self.ws / "essential-fixes.tsv"

        # A real repo at <ws>/gramps — the script drives `git -C "$ws/gramps"`.
        self.gramps = self.ws / "gramps"
        self.gramps.mkdir()
        _git("init", "-q", "-b", "main", cwd=self.gramps)
        _git("config", "user.email", "t@t.invalid", cwd=self.gramps)
        _git("config", "user.name", "T", cwd=self.gramps)
        (self.gramps / "f.txt").write_text("x\n")
        _git("add", "f.txt", cwd=self.gramps)
        _git("commit", "-qm", "init", cwd=self.gramps)

    def _write_manifest(self, *rows: str) -> None:
        self.manifest.write_text(_HEADER + "".join(r + "\n" for r in rows))

    def _add_essential(self, name: str, branch: str) -> Path:
        """Create <ws>/<name> as a real worktree on <branch>."""
        wt = self.ws / name
        _git("branch", "-f", branch, "main", cwd=self.gramps)
        _git("worktree", "add", "--quiet", str(wt), branch, cwd=self.gramps)
        return wt

    def _branches(self) -> list[str]:
        out = _git("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=self.gramps)
        return out.split()

    def _prune(self) -> str:
        out = subprocess.run(
            ["bash", str(SCRIPT), str(self.ws), str(self.manifest)],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout

    def test_worktree_for_dropped_row_is_removed(self) -> None:
        """The P1: every row dropped, the 6.1 worktree must not survive."""
        wt = self._add_essential("gramps-6.1-essential", "testbed/essential-gramps61")
        self._write_manifest()  # every row dropped
        out = self._prune()
        self.assertFalse(wt.exists(), "stale essential worktree left on disk")
        self.assertNotIn("testbed/essential-gramps61", self._branches())
        self.assertIn("pruning stale essential worktree", out)

    def test_declared_version_is_kept(self) -> None:
        """A live row keeps its worktree — pruning must not eat the working line."""
        wt = self._add_essential("gramps-6.1-essential", "testbed/essential-gramps61")
        self._write_manifest(_ROW_61)
        out = self._prune()
        self.assertTrue(wt.exists(), "pruned a worktree the manifest still declares")
        self.assertIn("testbed/essential-gramps61", self._branches())
        self.assertEqual(out.strip(), "")

    def test_lane_copies_are_pruned_too(self) -> None:
        """Lane worktrees share the line; a dropped row strands each of them."""
        main = self._add_essential("gramps-6.1-essential", "testbed/essential-gramps61")
        lane0 = self._add_essential(
            "gramps-6.1-essential-lane0", "testbed/essential-gramps61-lane0"
        )
        lane1 = self._add_essential(
            "gramps-6.1-essential-lane1", "testbed/essential-gramps61-lane1"
        )
        self._write_manifest()
        self._prune()
        for wt in (main, lane0, lane1):
            self.assertFalse(wt.exists(), f"{wt.name} survived the prune")
        for br in (
            "testbed/essential-gramps61",
            "testbed/essential-gramps61-lane0",
            "testbed/essential-gramps61-lane1",
        ):
            self.assertNotIn(br, self._branches())

    def test_only_the_dropped_version_is_pruned(self) -> None:
        """6.0 stays declared, 6.1 is dropped: prune must not be all-or-nothing."""
        keep = self._add_essential("gramps-6.0-essential", "testbed/essential-gramps60")
        drop = self._add_essential("gramps-6.1-essential", "testbed/essential-gramps61")
        self._write_manifest(_ROW_60)
        self._prune()
        self.assertTrue(keep.exists(), "pruned the still-declared 6.0 line")
        self.assertFalse(drop.exists(), "kept the dropped 6.1 line")
        self.assertIn("testbed/essential-gramps60", self._branches())
        self.assertNotIn("testbed/essential-gramps61", self._branches())

    def test_commented_row_does_not_keep_a_worktree(self) -> None:
        """A commented-out fix is dropped; the manifest parser must agree."""
        wt = self._add_essential("gramps-6.1-essential", "testbed/essential-gramps61")
        self._write_manifest("#" + _ROW_61)
        self._prune()
        self.assertFalse(wt.exists())

    def test_empty_workspace_is_a_noop(self) -> None:
        """No essential worktrees at all: the glob must not error under `set -e`."""
        self._write_manifest(_ROW_61)
        self.assertEqual(self._prune().strip(), "")

    def test_is_idempotent(self) -> None:
        """Running twice is safe — preflight calls this on every invocation."""
        self._add_essential("gramps-6.1-essential", "testbed/essential-gramps61")
        self._write_manifest()
        self._prune()
        self.assertEqual(self._prune().strip(), "")


if __name__ == "__main__":
    unittest.main()
