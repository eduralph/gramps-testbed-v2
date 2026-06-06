"""Regression guard: run-verify.sh classifies a patch's ADDED vs MODIFIED files.

The C4-verify gate proves a fix red->green by `git apply patch.diff` -> run the
test (green) -> revert the production change -> run again (must be red). The revert
used a blanket `git checkout -- $PROD` over *every* production file. A `git apply`
leaves a brand-NEW file untracked, and `git checkout -- <untracked>` errors
("pathspec did not match") and, under `set -e`, aborts the whole revert before the
gate even reports — so any fix whose tested logic lives in a NEW module could never
pass C4 (testbed issue #5). It also left patch-added files untracked in the
checkout, false-failing the next run on `git apply` "already exists".

The fix splits the production change: a new file (`--- /dev/null` header) is
`rm`-ed, a modified file `git checkout`-ed, and every added file is cleaned from the
checkout after the run. The core of that is the script's `_added_files` /`_in_list`
helpers. This test evaluates *those real helpers* (extracted from the script, like
test_root_resolution evaluates the resolver block) against fixture patches, plus a
structural check that the blanket revert did not creep back.
"""

# ------------------------
# Python modules
# ------------------------
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

# engine/tests/this_file -> parents[2] is the repo root (the dir with pdca.toml).
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "engine/scripts/ubuntu/run-verify.sh"
_PATH = os.environ.get("PATH", "/usr/bin:/bin")

_BEGIN = "# --- patch classification helpers"
_END = "# --- end patch classification helpers ---"


def _helpers_block() -> str:
    """The script's `_added_files` / `_in_list` helper region, verbatim."""
    lines = SCRIPT.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(_BEGIN))
    end = next(i for i, ln in enumerate(lines) if ln.startswith(_END))
    return "\n".join(lines[start : end + 1])


# A core patch that MODIFIES an existing module, ADDS a new module, and ADDS a new
# test. Only the two `--- /dev/null` files are "added".
PATCH_MIXED = textwrap.dedent(
    """\
    diff --git a/gramps/gen/utils/existing.py b/gramps/gen/utils/existing.py
    index 1111111..2222222 100644
    --- a/gramps/gen/utils/existing.py
    +++ b/gramps/gen/utils/existing.py
    @@ -1,3 +1,4 @@
     import os
    +import sys
    \x20
     x = 1
    diff --git a/gramps/plugins/tool/newmod.py b/gramps/plugins/tool/newmod.py
    new file mode 100644
    index 0000000..3333333
    --- /dev/null
    +++ b/gramps/plugins/tool/newmod.py
    @@ -0,0 +1,2 @@
    +def f():
    +    return 42
    diff --git a/gramps/plugins/test/newmod_test.py b/gramps/plugins/test/newmod_test.py
    new file mode 100644
    index 0000000..4444444
    --- /dev/null
    +++ b/gramps/plugins/test/newmod_test.py
    @@ -0,0 +1,3 @@
    +import unittest
    +class T(unittest.TestCase):
    +    def test_x(self): pass
    """
)

# Only modifications -> nothing added.
PATCH_MODIFY_ONLY = textwrap.dedent(
    """\
    diff --git a/a.py b/a.py
    index aaaaaaa..bbbbbbb 100644
    --- a/a.py
    +++ b/a.py
    @@ -1 +1 @@
    -old
    +new
    """
)

# A modified file whose REMOVED content line itself begins with "--- " (original
# source line was "-- foo"). The `+++ b/` of the *next* file is still preceded by
# that file's own `--- a/...` header, so the content line must not misclassify.
PATCH_TRICKY_CONTENT = textwrap.dedent(
    """\
    diff --git a/doc.py b/doc.py
    index aaaaaaa..bbbbbbb 100644
    --- a/doc.py
    +++ b/doc.py
    @@ -1,2 +1,2 @@
     keep
    --- foo
    +-- bar
    diff --git a/new.py b/new.py
    new file mode 100644
    index 0000000..ccccccc
    --- /dev/null
    +++ b/new.py
    @@ -0,0 +1 @@
    +real_new = 1
    """
)


