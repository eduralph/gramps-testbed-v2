"""Regression for Mantis #8400 ("report options dialog is taller than the
screen; the OK button falls below the bottom of the monitor and cannot be
reached").

Reported symptom
----------------
A report option dialog with many options -- e.g. the Detailed Descendant Book
Report -- grows taller than the work area on a small display (1366x768).  The
shared ``ReportDialog`` only ever set the dialog *width*
(``set_default_size(600, -1)``) and appended every notebook page as a bare
``Gtk.Grid`` with no scroller, so a tall option set pushed the ``Gtk.Dialog``
action area (OK/Cancel) below the bottom edge of the monitor where the user
cannot click it, and the window's bottom edge cannot be dragged up either.

Invariant under test
--------------------
A report options dialog must never request more height than the monitor work
area: when its option content overflows, the *window* is clamped to the
work-area height (keeping the OK/Cancel action area on-screen) while the
overflowing option content becomes scrollable.

  Production path: ``gramps/gui/plug/report/_reportdialog.py``,
  ``ReportDialog.fit_to_screen()`` (added by the #8400 fix, called from
  ``init_interface`` just before ``self.show()``).  It reads the monitor
  work-area height (``ReportDialog._work_area_height``), the window's natural
  height (``get_preferred_size``) and, when the natural height exceeds the work
  area, re-issues ``set_default_size(600, available)`` so the dialog fits.  The
  coupled ``ReportDialog._scrolled_page`` wraps each notebook page in a
  ``Gtk.ScrolledWindow`` so the clamped content scrolls instead of being
  clipped.

Why this drives production, not a copy
--------------------------------------
This test imports the real ``ReportDialog`` and calls the real
``fit_to_screen()`` decision method, injecting a lightweight recording
stand-in for the ``Gtk`` window collaborator and stubbing the monitor
work-area lookup.  It asserts the invariant the fix restores:

  * an overflowing dialog (natural height >> work area) is clamped to a height
    that fits within the work area and is strictly shorter than its natural
    height (RED before the fix: ``fit_to_screen`` does not exist, so the call
    raises ``AttributeError``; GREEN after), and
  * a dialog that already fits is left at its natural size (no regression for
    ordinary reports), and
  * when no monitor geometry is available the default size is left untouched.

It also guards the *wiring*, not just the method: a fourth check inspects the
real ``init_interface`` source and asserts it calls ``fit_to_screen()`` before
``self.show()`` -- so a fix that adds the method but forgets to invoke it from
the dialog-creation path fails here rather than leaving real report dialogs
taller than the screen.

It is NOT a dogtail/AT-SPI launch: it exercises one production method with a
fake collaborator, so it needs no running Gramps.  It lives in the interface
suite (not ``gramps/gui/test/``) because importing ``ReportDialog`` pulls in
the ``gramps.gui.plug`` widget stack, which only imports under the GTK-3 pin
the interface runner applies (``gi_bootstrap``); the plain headless core
runner resolves GTK 4 and cannot import it.  The full on-screen visual /
scrollbar behaviour is an irreducibly-GUI check recorded in the bundle's
build-notes for manual sign-off.
"""

from __future__ import annotations

import unittest

from gramps.gui.plug.report._reportdialog import ReportDialog


class _Size:
    """Stand-in for the Gtk requisition ``get_preferred_size`` returns."""

    def __init__(self, height: int) -> None:
        self.height = height


class _RecordingWindow:
    """A stand-in for the ``Gtk.Dialog`` ``fit_to_screen`` operates on.

    It reports a fixed natural height and records the ``set_default_size`` the
    clamp issues.  It is a collaborator, not the code under test --
    ``ReportDialog.fit_to_screen`` is the real production method.
    """

    def __init__(self, natural_height: int) -> None:
        self._natural = natural_height
        self.default_size: tuple[int, int] | None = None

    def get_preferred_size(self):
        # (minimum, natural) -- fit_to_screen reads the natural height.
        return (_Size(self._natural), _Size(self._natural))

    def set_default_size(self, width: int, height: int) -> None:
        self.default_size = (width, height)


def _make_dialog(window: _RecordingWindow, work_area_height: int) -> ReportDialog:
    """Build a ReportDialog far enough to call the real ``fit_to_screen``
    without the full ``__init__`` (which needs a live uistate / window
    manager).  Only what ``fit_to_screen`` reads is populated; the monitor
    work-area lookup is stubbed so the geometry is deterministic and no
    display is required."""
    rd = ReportDialog.__new__(ReportDialog)
    rd.window = window
    # Stub the monitor-detection collaborator; the clamp DECISION under test
    # is the real production method.
    rd._work_area_height = lambda: work_area_height
    return rd


class Bug8400ReportDialogFitsScreenTest(unittest.TestCase):
    """``ReportDialog`` never requests more height than the monitor work area,
    so the OK/Cancel buttons stay reachable (Mantis #8400)."""

    # A representative small-laptop work area: the 1366x768 panel of the bug,
    # less a typical top/bottom panel.
    WORK_AREA = 720

    def test_overflowing_dialog_is_clamped_to_the_work_area(self) -> None:
        window = _RecordingWindow(natural_height=1600)  # far taller than 720
        rd = _make_dialog(window, self.WORK_AREA)

        rd.fit_to_screen()

        self.assertIsNotNone(
            window.default_size,
            "fit_to_screen() did not clamp an overflowing report dialog; its "
            "OK/Cancel buttons fall below the bottom of the monitor (bug #8400).",
        )
        clamped_height = window.default_size[1]
        self.assertLessEqual(
            clamped_height,
            self.WORK_AREA,
            "an overflowing report dialog must never be taller than the monitor "
            "work area, or the OK button is unreachable",
        )
        self.assertLess(
            clamped_height,
            1600,
            "the clamped height must be shorter than the natural (overflowing) "
            "height",
        )

    def test_fitting_dialog_keeps_its_natural_size(self) -> None:
        window = _RecordingWindow(natural_height=400)  # already fits in 720
        rd = _make_dialog(window, self.WORK_AREA)

        rd.fit_to_screen()

        self.assertIsNone(
            window.default_size,
            "a report dialog that already fits must be left at its natural "
            "size; the #8400 fix must not resize ordinary dialogs",
        )

    def test_unknown_work_area_leaves_default_size_untouched(self) -> None:
        window = _RecordingWindow(natural_height=1600)
        rd = _make_dialog(window, work_area_height=0)  # no monitor geometry

        rd.fit_to_screen()

        self.assertIsNone(
            window.default_size,
            "with no monitor geometry the dialog must not be clamped to nothing",
        )

    def test_init_interface_wires_fit_to_screen_before_show(self) -> None:
        # The clamp only reaches real report dialogs if the production creation path calls
        # it. The three tests above exercise fit_to_screen() in isolation, so a fix that
        # ADDS the method but forgets to CALL it from init_interface would still pass while
        # actual dialogs stayed taller than the screen. Guard that wiring by inspecting the
        # real init_interface source: fit_to_screen() must be invoked there, before show().
        import inspect

        src = inspect.getsource(ReportDialog.init_interface)
        self.assertIn(
            "fit_to_screen(",
            src,
            "ReportDialog.init_interface must CALL fit_to_screen(); the method merely "
            "existing does not clamp an opened report dialog (bug #8400).",
        )
        self.assertLess(
            src.index("fit_to_screen("),
            src.index("self.show("),
            "fit_to_screen() must run BEFORE self.show(), or the dialog is shown at its "
            "overflowing height with the OK button off-screen.",
        )


if __name__ == "__main__":
    unittest.main()
