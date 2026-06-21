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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Unit tests for :func:`tests.addon_paths.is_in_addons_tree`.

Guards review-nit (c): ``_get_addon_plugins`` (and the import/export smoke
tests) must classify a plugin's ``fpath`` with a path-*prefix* check, not the
former ``ADDONS_ROOT in pdata.fpath`` substring test — otherwise a sibling
directory sharing the repo's name prefix (e.g. a ``addons-source-6.1`` checkout
beside ``addons-source``) is wrongly treated as part of this repository.

Import-light by design: it imports only :mod:`tests.addon_paths`, so it runs
under a plain ``python3 -m unittest`` with no Gramps, GI, or display.
"""

# ------------------------
# Python modules
# ------------------------
import os
import unittest

# ------------------------
# Module under test
# ------------------------
from tests.addon_paths import is_in_addons_tree


class IsInAddonsTreeTest(unittest.TestCase):
    """Path-prefix matching for plugin ``fpath`` classification."""

    def setUp(self) -> None:
        # An absolute, OS-portable addons-source root, e.g. /work/addons-source.
        self.root = os.path.join(os.sep + "work", "addons-source")

    def test_direct_child_matches(self) -> None:
        """A plugin directory directly under the root is inside the tree."""
        self.assertTrue(is_in_addons_tree(os.path.join(self.root, "Sqlite"), self.root))

    def test_nested_path_matches(self) -> None:
        """A deeper path under the root is inside the tree."""
        self.assertTrue(
            is_in_addons_tree(
                os.path.join(self.root, "Sqlite", "sqlite.gpr.py"), self.root
            )
        )

    def test_sibling_sharing_name_prefix_not_matched(self) -> None:
        """A sibling dir whose name only *starts with* the root is NOT inside.

        This is the exact case the old ``ADDONS_ROOT in fpath`` substring test
        got wrong: ``/work/addons-source`` is a substring of
        ``/work/addons-source-6.1/...`` but it is a different directory.
        """
        sibling = self.root + "-6.1"
        self.assertFalse(
            is_in_addons_tree(os.path.join(sibling, "SomeAddon", "x.gpr.py"), self.root)
        )

    def test_root_itself_not_matched(self) -> None:
        """The bare root (no trailing separator/child) is not a plugin path."""
        self.assertFalse(is_in_addons_tree(self.root, self.root))

    def test_empty_or_missing_fpath_not_matched(self) -> None:
        """A falsy ``fpath`` (unregistered plugin) is never inside the tree."""
        self.assertFalse(is_in_addons_tree("", self.root))
        self.assertFalse(is_in_addons_tree(None, self.root))


if __name__ == "__main__":
    unittest.main()