def _run(program: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", program], capture_output=True, text=True)


@unittest.skipUnless(shutil.which("bash"), "bash required to evaluate the helpers")
class VerifyClassificationTest(unittest.TestCase):
    """The real run-verify.sh helpers split added vs modified files correctly."""

    def _added(self, patch_text: str) -> list[str]:
        """Run the script's own `_added_files` over a patch, return the added paths."""
        program = (
            "set -euo pipefail\n"
            + _helpers_block() + "\n"
            'printf "%s" "$PATCH_TEXT" > "$TMP/p.diff"\n'
            '_added_files "$TMP/p.diff"\n'
        )
        res = subprocess.run(
            ["bash", "-c", program],
            capture_output=True, text=True,
            env={"PATCH_TEXT": patch_text, "TMP": self.tmp, "PATH": _PATH},
        )
        self.assertEqual(res.returncode, 0, f"_added_files failed:\n{res.stderr}")
        return res.stdout.split()

    def setUp(self) -> None:
        self._tmpdir = __import__("tempfile").TemporaryDirectory()
        self.tmp = self._tmpdir.name
        self.addCleanup(self._tmpdir.cleanup)

    def test_added_files_picks_only_dev_null_files(self) -> None:
        self.assertEqual(
            self._added(PATCH_MIXED),
            ["gramps/plugins/tool/newmod.py", "gramps/plugins/test/newmod_test.py"],
            "only the two `--- /dev/null` files are added; the modified one is not",
        )

    def test_added_files_empty_for_modify_only_patch(self) -> None:
        self.assertEqual(self._added(PATCH_MODIFY_ONLY), [])

    def test_added_files_ignores_content_line_starting_with_dashes(self) -> None:
        # doc.py is modified (its removed content line is "--- foo"); only new.py is added.
        self.assertEqual(self._added(PATCH_TRICKY_CONTENT), ["new.py"])

    def test_prod_split_rm_new_checkout_modified(self) -> None:
        """The PROD_NEW/PROD_MOD split: of the production files (test excluded), the
        new module is removed and the modified module is checked out."""
        program = (
            "set -euo pipefail\n"
            + _helpers_block() + "\n"
            'printf "%s" "$PATCH_TEXT" > "$TMP/p.diff"\n'
            'mapfile -t ADDED < <(_added_files "$TMP/p.diff")\n'
            # production files = the two non-test files in PATCH_MIXED
            'PROD=(gramps/gen/utils/existing.py gramps/plugins/tool/newmod.py)\n'
            'PROD_MOD=(); PROD_NEW=()\n'
            'for f in "${PROD[@]}"; do\n'
            '  if _in_list "$f" "${ADDED[@]}"; then PROD_NEW+=("$f"); else PROD_MOD+=("$f"); fi\n'
            'done\n'
            'printf "MOD:%s\\n" "${PROD_MOD[*]}"\n'
            'printf "NEW:%s\\n" "${PROD_NEW[*]}"\n'
        )
        res = subprocess.run(
            ["bash", "-c", program],
            capture_output=True, text=True,
            env={"PATCH_TEXT": PATCH_MIXED, "TMP": self.tmp, "PATH": _PATH},
        )
        self.assertEqual(res.returncode, 0, f"split failed:\n{res.stderr}")
        out = dict(ln.split(":", 1) for ln in res.stdout.splitlines())
        self.assertEqual(out["MOD"], "gramps/gen/utils/existing.py")
        self.assertEqual(out["NEW"], "gramps/plugins/tool/newmod.py")

    def test_in_list_handles_empty_candidate_set(self) -> None:
        # An all-modifications patch yields an empty ADDED; membership must not error
        # (set -u) and must report non-member.
        program = (
            "set -euo pipefail\n"
            + _helpers_block() + "\n"
            'ADDED=()\n'
            'if _in_list "x" "${ADDED[@]}"; then echo MEMBER; else echo ABSENT; fi\n'
        )
        res = _run(program)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "ABSENT")


class VerifyScriptStructureTest(unittest.TestCase):
    """The blanket revert that caused issue #5 must not creep back."""

    def test_no_blanket_prod_checkout(self) -> None:
        body = SCRIPT.read_text()
        self.assertNotIn(
            "git checkout -- $PROD\n", body,
            "the unconditional `git checkout -- $PROD` is the issue #5 bug — "
            "the red pass must split PROD into modified (checkout) and new (rm)",
        )

    def test_red_pass_splits_and_cleanup_removes_added(self) -> None:
        body = SCRIPT.read_text()
        self.assertIn("PROD_NEW", body, "red pass must handle newly added prod files (rm)")
        self.assertIn("PROD_MOD", body, "red pass must handle modified prod files (git checkout)")
        self.assertIn(
            'rm -f -- "${ADDED[@]}"', body,
            "post-run restore must remove patch-added files so a re-run does not "
            "false-fail on `git apply` already-exists",
        )


import os  # noqa: E402  (kept low to mirror the std-lib import grouping above)

_PATH = os.environ.get("PATH", "/usr/bin:/bin")


if __name__ == "__main__":
    unittest.main()
