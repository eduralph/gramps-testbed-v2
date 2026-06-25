# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2024  Gramps developers
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
Unittest for the RCS subprocess message-assembly logic in dbman.py
(issue 13518).

The five RCS helpers in :mod:`gramps.gui.dbman` open ``stderr`` with a binary
``subprocess.PIPE`` and used to build their error message with
``"\\n".join(proc.stderr.readlines())``.  ``readlines()`` returns ``bytes``, so
joining the lines into a ``str`` raised
``TypeError: sequence item 0: expected str instance, bytes found`` and crashed
the operation whenever the subprocess wrote anything to stderr.

Production now routes every one of those sites through
:func:`gramps.gui.dbman_utils.read_subprocess_messages`; this test drives that
same function (it carries no GTK dependency, so it runs headless).
"""

import unittest

from .. import dbman_utils


class _FakeStderr:
    """A binary stderr pipe stand-in: ``readlines()`` yields ``bytes``."""

    def __init__(self, lines):
        self._lines = list(lines)
        self.closed = False

    def readlines(self):
        return self._lines

    def close(self):
        self.closed = True


class _FakeProc:
    """A minimal ``subprocess.Popen`` stand-in exposing only ``stderr``."""

    def __init__(self, stderr_lines):
        self.stderr = _FakeStderr(stderr_lines)


class TestReadSubprocessMessages(unittest.TestCase):
    def test_documents_the_bug(self):
        """The naive join (the pre-fix production code) raises TypeError."""
        proc = _FakeProc([b"rcs: error\n", b"co aborted\n"])
        with self.assertRaises(TypeError):
            "\n".join(proc.stderr.readlines())

    def test_decodes_bytes_to_str(self):
        """The production helper decodes bytes and returns a usable str."""
        proc = _FakeProc([b"rcs: archive corrupt\n", b"ci aborted\n"])
        message = dbman_utils.read_subprocess_messages(proc)
        self.assertIsInstance(message, str)
        self.assertEqual(message, "rcs: archive corrupt\n\nci aborted\n")

    def test_empty_stderr_is_empty_str(self):
        """No stderr output yields an empty string, not an error."""
        proc = _FakeProc([])
        self.assertEqual(dbman_utils.read_subprocess_messages(proc), "")

    def test_non_utf8_does_not_raise(self):
        """A non-UTF-8 diagnostic still decodes to a str instead of crashing."""
        proc = _FakeProc([b"rcs: \xff\xfe broken\n"])
        message = dbman_utils.read_subprocess_messages(proc)
        self.assertIsInstance(message, str)
        self.assertIn("broken", message)


if __name__ == "__main__":
    unittest.main()
