"""Regression for Mantis #8604 ("editor opens behind the main window and
blocks the desktop on Windows").

Reported symptom (Windows only)
-------------------------------
On Windows, when Gramps is maximized but NOT the foreground application and
the user clicks an edit button, the editor window opens *behind* the main
window while its modal grab blocks the whole desktop -- the user cannot
interact with anything until they find and raise the hidden modal editor.

The Windows window manager, unlike the GNOME/X stack, does not raise a
newly mapped top-level window to the front when the owning process is not
the foreground application; it only maps it, leaving it stacked behind the
maximized main window even though the modal grab is active.

Invariant under test
--------------------
A newly-shown modal ``ManagedWindow`` must be *presented* -- raised to the
front and given focus -- when it is shown, regardless of whether the Gramps
process was the foreground application at the time. That is what puts the
modal grab on a visible window.

  Production path: ``gramps/gui/managedwindow.py`` ``ManagedWindow.show()``.
  Before the fix, ``show()`` maps the window with ``show_all()`` but never
  calls ``present()``, so on a non-cooperative window manager (Windows) the
  modal is left behind the main window. The fix adds a ``self.window.present()``
  for modal windows after ``show_all()``.

Why this test drives the mechanism, not the OS symptom
------------------------------------------------------
The *OS-level* symptom is irreducibly Windows-window-manager specific: on
the Linux/Xvfb stack that the interface suite runs on, ``show_all()`` on a
transient modal already lands in front, so the behind-the-parent stacking
cannot be reproduced here -- it is a **manual Windows** check at sign-off
(see the bundle's build-notes for the manual repro steps).

What *is* verifiable headless, and what this test asserts, is the invariant
that fixes it: that the real production ``ManagedWindow.show()`` presents a
modal window on show. This test therefore drives the genuine
``ManagedWindow.show()`` method (no re-implementation) with a lightweight
recording stand-in for the Gtk window collaborator, and asserts:

  * a **modal** ManagedWindow is ``present()``-ed after ``show_all()``
    (red before the fix, green after), and
  * a **non-modal** ManagedWindow is *not* presented (the fix is scoped to
    the modal-grab case named in the invariant, so no behaviour change for
    ordinary child windows).

It is NOT an AT-SPI/dogtail launch: it exercises one production method with
a fake collaborator, so it runs without launching Gramps.
"""

from __future__ import annotations

import unittest

from gramps.gui.managedwindow import ManagedWindow


class _RecordingWindow:
    """A stand-in for the Gtk top-level window ``ManagedWindow.show()``
    operates on. It records the methods ``show()`` calls so the test can
    assert on ordering and on whether ``present()`` was invoked. It is a
    collaborator, not the code under test -- ``ManagedWindow.show()`` is
    the real production method."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.transient_for = "unset"

    def set_transient_for(self, parent) -> None:
        self.transient_for = parent
        self.calls.append("set_transient_for")

    def show_all(self) -> None:
        self.calls.append("show_all")

    def present(self) -> None:
        self.calls.append("present")


def _make_managed_window(window, *, modal: bool, parent="parent") -> ManagedWindow:
    """Build a ManagedWindow far enough to call the real ``show()`` without
    the full ``__init__`` (which needs a live uistate/window-manager). Only
    the attributes ``show()`` reads are populated."""
    mw = ManagedWindow.__new__(ManagedWindow)
    mw.window = window
    mw.other_modal_window = None
    mw.parent_window = parent
    mw.modal = modal
    mw.opened = False
    return mw


class Bug8604ModalRaiseTest(unittest.TestCase):
    """``ManagedWindow.show()`` presents a modal window on show so its grab
    is always on a visible, raised window (Mantis #8604)."""

    def test_modal_window_is_presented_on_show(self) -> None:
        window = _RecordingWindow()
        mw = _make_managed_window(window, modal=True)

        mw.show()

        # The invariant: a modal window is raised to the front (present)
        # after being mapped (show_all). Before the #8604 fix, show() never
        # calls present(), so on Windows the modal is left behind the main
        # window -- this assertion is the red leg.
        self.assertIn(
            "present",
            window.calls,
            "ManagedWindow.show() did not present() the modal window; on a "
            "non-cooperative window manager (Windows) the modal grab is left "
            "on a window hidden behind the maximized main window (bug #8604).",
        )
        # present() must come AFTER the window is mapped, otherwise there is
        # nothing to raise.
        self.assertIn("show_all", window.calls)
        self.assertLess(
            window.calls.index("show_all"),
            window.calls.index("present"),
            "present() must be called after show_all()",
        )
        self.assertTrue(mw.opened)

    def test_non_modal_window_is_not_presented(self) -> None:
        window = _RecordingWindow()
        mw = _make_managed_window(window, modal=False)

        mw.show()

        # The fix is scoped to the modal-grab case in the invariant; a plain
        # non-modal child window keeps its previous behaviour (mapped, not
        # force-raised).
        self.assertIn("show_all", window.calls)
        self.assertNotIn(
            "present",
            window.calls,
            "A non-modal ManagedWindow should not be force-presented; the "
            "#8604 fix is scoped to modal windows.",
        )


if __name__ == "__main__":
    unittest.main()
