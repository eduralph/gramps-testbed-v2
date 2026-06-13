"""Unit tests for addon_authors.py — credit metadata read from an addon's .gpr.py.

Issue #53: a PR that modifies a third-party addon credits the original author(s)
and @-mentions (calls out) the current maintainer so they are aware. This guards the extraction: maintainers
when declared, else authors; emails paired; the `authors` pattern not confused by
`authors_email`. Synthetic .gpr.py fixtures (no addons-source checkout needed).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB))

import addon_authors  # noqa: E402


class AddonAuthors(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _addon(self, name: str, gpr_body: str) -> Path:
        d = self.tmp / name
        d.mkdir()
        (d / f"{name}.gpr.py").write_text(gpr_body, encoding="utf-8")
        return d

    # --- addon_credits: reads all four fields, authors != authors_email -----
    def test_reads_all_fields_without_prefix_confusion(self) -> None:
        d = self._addon(
            "Demo",
            'authors=["Greg Lamberson"]\nauthors_email=["lamberson@yahoo.com"]\n'
            'maintainers=["Nick Hall"]\nmaintainers_email=["nick@example.org"]\n',
        )
        c = addon_authors.addon_credits(str(d))
        self.assertEqual(c["authors"], ["Greg Lamberson"])
        self.assertEqual(c["authors_email"], ["lamberson@yahoo.com"])
        self.assertEqual(c["maintainers"], ["Nick Hall"])
        self.assertEqual(c["maintainers_email"], ["nick@example.org"])

    # --- mention_targets: maintainers when present ----------------------------
    def test_mentions_maintainer_when_declared(self) -> None:
        d = self._addon(
            "TMGimporter",
            'authors=["Sam Manzi"]\nauthors_email=[""]\n'
            'maintainers=["Sam Manzi"]\nmaintainers_email=[""]\n',
        )
        role, people = addon_authors.mention_targets(str(d))
        self.assertEqual(role, "maintainer")
        self.assertEqual(people, [("Sam Manzi", "")])

    # --- mention_targets: falls back to authors when no maintainer ------------
    def test_falls_back_to_authors_when_no_maintainer(self) -> None:
        d = self._addon(
            "MediaReport",
            'authors=["Matthias Kemmer"]\n'
            'authors_email=["matt.familienforschung@gmail.com"]\n',
        )
        role, people = addon_authors.mention_targets(str(d))
        self.assertEqual(role, "author")
        self.assertEqual(people, [("Matthias Kemmer", "matt.familienforschung@gmail.com")])

    def test_multiple_people_zipped_with_emails(self) -> None:
        d = self._addon(
            "Betawhatsnext",
            'authors=["Reinhard Mueller"]\nauthors_email=[""]\n'
            'maintainers=["Jakim Friant", "Brian McCullough"]\n'
            'maintainers_email=["jmodule@friant.org", "emyoulation@yahoo.com"]\n',
        )
        role, people = addon_authors.mention_targets(str(d))
        self.assertEqual(role, "maintainer")
        self.assertEqual(
            people,
            [("Jakim Friant", "jmodule@friant.org"),
             ("Brian McCullough", "emyoulation@yahoo.com")],
        )

    def test_no_credit_fields_is_empty(self) -> None:
        d = self._addon("Bare", "register(GRAMPLET, id='x')\n")
        role, people = addon_authors.mention_targets(str(d))
        self.assertEqual(role, "author")
        self.assertEqual(people, [])

    def test_drops_empty_email_placeholders(self) -> None:
        # authors_email=[""] is the common "no email" placeholder — dropped.
        d = self._addon("NoEmail", 'authors=["Serge Noiraud"]\nauthors_email=[""]\n')
        self.assertEqual(addon_authors.addon_credits(str(d))["authors_email"], [])


if __name__ == "__main__":
    unittest.main()
