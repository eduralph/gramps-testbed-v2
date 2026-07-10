"""Regression guard: the essential-line retry requires a live manifest row.

When a C4-verify leg fails on clean upstream, run-verify.sh retries the bundle on
the "essential" line (upstream + the harness-enabling fixes in
`engine/essential-fixes.tsv`) and, on a pass, stamps `essential-dependency.json`
instead of failing the gate.

The retry used to be gated on directory presence alone (`[ -d "$ess" ]`). Dropping
a row from the manifest does not remove the worktree an earlier `make
essential-worktrees` created — `Makefile`'s loop derives its versions *from the
manifest*, so a dropped version is simply never visited again, not even under
`REBUILD=1`. On every machine that had built it, `../gramps-<ver>-essential` lived
on as a stale line carrying a fix that is no longer essential, on a base no longer
refreshed. run-verify would still retry there, and a pass would stamp
`"depends_on": []` — a green gate naming no prerequisite, masking an upstream
failure (testbed PR #327, Codex review).

The manifest is the source of truth: a directory is not evidence. These cases
evaluate the script's *real* `_essential_slugs` / `_essential_retry_ok` helpers
(extracted from the script, as test_verify_classification does) against fixture
manifests, plus a structural check that the bare `[ -d "$ess" ]` gate does not
creep back.
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
SCRIPT = REPO_ROOT / "engine/scripts/ubuntu/run-verify.sh"
_PATH = os.environ.get("PATH", "/usr/bin:/bin")

_BEGIN = "# --- essential-line eligibility"
_END = "# --- end essential-line eligibility ---"

# A manifest is TAB-separated: version <TAB> commit <TAB> slug <TAB> description.
_ROW_61 = "6.1\tf4f94f34db\theadless-ut-segfault\tlazy LinkTag colour"
_ROW_60 = "6.0\tdeadbeef12\tsome-other-fix\tanother essential fix"
_COMMENTS = textwrap.dedent(
    """\
    # Essential fixes — the harness-enabling PRODUCTION fixes.
    #
    # Columns (TAB-separated): target_version <TAB> source_commit <TAB> slug
    """
)


def _helpers_block() -> str:
    """The script's essential-line eligibility helpers, verbatim."""
    lines = SCRIPT.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(_BEGIN))
    end = next(i for i, ln in enumerate(lines) if ln.startswith(_END))
    return "\n".join(lines[start : end + 1])


class EssentialRetryGateTest(unittest.TestCase):
    """`_essential_retry_ok` must require BOTH the worktree and a manifest row."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.engine = self.tmp / "engine"
        self.engine.mkdir()
        self.addCleanup(self._tmp.cleanup)

    def _write_manifest(self, *rows: str) -> None:
        body = _COMMENTS + "".join(row + "\n" for row in rows)
        (self.engine / "essential-fixes.tsv").write_text(body)

    def _retry_ok(self, leg: str, ess: Path) -> bool:
        """Run the real helpers under bash; return `_essential_retry_ok`'s verdict."""
        script = "\n".join(
            [
                "set -euo pipefail",
                f'ENGINE="{self.engine}"',
                _helpers_block(),
                f'if _essential_retry_ok "{leg}" "{ess}"; then echo YES; else echo NO; fi',
            ]
        )
        out = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            env={"PATH": _PATH},
            check=True,
        )
        return out.stdout.strip() == "YES"

    def _slugs(self, leg: str) -> list[str]:
        script = "\n".join(
            [
                "set -euo pipefail",
                f'ENGINE="{self.engine}"',
                _helpers_block(),
                f'_essential_slugs "{leg}"',
            ]
        )
        out = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            env={"PATH": _PATH},
            check=True,
        )
        return out.stdout.split()

    def test_row_and_worktree_present_is_eligible(self) -> None:
        """The intended case: manifest declares the fix and the line was built."""
        self._write_manifest(_ROW_61)
        ess = self.tmp / "gramps-6.1-essential"
        ess.mkdir()
        self.assertTrue(self._retry_ok("6.1", ess))

    def test_stale_worktree_without_row_is_not_eligible(self) -> None:
        """The P1: row dropped, worktree survives. Must NOT retry there.

        Red before the fix, where the gate was `[ -d "$ess" ]` alone.
        """
        self._write_manifest(_ROW_60)  # a 6.0 row, nothing for 6.1
        ess = self.tmp / "gramps-6.1-essential"
        ess.mkdir()
        self.assertFalse(self._retry_ok("6.1", ess))

    def test_empty_manifest_with_worktree_is_not_eligible(self) -> None:
        """Every row dropped — exactly the state PR #327 leaves the manifest in."""
        self._write_manifest()
        ess = self.tmp / "gramps-6.1-essential"
        ess.mkdir()
        self.assertFalse(self._retry_ok("6.1", ess))

    def test_row_without_worktree_is_not_eligible(self) -> None:
        """Declared but never built: nothing to retry on."""
        self._write_manifest(_ROW_61)
        self.assertFalse(self._retry_ok("6.1", self.tmp / "gramps-6.1-essential"))

    def test_lane_worktree_is_gated_by_the_same_row(self) -> None:
        """A lane copy is the same line; the manifest still decides."""
        self._write_manifest(_ROW_61)
        lane = self.tmp / "gramps-6.1-essential-lane0"
        lane.mkdir()
        self.assertTrue(self._retry_ok("6.1", lane))
        self._write_manifest()
        self.assertFalse(self._retry_ok("6.1", lane))

    def test_comment_row_is_not_a_declaration(self) -> None:
        """A commented-out fix is dropped, not declared."""
        self._write_manifest("#" + _ROW_61)
        ess = self.tmp / "gramps-6.1-essential"
        ess.mkdir()
        self.assertFalse(self._retry_ok("6.1", ess))

    def test_slugs_are_read_per_version(self) -> None:
        """`depends_on` is built from these; a leg must not inherit another's fix."""
        self._write_manifest(_ROW_60, _ROW_61)
        self.assertEqual(self._slugs("6.1"), ["headless-ut-segfault"])
        self.assertEqual(self._slugs("6.0"), ["some-other-fix"])
        self.assertEqual(self._slugs("5.2"), [])


class NoBareDirectoryGateTest(unittest.TestCase):
    """Structural: the directory-only retry gate must not creep back."""

    def test_retry_is_not_gated_on_directory_presence_alone(self) -> None:
        # Line-anchored: the trailing `elif [ "$MODE" = core ] && [ -d "$ess" ]`
        # that reports the stale worktree legitimately contains this text.
        stale_gate = 'if [ "$MODE" = core ] && [ -d "$ess" ]; then'
        offenders = [
            ln
            for ln in SCRIPT.read_text().splitlines()
            if ln.strip() == stale_gate
        ]
        self.assertEqual(
            offenders,
            [],
            "the essential retry must consult the manifest, not just the worktree",
        )
        self.assertIn('_essential_retry_ok "$leg" "$ess"', SCRIPT.read_text())

    def test_stamp_refuses_an_empty_depends_on(self) -> None:
        body = SCRIPT.read_text()
        self.assertIn("refusing to stamp", body)


if __name__ == "__main__":
    unittest.main()
