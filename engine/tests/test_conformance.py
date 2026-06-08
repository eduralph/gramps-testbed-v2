"""Unit tests for the T1/T2/T4 conformance checkers (stdlib only, synthetic
fixtures).

Each checker mechanises **MUST** rules from wiki doc 16, the foundation of the
T1–T4 conformance ladder. These tests build tiny conformant / violating fixtures
and assert each rule fires exactly when doc 16 says it should, that it cites the
right guideline by **section** for the contribution target (core vs addon), and
that every cited section still exists in the vendored source (the anchor-drift
guard) — so the gates can be trusted to cite the doc faithfully (issue #6).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CONF = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(CONF))

import doc16  # noqa: E402
import gate  # noqa: E402
import t1_structure  # noqa: E402
import t2_shape  # noqa: E402
import t4_contribution  # noqa: E402

_GPL = "# This program is free software; under the terms of the GNU General Public License\n"


# ---------------------------------------------------------------------------
# T1 — Structure (doc 16 §Structure)
# ---------------------------------------------------------------------------
class T1Structure(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _addon(self, name: str, gpr: str, *, module: str | None = None) -> Path:
        d = self.tmp / name
        d.mkdir()
        (d / f"{name}.gpr.py").write_text(gpr, encoding="utf-8")
        if module:
            (d / module).write_text(_GPL, encoding="utf-8")
        return d

    def _conformant_gpr(self, addon_id: str, module: str) -> str:
        return (
            f'register(TOOL, id="{addon_id}", gramps_target_version="6.0",\n'
            f'         fname="{module}", name=_("X"))\n'
        )

    def test_conformant_addon_passes(self) -> None:
        # folder CalcThing ↔ id "calcthing" — case-insensitive match (doc16:30).
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        (d / "tests").mkdir()
        (d / "tests" / "__init__.py").write_text("", encoding="utf-8")
        must, should = t1_structure.check_addon(str(d))
        self.assertEqual(must, [])
        self.assertEqual(should, [])

    def test_folder_id_mismatch_flagged(self) -> None:  # §Structure
        d = self._addon("CalcThing", self._conformant_gpr("somethingelse", "CalcThing.py"),
                        module="CalcThing.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("doc16-addon §Structure" in m for m in must), must)

    def test_missing_target_version_flagged(self) -> None:  # §Structure
        d = self._addon("CalcThing",
                        'register(TOOL, id="calcthing", fname="CalcThing.py")\n',
                        module="CalcThing.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("doc16-addon §Structure" in m for m in must), must)

    def test_fname_module_absent_flagged(self) -> None:  # §Structure
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"))
        must, _ = t1_structure.check_addon(str(d))  # module file never created
        self.assertTrue(any("doc16-addon §Structure" in m for m in must), must)

    def test_init_py_in_addon_dir_flagged(self) -> None:  # §Structure (Mantis 12691)
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        (d / "__init__.py").write_text("", encoding="utf-8")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("Mantis 12691" in m for m in must), must)

    def test_injected_import_flagged(self) -> None:  # §Structure
        d = self._addon("CalcThing",
                        'import _\n' + self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("Gramps-injected name" in m for m in must), must)

    def test_multi_register_matches_any_id(self) -> None:  # §Structure multi-kind
        gpr = (
            'register(GRAMPLET, id="lxml gramplet", gramps_target_version="6.0",\n'
            '         fname="etree.py")\n'
            'register(VIEW, id="lxml", gramps_target_version="6.0", fname="etree.py")\n'
        )
        d = self._addon("lxml", gpr, module="etree.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertFalse(any("folder name" in m for m in must), must)

    def test_missing_tests_is_advisory_not_must(self) -> None:  # §Structure SHOULD
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        must, should = t1_structure.check_addon(str(d))
        self.assertEqual(must, [])
        self.assertTrue(any("tests/" in s and "SHOULD" in s for s in should), should)


# ---------------------------------------------------------------------------
# T2 — Shape (doc 16 §Coding style)
# ---------------------------------------------------------------------------
class T2Shape(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _py(self, name: str, body: str) -> Path:
        p = self.tmp / name
        p.write_text(body, encoding="utf-8")
        return p

    def test_header_present_no_print_passes(self) -> None:
        p = self._py("ok.py", _GPL + "import logging\nLOG = logging.getLogger(__name__)\n")
        self.assertEqual(t2_shape.check_file(str(p)), ([], []))

    def test_missing_gpl_header_flagged(self) -> None:  # AGENTS.md §File Headers
        p = self._py("nohdr.py", "x = 1\n")
        viol, _ = t2_shape.check_file(str(p))
        self.assertTrue(any("AGENTS.md §File Headers" in v for v in viol), viol)

    def test_print_is_advisory_not_violation(self) -> None:  # AGENTS.md §Logging
        # §Logging bans print() for *diagnostic* output only — the gate cannot tell
        # diagnostic from intentional output, so it surfaces print() as an advisory
        # for the reviewer to adjudicate, never a MUST violation.
        p = self._py("prints.py", _GPL + "print('debug')\n")
        viol, adv = t2_shape.check_file(str(p))
        self.assertEqual(viol, [])
        self.assertTrue(any("AGENTS.md §Logging" in a and "print()" in a for a in adv), adv)

    def test_commented_print_not_flagged(self) -> None:
        p = self._py("comment.py", _GPL + "# print('debug') left as a note\n")
        self.assertEqual(t2_shape.check_file(str(p)), ([], []))

    def test_empty_init_marker_exempt_from_header(self) -> None:
        # A 0-byte / comment-only __init__.py package marker carries no code to
        # license, so the header MUST is exempt (11589 §10 / act-log resolution).
        empty = self._py("__init__.py", "")
        self.assertEqual(t2_shape.check_file(str(empty)), ([], []))
        comment_only = self.tmp / "pkg"
        comment_only.mkdir()
        marker = comment_only / "__init__.py"
        marker.write_text("# tests package\n", encoding="utf-8")
        self.assertEqual(t2_shape.check_file(str(marker)), ([], []))

    def test_init_with_code_still_needs_header(self) -> None:
        # An __init__.py that actually contains code is NOT a bare marker — header applies.
        p = self._py("__init__.py", "import os\nx = os.getcwd()\n")
        viol, _ = t2_shape.check_file(str(p))
        self.assertTrue(any("AGENTS.md §File Headers" in v for v in viol), viol)


# ---------------------------------------------------------------------------
# T2 dispatch — touched-file scope (gate.py)
# ---------------------------------------------------------------------------
class T2TouchedScope(unittest.TestCase):
    """T2 audits only the .py files the patch touches (added or modified), never a
    pre-existing untouched file — the §File Headers MUST is "every *new* .py file"
    and pdca.toml mandates no gating on legacy state the patch did not introduce."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addons = self.tmp / "addons-source"
        addon = self.addons / "MyAddon"
        addon.mkdir(parents=True)
        for f in ("added.py", "modified.py", "untouched.py"):
            (addon / f).write_text("x = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_only_touched_files_in_scope(self) -> None:
        patch = self.tmp / "patch.diff"
        patch.write_text(
            "diff --git a/MyAddon/added.py b/MyAddon/added.py\n"
            "new file mode 100644\n--- /dev/null\n+++ b/MyAddon/added.py\n"
            "@@ -0,0 +1 @@\n+x = 1\n"
            "diff --git a/MyAddon/modified.py b/MyAddon/modified.py\n"
            "--- a/MyAddon/modified.py\n+++ b/MyAddon/modified.py\n"
            "@@ -1 +1 @@\n-x = 1\n+x = 2\n",
            encoding="utf-8",
        )
        names = {f.name for f in gate._touched_addon_files(patch, self.addons)}
        self.assertEqual(names, {"added.py", "modified.py"})
        self.assertNotIn("untouched.py", names)


# ---------------------------------------------------------------------------
# T4 — Contribution (doc 16 §Commit messages / §Mantis trailers / PR body)
# ---------------------------------------------------------------------------
class T4Contribution(unittest.TestCase):
    GOOD = (
        "Fix toolbar update crash during shutdown\n"
        "\n"
        "When the main window is torn down a queued update_menu() could run\n"
        "against a detached toolbar and raise AttributeError.\n"
        "\n"
        "Fixes #13636\n"
    )

    def test_conformant_commit_passes(self) -> None:
        self.assertEqual(t4_contribution.check_commit_msg(self.GOOD), [])

    def test_summary_too_long_flagged(self) -> None:  # §Commit messages
        msg = "x" * 71 + "\n\nbody\n\nFixes #1\n"
        self.assertTrue(any("§Commit messages" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_no_blank_after_summary_flagged(self) -> None:  # §Commit messages
        msg = "Short summary\nbody right away\n\nFixes #1\n"
        self.assertTrue(any("§Commit messages" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_missing_trailer_flagged(self) -> None:  # §Mantis trailer keywords
        msg = "Short summary\n\nbody text here\n"
        self.assertTrue(any("§Mantis trailer keywords" in v
                            for v in t4_contribution.check_commit_msg(msg)))

    def test_bare_number_trailer_flagged(self) -> None:  # §Mantis trailer keywords
        msg = "Short summary\n\nbody text\n\nFixes 13636\n"
        self.assertTrue(any("§Mantis trailer keywords" in v
                            for v in t4_contribution.check_commit_msg(msg)))

    def test_short_hash_flagged(self) -> None:  # §Commit messages
        msg = "Short summary\n\nfollow-up to [abc1234] earlier work\n\nFixes #1\n"
        self.assertTrue(any("§Commit messages" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_link_keyword_accepted(self) -> None:  # link form
        msg = "Short summary\n\nbody text\n\nBug #13636\n"
        self.assertEqual(t4_contribution.check_commit_msg(msg), [])

    def test_commit_cites_the_target_guideline(self) -> None:
        # The same defect cites the core page for a core fix and the addon page for
        # an addon fix — never the wrong guideline (issue #6).
        bad = "x" * 71 + "\n\nbody\n\nFixes #1\n"
        self.assertTrue(any("doc16-core" in v for v in
                            t4_contribution.check_commit_msg(bad, "core")))
        self.assertTrue(any("doc16-addon" in v for v in
                            t4_contribution.check_commit_msg(bad, "addon")))

    def test_pr_body_four_sections_core_only(self) -> None:  # issue #6
        prose = "just some prose, no structure, mentions #13636"
        # core: the four-section structure is a MUST → flagged.
        core_viol = t4_contribution.check_pr_body(prose, "core")
        self.assertTrue(any("Root cause" in v and "§Contributor workflow" in v
                            for v in core_viol), core_viol)
        # addon: NOT a rule — an addon PR body need only reference the bug, which
        # this one does, so it is clean (never failed against the core-only rule).
        self.assertEqual(t4_contribution.check_pr_body(prose, "addon"), [])

    def test_pr_body_addon_requires_bug_reference(self) -> None:
        viol = t4_contribution.check_pr_body("no structure, no bug id", "addon")
        self.assertTrue(any("bug reference" in v and "doc16-addon" in v
                            for v in viol), viol)

    def test_pr_body_conformant(self) -> None:
        body = ("## Root cause\nx\n## Fix\ny\n## Verified against\nz\n## Test\nt\n"
                "References #13636\n")
        self.assertEqual(t4_contribution.check_pr_body(body, "core"), [])

    def test_publisher_stub_artifacts_pass_t4(self) -> None:
        # The Check-closing publisher leaf's offline stub must write doc-16/T4-valid
        # commit-msg.txt + pr-description.md — the publish slice relies on it.
        import shutil
        import sys
        import tempfile
        src = Path(__file__).resolve().parents[2] / "src"
        sys.path.insert(0, str(src))
        from pdca_harness import leaves  # noqa: E402
        from pdca_harness.config import Config, LeafConfig  # noqa: E402
        tmp = Path(tempfile.mkdtemp())
        try:
            d = tmp / "issue_13636"
            d.mkdir()
            cfg = Config(
                root=tmp, bundle_root=tmp, process_dir=tmp, templates_dir=tmp,
                default_branch="main", tracker_system="", tracker_url="",
                issue_id_example="", builder=LeafConfig(), reviewer=LeafConfig(),
                publisher=LeafConfig(mode="stub"),
            )
            leaves._stub_publish(d, cfg)
            self.assertEqual(
                t4_contribution.check_commit_msg((d / "commit-msg.txt").read_text()), [])
            self.assertEqual(
                t4_contribution.check_pr_body((d / "pr-description.md").read_text()), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# doc16 anchors — every cited section must exist in its vendored source
# ---------------------------------------------------------------------------
class Doc16Anchors(unittest.TestCase):
    """The anchor-drift guard (issue #6): citing by section heading is only safe
    if the section still exists. Every (source, section) the checkers cite is
    asserted present in the vendored page — so an edit that renames/removes a
    cited heading fails here instead of producing a dangling citation. A source
    whose page file isn't present (e.g. the sibling ``AGENTS.md`` in a checkout
    without it) is skipped, not failed."""

    # The complete set of anchors the T1/T2/T4 checkers cite.
    CITED = [
        ("addon", "Structure"),
        ("agents", "File Headers"),
        ("agents", "Logging"),
        ("core", "Commit messages"),
        ("addon", "Commit messages"),
        ("core", "Mantis trailer keywords"),
        ("addon", "Mantis trailer keywords"),
        ("core", "Contributor workflow"),
        ("addon", "addons-source: bug reference in PR body"),
    ]

    def test_every_cited_section_exists(self) -> None:
        for source, section in self.CITED:
            with self.subTest(source=source, section=section):
                present = doc16.sections_present(source)
                if not present:
                    self.skipTest(f"vendored source {source!r} not present "
                                  f"({doc16.PAGES[source]})")
                self.assertIn(
                    section, present,
                    f"cited section §{section} not found in {source} "
                    f"({doc16.PAGES[source]}) — heading renamed/removed? "
                    f"update the citation or the page",
                )


if __name__ == "__main__":
    unittest.main()
