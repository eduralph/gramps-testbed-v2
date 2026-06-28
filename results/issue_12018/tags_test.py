#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  Eduard Ralph
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

"""Unit test for the Organize Tags dialog search configuration — Mantis 12018.

The "Organize Tags" dialog (``gramps/gui/views/tags.py``,
``OrganizeTagsDialog``) builds its tag list in a ``Gtk.TreeView`` via
``ListModel``. GtkTreeView ships interactive type-ahead search enabled by
default, but the dialog never bound it to a model column, so it stayed at
the GTK default of -1: pressing Ctrl-F (or just typing) popped up the search
box yet never scrolled/focused the matching tag — a control that does
nothing.

The fix points the TreeView's search at the visible Name column. This test
drives the production helpers that decide and apply that binding. It is kept
import-light on purpose: ``OrganizeTagsDialog`` is a ``ManagedWindow`` whose
``Gtk.TreeView`` cannot be instantiated on the headless C4 runner (GTK aborts
with "Can't create a GtkStyleContext without a display connection"), so this
unit drives the search-configuration seam with a recording stand-in instead
of building the widget. The end-to-end behaviour is checked manually: open
People list -> Edit -> Tag -> Organize Tags..., add several tags, then type a
tag's name -- the selection now jumps to the matching tag instead of the
search box doing nothing.
"""

import unittest

# ``gramps.gui.views.tags`` imports ``from gi.repository import Gtk`` at module
# load; pin the GTK 3 ABI before that import chain runs (matches the other
# gramps.gui unit tests).
import gi

gi.require_version("Gtk", "3.0")

from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gui.views.tags import (
    _TAG_NAME_COL,
    _setup_tag_search,
    _tag_list_columns,
)

_ = glocale.translation.sgettext


class _RecordingTreeView:
    """Minimal stand-in recording the search column the production code sets.

    GtkTreeView cannot be constructed without a display on the headless test
    runner, so this records ``set_search_column`` exactly as the real widget
    would receive it. The production code path (``_setup_tag_search``) is the
    one under test — this only captures its single side effect.
    """

    def __init__(self):
        self.search_column = None

    def set_search_column(self, column):
        self.search_column = column


class TagSearchConfigTest(unittest.TestCase):
    """Regression tests for Mantis 12018 — Organize Tags search is inert."""

    def test_name_column_index_matches_visible_name_column(self):
        """``_TAG_NAME_COL`` must point at the visible Name column.

        The binding is only useful if the index it targets really is the
        Name column in the production column layout. Guards against the
        index drifting away from the Name column (the "wrong, non-name
        column" the report describes).
        """
        columns = _tag_list_columns()
        self.assertEqual(
            columns[_TAG_NAME_COL][0],
            _("Name"),
            "the search column index must address the visible Name column",
        )

    def test_search_bound_to_name_column(self):
        """``_setup_tag_search`` must bind the TreeView search to the Name column.

        Before the fix the TreeView kept GtkTreeView's default search column
        of -1, so the type-ahead search box appeared but matched nothing.
        The dialog must point it at the Name column so the control works.
        """
        tree = _RecordingTreeView()
        _setup_tag_search(tree)
        self.assertEqual(
            tree.search_column,
            _TAG_NAME_COL,
            "Organize Tags must bind type-ahead search to the Name column",
        )
        self.assertNotEqual(
            tree.search_column,
            -1,
            "search must not be left at the inert GtkTreeView default (-1)",
        )


if __name__ == "__main__":
    unittest.main()
