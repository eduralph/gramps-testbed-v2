"""Unit tests for the T1/T2/T4 conformance checkers (stdlib only, synthetic
fixtures).

Each checker mechanises **MUST** rules from wiki doc 16 ("Addon Development —
Rules"), the foundation of the T1–T4 conformance ladder. These tests build tiny
conformant / violating fixtures and assert each rule fires exactly when doc 16
says it should — so the gates can be trusted to cite the doc faithfully.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CONF = Path(__file__).resolve().parents[1] / "conformance"
sys.path.insert(0, str(CONF))

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

    def test_folder_id_mismatch_flagged(self) -> None:  # doc16:30
        d = self._addon("CalcThing", self._conformant_gpr("somethingelse", "CalcThing.py"),
                        module="CalcThing.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("doc16:30" in m for m in must), must)

    def test_missing_target_version_flagged(self) -> None:  # doc16:31
        d = self._addon("CalcThing",
                        'register(TOOL, id="calcthing", fname="CalcThing.py")\n',
                        module="CalcThing.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("doc16:31" in m for m in must), must)

    def test_fname_module_absent_flagged(self) -> None:  # doc16:32
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"))
        must, _ = t1_structure.check_addon(str(d))  # module file never created
        self.assertTrue(any("doc16:32" in m for m in must), must)

    def test_init_py_in_addon_dir_flagged(self) -> None:  # doc16:35
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        (d / "__init__.py").write_text("", encoding="utf-8")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("doc16:35" in m for m in must), must)

    def test_injected_import_flagged(self) -> None:  # doc16:34
        d = self._addon("CalcThing",
                        'import _\n' + self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertTrue(any("doc16:34" in m for m in must), must)

    def test_multi_register_matches_any_id(self) -> None:  # doc16:30 multi-kind
        gpr = (
            'register(GRAMPLET, id="lxml gramplet", gramps_target_version="6.0",\n'
            '         fname="etree.py")\n'
            'register(VIEW, id="lxml", gramps_target_version="6.0", fname="etree.py")\n'
        )
        d = self._addon("lxml", gpr, module="etree.py")
        must, _ = t1_structure.check_addon(str(d))
        self.assertFalse(any("doc16:30" in m for m in must), must)

    def test_missing_tests_is_advisory_not_must(self) -> None:  # doc16:38 SHOULD
        d = self._addon("CalcThing", self._conformant_gpr("calcthing", "CalcThing.py"),
                        module="CalcThing.py")
        must, should = t1_structure.check_addon(str(d))
        self.assertEqual(must, [])
        self.assertTrue(any("doc16:38" in s for s in should), should)


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
        self.assertEqual(t2_shape.check_file(str(p)), [])

    def test_missing_gpl_header_flagged(self) -> None:  # doc16:99
        p = self._py("nohdr.py", "x = 1\n")
        self.assertTrue(any("doc16:99" in v for v in t2_shape.check_file(str(p))))

    def test_print_flagged(self) -> None:  # doc16:71
        p = self._py("prints.py", _GPL + "print('debug')\n")
        viol = t2_shape.check_file(str(p))
        self.assertTrue(any("doc16:71" in v for v in viol), viol)

    def test_commented_print_not_flagged(self) -> None:
        p = self._py("comment.py", _GPL + "# print('debug') left as a note\n")
        self.assertEqual(t2_shape.check_file(str(p)), [])


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

    def test_summary_too_long_flagged(self) -> None:  # doc16:137
        msg = "x" * 71 + "\n\nbody\n\nFixes #1\n"
        self.assertTrue(any("doc16:137" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_no_blank_after_summary_flagged(self) -> None:  # doc16:138
        msg = "Short summary\nbody right away\n\nFixes #1\n"
        self.assertTrue(any("doc16:138" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_missing_trailer_flagged(self) -> None:  # doc16:142,144
        msg = "Short summary\n\nbody text here\n"
        self.assertTrue(any("doc16:142" in v or "doc16:144" in v
                            for v in t4_contribution.check_commit_msg(msg)))

    def test_bare_number_trailer_flagged(self) -> None:  # doc16:165
        msg = "Short summary\n\nbody text\n\nFixes 13636\n"
        self.assertTrue(any("doc16:165" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_short_hash_flagged(self) -> None:  # doc16:141
        msg = "Short summary\n\nfollow-up to [abc1234] earlier work\n\nFixes #1\n"
        self.assertTrue(any("doc16:141" in v for v in t4_contribution.check_commit_msg(msg)))

    def test_link_keyword_accepted(self) -> None:  # doc16:156 link form
        msg = "Short summary\n\nbody text\n\nBug #13636\n"
        self.assertEqual(t4_contribution.check_commit_msg(msg), [])

    def test_pr_body_sections_required(self) -> None:  # doc16:118
        viol = t4_contribution.check_pr_body("just some prose, no structure")
        self.assertTrue(any("doc16:118" in v for v in viol), viol)

    def test_pr_body_conformant(self) -> None:
        body = ("## Root cause\nx\n## Fix\ny\n## Verified against\nz\n## Test\nt\n"
                "References #13636\n")
        self.assertEqual(t4_contribution.check_pr_body(body), [])

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


if __name__ == "__main__":
    unittest.main()
