"""Regression repro for Mantis 8841 — note hyperlink click hyper-sensitivity.

Bug: in the styled-text note editor/view a hyperlink fires "open in browser"
when the user clicks *beyond* the link — e.g. in the empty area to the right of
(or below) the last line — not just on the link glyph. ``Gtk.TextView`` snaps
such a click to the nearest text position (the end of the link) via
``get_iter_at_location()``, so the link opens on clicks that never landed on it.

This repro drives the *production* code path directly:
``gramps.gui.widgets.styledtexteditor.StyledTextEditor.on_motion_notify_event``
(which sets ``self.match`` / ``url_match``) followed by ``on_button_press_event``
(which calls ``_open_url_cb`` when a URL match is active). It builds a real
``StyledTextEditor`` in an offscreen ``Gtk.Window`` under the interface runner's
display, so it exercises the same glyph hit-testing GTK performs in gramps — not
a copy of it.

It is committed in the testbed (``engine/interface/``), NOT in ``patch.diff``, so
run-verify-interface.sh establishes red↔green purely by patch-applied-vs-not:
  * UNPATCHED — a click beside/below the link opens it  -> the test FAILS
  * PATCHED   — such a click is ignored                 -> the test PASSES

A click genuinely on the link text must still open it (the invariant the fix
must not break); that is asserted alongside the "beside" case. Both reported
geometries — to the RIGHT of the URL on its line, and BELOW the last line — are
covered.
"""

from __future__ import annotations

import unittest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from gramps.gen.lib import StyledText
from gramps.gui.widgets.styledtexteditor import StyledTextEditor


# A URL that matches the editor's GENURL pattern and renders on a single line.
URL = "http://example.com/page"


def _pump() -> None:
    """Drain the GTK main loop so layout/realization completes."""
    for _ in range(50):
        if not Gtk.events_pending():
            break
        Gtk.main_iteration()


class _FakeMotionEvent:
    """Minimal stand-in for a Gdk motion event (only ``.x`` / ``.y`` are read)."""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class _FakeButtonEvent:
    """Minimal stand-in for a plain left Gdk.EventType.BUTTON_PRESS event."""

    type = Gdk.EventType.BUTTON_PRESS
    button = 1

    def get_state(self):
        return Gdk.ModifierType(0)


class NoteLinkHitTestTest(unittest.TestCase):
    """Clicking beside/below a link must not open it; clicking on it still does."""

    def setUp(self) -> None:
        self.window = Gtk.Window()
        self.window.set_default_size(600, 400)
        self.editor = StyledTextEditor()
        # Read-only note view: in view mode a *plain* left click follows a link
        # (Ctrl-click in edit mode), which is exactly the reported bug context.
        self.editor.set_editable(False)
        self.editor.set_size_request(500, 200)
        self.window.add(self.editor)
        self.window.show_all()
        self.editor.set_text(StyledText(URL))
        _pump()

        # A realized TEXT window is required: on_motion emits "match-changed",
        # whose default handler sets the cursor on that window.
        if self.editor.get_window(Gtk.TextWindowType.TEXT) is None:
            self.editor.realize()
            _pump()

        # Capture link-open attempts instead of launching a browser.
        self.opened: list = []
        self.editor._open_url_cb = lambda *args, **kwargs: self.opened.append(args)

    def tearDown(self) -> None:
        self.window.destroy()
        _pump()

    def _widget_coords(self, buffer_x: int, buffer_y: int):
        return self.editor.buffer_to_window_coords(
            Gtk.TextWindowType.WIDGET, buffer_x, buffer_y
        )

    def _click(self, widget_x: int, widget_y: int) -> None:
        """Move the pointer to (widget_x, widget_y) then press button 1."""
        self.editor.on_motion_notify_event(
            self.editor, _FakeMotionEvent(widget_x, widget_y)
        )
        self.editor.on_button_press_event(self.editor, _FakeButtonEvent())

    def _on_link_widget_point(self):
        """Widget coords over the middle of the URL glyphs (a genuine hit)."""
        on_iter = self.editor.textbuffer.get_iter_at_offset(5)
        rect = self.editor.get_iter_location(on_iter)
        bx = rect.x + max(rect.width // 2, 1)
        by = rect.y + rect.height // 2
        return self._widget_coords(bx, by)

    def _end_rect(self):
        return self.editor.get_iter_location(self.editor.textbuffer.get_end_iter())

    def test_click_to_right_of_link_does_not_open(self) -> None:
        # Point far to the right of the URL on the SAME line (empty area). GTK
        # snaps get_iter_at_location() here to the end of the link text.
        end_rect = self._end_rect()
        beyond_bx = end_rect.x + end_rect.width + 300
        beyond_by = end_rect.y + end_rect.height // 2
        beyond_wx, beyond_wy = self._widget_coords(beyond_bx, beyond_by)

        # Bug 8841: a click that is NOT over the link glyph must not open it.
        self._click(beyond_wx, beyond_wy)
        self.assertEqual(
            self.opened,
            [],
            "click in the empty area to the right of the link opened it (bug 8841)",
        )

        # Invariant preserved: a click on the link text still opens it.
        on_wx, on_wy = self._on_link_widget_point()
        self._click(on_wx, on_wy)
        self.assertTrue(
            self.opened,
            "click directly on the link text failed to open the link",
        )

    def test_click_below_link_does_not_open(self) -> None:
        # Point well below the last rendered line (the other reported geometry);
        # GTK snaps get_iter_at_location() back up to the end of the link text.
        end_rect = self._end_rect()
        below_bx = end_rect.x + max(end_rect.width // 2, 1)
        below_by = end_rect.y + end_rect.height + 200
        below_wx, below_wy = self._widget_coords(below_bx, below_by)

        self._click(below_wx, below_wy)
        self.assertEqual(
            self.opened,
            [],
            "click in the empty area below the link opened it (bug 8841)",
        )


if __name__ == "__main__":
    unittest.main()
