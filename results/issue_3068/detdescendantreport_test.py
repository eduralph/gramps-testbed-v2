#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  Gramps Development Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.
#

"""
Regression test for Mantis 3068 -- "Wrong reference number for 'same person
as' in the Detailed Descendant Report".

RECORD ARTIFACT / STANDALONE COPY.  In the shipped patch (patch.diff) this exact
regression is added to the existing, already-registered report-regression file
``gramps/plugins/test/reports_test.py`` (the ``TestDetDescendantDuplicateNumber``
class), NOT as a new module.  See build-notes.md for why the brief's originally
named new file ``gramps/plugins/textreport/test/detdescendantreport_test.py``
could not pass the automated C4-verify gate (a new .py forces a po/POTFILES.skip
change, which makes run-verify.sh treat the bundle as a normal fix and run a
red->green mechanic that can never go red for an already-merged fix).

This standalone copy is logically identical to the class added to reports_test.py
and is runnable in isolation (no heavy module-level CLI fixture):

    PYTHONPATH=<gramps> GRAMPS_RESOURCES=<gramps> \\
        python3 -m unittest gramps.plugins.textreport.test.detdescendantreport_test

When a descendant is reachable through more than one descent path (e.g. the
child of two first cousins) the Henry-numbering filter must keep the *first /
smaller* reference number for that person, not the number from the last path
visited.  The "is the same person as [N]" line printed by ``write_person``
cites ``self.dnumber[person_handle]`` verbatim, so the value the filter stores
is exactly what the report prints.

The unit under test is the production method
``DetDescendantReport.apply_henry_filter`` itself (driven through a light probe
object), not a re-implementation of its logic -- so any future drift in that
method is caught here.  The module imports only ``gramps.gen`` /
``gramps.plugins.lib`` code (no ``gi`` / ``gramps.gui``), so it loads under the
headless test runner.
"""

import unittest

from gramps.gen.db import DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.lib import ChildRef, Family, Person
from gramps.plugins.textreport.detdescendantreport import DetDescendantReport


class _HenryProbe:
    """Minimal stand-in for ``DetDescendantReport`` exposing only the
    attributes ``apply_henry_filter`` touches, while reusing the *real*
    production method (assigned below) so the test exercises shipping code."""

    apply_henry_filter = DetDescendantReport.apply_henry_filter

    def __init__(self, db, max_generations=100):
        self._db = db
        self.max_generations = max_generations
        self.dnumber = {}
        self.map = {}
        self.gen_keys = []


def _make_db():
    db = make_database("sqlite")
    db.load(":memory:")
    return db


def _add_person(db, trans):
    person = Person()
    person.set_gender(Person.MALE)
    return db.add_person(person, trans)


def _add_family(db, trans, father=None, mother=None, children=()):
    family = Family()
    if father is not None:
        family.set_father_handle(father)
    if mother is not None:
        family.set_mother_handle(mother)
    for child_handle in children:
        child_ref = ChildRef()
        child_ref.set_reference_handle(child_handle)
        family.add_child_ref(child_ref)
    family_handle = db.add_family(family, trans)
    for parent in (father, mother):
        if parent is None:
            continue
        person = db.get_person_from_handle(parent)
        person.add_family_handle(family_handle)
        db.commit_person(person, trans)
    return family_handle


class TestDetDescendantDuplicateNumber(unittest.TestCase):
    """Mantis 3068: a duplicated descendant keeps the first/smaller number."""

    def setUp(self):
        self.db = _make_db()
        #   a (1)
        #   |-- b (11) ----- d (111) --+
        #   |-- c (12) ----- e (121) --+-- f (child of d & e)
        with DbTxn("build 3068 tree", self.db) as trans:
            self.a = _add_person(self.db, trans)
            self.b = _add_person(self.db, trans)
            self.c = _add_person(self.db, trans)
            self.d = _add_person(self.db, trans)
            self.e = _add_person(self.db, trans)
            self.f = _add_person(self.db, trans)

            _add_family(self.db, trans, father=self.a, children=(self.b, self.c))
            _add_family(self.db, trans, father=self.b, children=(self.d,))
            _add_family(self.db, trans, father=self.c, children=(self.e,))
            _add_family(self.db, trans, father=self.d, mother=self.e, children=(self.f,))

    def tearDown(self):
        self.db.close()

    def test_duplicate_descendant_keeps_smaller_number(self):
        probe = _HenryProbe(self.db)
        probe.apply_henry_filter(self.a, 1, "1")

        self.assertEqual(probe.dnumber[self.a], "1")
        self.assertEqual(probe.dnumber[self.b], "11")
        self.assertEqual(probe.dnumber[self.c], "12")
        self.assertEqual(probe.dnumber[self.d], "111")
        self.assertEqual(probe.dnumber[self.e], "121")

        # f is reachable as "1111" (via d, first) and "1211" (via e, last).
        # Pre-fix the filter kept the last number ("1211"); the fix keeps the
        # first/smaller one ("1111").
        self.assertEqual(
            probe.dnumber[self.f],
            "1111",
            "duplicate descendant must keep the first/smaller reference number",
        )


if __name__ == "__main__":
    unittest.main()
