#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025
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
Regression test for Mantis 7814.

The Detailed Descendant Report printed a "Died _____ in _____." line for a
person who is still living and has no death event (the report's narrator
emits the empty-entry placeholders when "replace missing dates/places" is on).
The fix gates every death/burial emission with ``if not probably_alive(...)``
(detdescendantreport.py write_person_info and __write_children).

This test drives the SHIPPED production routine ``write_person_info`` (and the
child-list routine ``__write_children``) directly against an in-memory database
and asserts that no death narrative is emitted for a ``probably_alive`` person
with no death event, while it IS emitted for a deceased person — so the guard
is exercised, not re-implemented.  Removing either guard makes the matching
assertion fail.
"""

import unittest

from gramps.gen.db import DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.lib import (
    ChildRef,
    Date,
    Event,
    EventRef,
    EventType,
    Family,
    Name,
    Person,
    Surname,
)
from gramps.gen.display.name import displayer as _nd
from gramps.plugins.lib.libnarrate import Narrator
from gramps.plugins.textreport.detdescendantreport import (
    DetDescendantReport,
    EMPTY_ENTRY,
)


def _make_db():
    """Create a fresh in-memory SQLite database."""
    db = make_database("sqlite")
    db.load(":memory:")
    return db


def _add_event(db, trans, event_type, year):
    """Create a dated event of the given type, store it, return its handle."""
    event = Event()
    event.set_type(EventType(event_type))
    date = Date()
    date.set_yr_mon_day(year, 0, 0)
    event.set_date_object(date)
    return db.add_event(event, trans)


def _add_person(db, trans, given, surname, birth_year, death_year=None):
    """
    Create a person with a primary name and a birth event, optionally a death
    event.  Returns the committed person handle.
    """
    person = Person()
    person.set_gender(Person.MALE)

    name = Name()
    name.set_first_name(given)
    sn = Surname()
    sn.set_surname(surname)
    name.add_surname(sn)
    person.set_primary_name(name)

    birth_handle = _add_event(db, trans, EventType.BIRTH, birth_year)
    birth_ref = EventRef()
    birth_ref.set_reference_handle(birth_handle)
    person.set_birth_ref(birth_ref)

    if death_year is not None:
        death_handle = _add_event(db, trans, EventType.DEATH, death_year)
        death_ref = EventRef()
        death_ref.set_reference_handle(death_handle)
        person.set_death_ref(death_ref)

    return db.add_person(person, trans)


class _RecordingDoc:
    """Minimal docgen stand-in: records every text written to the document."""

    def __init__(self):
        self.chunks = []

    def start_paragraph(self, *args, **kwargs):
        pass

    def end_paragraph(self, *args, **kwargs):
        pass

    def write_text(self, text="", *args, **kwargs):
        self.chunks.append(text)

    def write_text_citation(self, text="", *args, **kwargs):
        self.chunks.append(text)

    def write_styled_note(self, *args, **kwargs):
        pass

    def text(self):
        return "".join(self.chunks)


def _make_report(db):
    """
    Build a DetDescendantReport instance wired with just enough collaborators
    to call the real ``write_person_info`` / ``__write_children`` methods, with
    the "replace missing dates/places" placeholders enabled (the condition that
    triggered Mantis 7814).
    """
    report = DetDescendantReport.__new__(DetDescendantReport)
    report._db = db
    report.database = db
    report._name_display = _nd
    report._ = lambda s: s
    report.doc = _RecordingDoc()
    report.addimages = False
    report.verbose = False
    report.calcageflag = False
    report.inc_notes = False
    report.inc_names = False
    report.inc_events = False
    report.inc_addr = False
    report.inc_attrs = False
    # __write_children collaborators
    report.showgender = False
    report.childref = False
    report.prev_gen_handles = {}
    report.inc_ssign = False
    report.dnumber = {}
    report.want_ids = False
    report.list_children_spouses = False

    narrator = Narrator(
        db,
        verbose=False,
        empty_date=EMPTY_ENTRY,
        empty_place=EMPTY_ENTRY,
    )
    # name-mangled private attribute used by the report
    report._DetDescendantReport__narrator = narrator
    return report


def _would_be_died_text(db, person):
    """The death sentence the narrator produces for `person` (no guard)."""
    narrator = Narrator(
        db,
        verbose=False,
        empty_date=EMPTY_ENTRY,
        empty_place=EMPTY_ENTRY,
    )
    narrator.set_subject(person)
    return narrator.get_died_string().strip()


class TestDetDescendantDeathGuard(unittest.TestCase):
    """Mantis 7814: no death line for a probably-alive, death-event-less person."""

    def setUp(self):
        self.db = _make_db()

    def tearDown(self):
        self.db.close()

    # ------------------------------------------------------------------
    # write_person_info (detdescendantreport.py:902 guard)
    # ------------------------------------------------------------------

    def test_living_person_emits_no_death_line(self):
        """A living person with no death event yields no 'Died ____' line."""
        with DbTxn("test", self.db) as trans:
            handle = _add_person(self.db, trans, "Liv", "Ing", birth_year=1990)
        person = self.db.get_person_from_handle(handle)

        # Sanity: the narrator on its own WOULD emit a death sentence (the bug
        # symptom) — so the report-level guard is what must suppress it.
        died = _would_be_died_text(self.db, person)
        self.assertTrue(died, "expected the narrator to produce a death sentence")

        report = _make_report(self.db)
        report.write_person_info(person)
        output = report.doc.text()

        self.assertNotIn(
            died,
            output,
            "Mantis 7814: death narrative emitted for a probably-alive person",
        )
        self.assertNotIn("died", output.lower())
        # the routine still ran and produced the birth narrative
        self.assertIn("orn", output, "expected a birth sentence in the output")

    def test_deceased_person_emits_death_line(self):
        """A deceased person still gets the death narrative (guard not over-broad)."""
        with DbTxn("test", self.db) as trans:
            handle = _add_person(
                self.db, trans, "Dec", "Ing", birth_year=1850, death_year=1850
            )
        person = self.db.get_person_from_handle(handle)

        died = _would_be_died_text(self.db, person)
        self.assertTrue(died)

        report = _make_report(self.db)
        report.write_person_info(person)
        output = report.doc.text()

        self.assertIn(
            died,
            output,
            "death narrative wrongly suppressed for a deceased person",
        )

    # ------------------------------------------------------------------
    # __write_children (detdescendantreport.py:769 guard)
    # ------------------------------------------------------------------

    def _family_with_child(self, child_handle):
        with DbTxn("test", self.db) as trans:
            family = Family()
            cref = ChildRef()
            cref.set_reference_handle(child_handle)
            family.add_child_ref(cref)
            fam_handle = self.db.add_family(family, trans)
        return self.db.get_family_from_handle(fam_handle)

    def test_living_child_emits_no_death_line(self):
        """A living child in the child list yields no death line."""
        with DbTxn("test", self.db) as trans:
            child_handle = _add_person(self.db, trans, "Kid", "Ing", birth_year=2000)
        child = self.db.get_person_from_handle(child_handle)
        died = _would_be_died_text(self.db, child)
        self.assertTrue(died)

        family = self._family_with_child(child_handle)
        report = _make_report(self.db)
        report._DetDescendantReport__write_children(family)
        output = report.doc.text()

        self.assertNotIn(
            died,
            output,
            "Mantis 7814: death narrative emitted for a living child",
        )
        self.assertNotIn("died", output.lower())

    def test_deceased_child_emits_death_line(self):
        """A deceased child in the child list still gets the death narrative."""
        with DbTxn("test", self.db) as trans:
            child_handle = _add_person(
                self.db, trans, "Old", "Ing", birth_year=1850, death_year=1850
            )
        child = self.db.get_person_from_handle(child_handle)
        died = _would_be_died_text(self.db, child)
        self.assertTrue(died)

        family = self._family_with_child(child_handle)
        report = _make_report(self.db)
        report._DetDescendantReport__write_children(family)
        output = report.doc.text()

        self.assertIn(
            died,
            output,
            "death narrative wrongly suppressed for a deceased child",
        )


if __name__ == "__main__":
    unittest.main()
