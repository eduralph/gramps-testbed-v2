#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  The Gramps project
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
Regression test for gramps.gui.uimanager.UIManager.update_menu().

Mantis bug 13636: closing the Gramps main window before a queued update_menu()
runs (viewmanager.page_changer firing from GLib.idle_add during teardown) leaves
the previous toolbar already detached, so toolbar.get_parent() returns None.
Before the fix update_menu() blindly called toolbar.get_parent().remove(toolbar),
raising "AttributeError: 'NoneType' object has no attribute 'remove'".

Unit-layer substitute for the GUI shutdown race (the interface runner is not yet
ported in the testbed): Gtk (and config) are mocked so no display is needed and
only the None-guard logic is exercised, not real widget plumbing.
"""

import unittest
from unittest import mock

import gi

gi.require_version("Gtk", "3.0")

from gramps.gui.uimanager import UIManager


class UpdateMenuToolbarParentTest(unittest.TestCase):
    """update_menu() must tolerate a toolbar whose parent is already gone."""

    MINIMAL_UI = "<interface></interface>"

    def _make_uimanager(self, toolbar):
        """Real UIManager whose 'previous' builder is mocked to return the
        supplied toolbar from get_object('ToolBar'); the rebuilt builder comes
        from the patched Gtk, so no real widgets are created."""
        ui = UIManager(mock.MagicMock(), self.MINIMAL_UI)
        old_builder = mock.MagicMock()
        old_builder.get_object.return_value = toolbar
        ui.builder = old_builder
        return ui

    @mock.patch("gramps.gui.uimanager.config")
    @mock.patch("gramps.gui.uimanager.Gtk")
    def test_detached_toolbar_does_not_raise(self, _gtk, _config):
        """get_parent() is None (the 13636 shutdown race) -> no AttributeError."""
        toolbar = mock.MagicMock()
        toolbar.get_parent.return_value = None
        ui = self._make_uimanager(toolbar)

        try:
            ui.update_menu(init=False)
        except AttributeError as err:
            self.fail(
                "update_menu() raised AttributeError on a detached toolbar "
                "(Mantis 13636 shutdown race): %s" % err
            )

        # The toolbar-removal path really was reached.
        toolbar.get_parent.assert_called_once_with()

    @mock.patch("gramps.gui.uimanager.config")
    @mock.patch("gramps.gui.uimanager.Gtk")
    def test_attached_toolbar_is_still_updated(self, _gtk, config_mock):
        """Positive control: a toolbar that still has a parent is removed and
        repacked, so the None-guard does not short-circuit the normal path."""
        config_mock.get.return_value = 2  # interface.toolbar-style -> ICONS
        parent = mock.MagicMock()
        toolbar = mock.MagicMock()
        toolbar.get_parent.return_value = parent
        ui = self._make_uimanager(toolbar)

        ui.update_menu(init=False)

        parent.remove.assert_called_once_with(toolbar)
        self.assertTrue(parent.pack_start.called)


if __name__ == "__main__":
    unittest.main()
