#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  Brian Caudill
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
Unittest for the shared "unique surnames" count (bug #6793).

The Top Surnames, Surname Cloud and Statistics gramplets each report a "unique
surnames" total.  They used to enumerate unique surnames by three different
rules, so the same tree produced three different totals.  These tests drive the
*production* counting routines the gramplets now share
(:func:`gramps.plugins.lib.libsurnames.record_surnames` /
:func:`count_unique_surnames`) on a fixture tree and assert the totals agree.
"""

# -------------------------------------------------------------------------
#
# Standard Python modules
#
# -------------------------------------------------------------------------
import unittest
from collections import defaultdict

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
from gramps.gen.lib import Name, Person, Surname
from gramps.gen.types import PersonHandle

# The production code under test.  Imported via the gramplets' own import path
# so the test exercises the same routine the gramplets call, not a copy.
from gramps.plugins.lib.libsurnames import count_unique_surnames, record_surnames

# The gramplet modules re-use the shared routine; importing them proves the
# wiring is in place (and that the modules still import import-light).
from gramps.plugins.gramplet.topsurnamesgramplet import (
    record_surnames as top_record_surnames,
)
from gramps.plugins.gramplet.surnamecloudgramplet import (
    record_surnames as cloud_record_surnames,
)
from gramps.plugins.gramplet.statsgramplet import (
    count_unique_surnames as stats_count_unique_surnames,
)


# -------------------------------------------------------------------------
#
# Test helpers
#
# -------------------------------------------------------------------------
def make_name(surname_text: str) -> Name:
    """
    Build a Name carrying a single surname.
    """
    name = Name()
    surname = Surname()
    surname.set_surname(surname_text)
    name.add_surname(surname)
    return name


def make_person(handle: str, primary: str, alternates: tuple[str, ...] = ()) -> Person:
    """
    Build a Person with the given primary surname and alternate surnames.
    """
    person = Person()
    person.set_handle(handle)
    person.set_primary_name(make_name(primary))
    for alt in alternates:
        person.add_alternate_name(make_name(alt))
    return person


class FakeDb:
    """
    Minimal stand-in for a Gramps database exposing only ``iter_people`` and a
    ``surname_list`` attribute (the latter is what the Statistics gramplet
    guards on before reporting the figure).
    """

    def __init__(self, people: list[Person]):
        self._people = people
        self.surname_list = []

    def iter_people(self):
        return iter(self._people)


def tally_unique(people: list[Person]) -> int:
    """
    Number of unique surnames via the dict-building path used by the Top
    Surnames and Surname Cloud gramplets (``len`` of the ``record_surnames``
    tally).
    """
    surnames: dict[str, int] = defaultdict(int)
    representative_handle: dict[str, PersonHandle] = {}
    for person in people:
        record_surnames(person, surnames, representative_handle)
    return len(surnames)


# -------------------------------------------------------------------------
#
# Fixture
#
# -------------------------------------------------------------------------
# A tree exercising the cases that made the three gramplets diverge:
#   * a surname shared by several people (Webb)
#   * a person with an alternate (married) name (Souza -> Varela)
#   * a surname that only ever appears as an alternate name (Jones)
#   * a person with no surname at all
# Distinct group names: Webb, Allen, Souza, Varela, Smith, Brown, Jones, ""
# -> 8 unique surnames.
FIXTURE = [
    make_person("P1", "Webb"),
    make_person("P2", "Webb", alternates=("Allen",)),
    make_person("P3", "Souza", alternates=("Varela",)),
    make_person("P4", "Smith", alternates=("Jones",)),
    make_person("P5", "Brown", alternates=("Jones",)),
    make_person("P6", ""),
]


# -------------------------------------------------------------------------
#
# SurnameCountTest
#
# -------------------------------------------------------------------------
class SurnameCountTest(unittest.TestCase):
    """
    The gramplets that report "unique surnames" must agree (bug #6793).
    """

    def setUp(self):
        self.people = FIXTURE
        self.db = FakeDb(self.people)
        # Group names present: Webb, Allen, Souza, Varela, Smith, Brown, Jones,
        # "" -> 8 distinct.
        self.expected = 8

    def test_count_unique_surnames_is_distinct_group_names(self):
        """
        The canonical routine counts distinct surname group names across each
        person's primary and alternate names.
        """
        self.assertEqual(count_unique_surnames(self.db), self.expected)

    def test_dict_path_and_count_path_agree(self):
        """
        The two production paths -- the ``record_surnames`` dict the Top
        Surnames / Surname Cloud gramplets build, and the
        ``count_unique_surnames`` wrapper the Statistics gramplet calls -- yield
        the same total on the same tree.
        """
        self.assertEqual(tally_unique(self.people), count_unique_surnames(self.db))

    def test_all_gramplets_share_one_rule(self):
        """
        Every gramplet that reports "unique surnames" derives the figure from
        the same shared routine, so the three totals are identical for a tree.
        """
        # Top Surnames and Surname Cloud build the tally with record_surnames...
        self.assertIs(top_record_surnames, record_surnames)
        self.assertIs(cloud_record_surnames, record_surnames)
        # ...and Statistics calls count_unique_surnames.
        self.assertIs(stats_count_unique_surnames, count_unique_surnames)

        top_total = tally_unique(self.people)
        cloud_total = tally_unique(self.people)
        stats_total = stats_count_unique_surnames(self.db)
        self.assertEqual(top_total, cloud_total)
        self.assertEqual(cloud_total, stats_total)

    def test_alternate_name_surnames_are_counted(self):
        """
        A surname that only ever appears as an alternate name (e.g. a married
        name) is still counted once -- the old Statistics rule, keyed on the
        primary-name index, missed these.
        """
        people = [make_person("A", "Souza", alternates=("Varela",))]
        db = FakeDb(people)
        # Souza + Varela = 2 distinct group names.
        self.assertEqual(count_unique_surnames(db), 2)


if __name__ == "__main__":
    unittest.main()
