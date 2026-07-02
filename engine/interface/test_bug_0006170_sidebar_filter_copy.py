"""Regression for Mantis #6170 ("Ctrl+C in the sidebar/filter text entry copies
the selected list object and pops up the Clipboard instead of copying text").

Reported by fireman_biff (3.4.2), user2418 (4.0.2) and sam888 on master
("CTRL+C pops up the Clipboard"). In a list view whose sidebar/filter has a
focused text entry, pressing Ctrl+C does not copy the selected text — it copies
the currently selected list object to the Gramps clipboard and pops the
Clipboard window up. Ctrl+X (cut) and Ctrl+V (paste) already work in the same
entry; the remaining live defect is Ctrl+C being stolen from the focused entry.

Root cause (read on maintenance/gramps61)
------------------------------------------
``NavigationView.key_press_handler`` (gramps/gui/views/navigationview.py:481-490)
is connected on the *toplevel* window (gramps/gui/views/pageview.py:131,
``self.uistate.window.connect("key-press-event", self.key_press_handler)``).
GtkWindow delivers the key-press-event to the toplevel *before* the focused
child, so this handler runs first; for Ctrl+C it unconditionally calls
``call_copy()`` and returns ``True``, consuming the event. The focused
text-editable entry therefore never sees Ctrl+C, and ``call_copy`` ->
``copy_to_clipboard`` brings up the Clipboard window with the selected list
object (gramps/gui/views/pageview.py:274-295). Cut/Paste are unaffected because
this handler only intercepts ``Gdk.KEY_c``.

Fix
---
Before invoking the object copy, ``key_press_handler`` consults
``self.uistate.window.get_focus()``: when a text-editable widget
(``Gtk.Editable`` / ``Gtk.TextView``) holds keyboard focus it returns ``False``
so the event propagates to that widget, which performs the standard text Copy.
The object copy is preserved when the list/tree itself holds the focus. This is
a view-level fix in the shared ``NavigationView``, so it holds for every list
view whose sidebar/bottombar carries a text entry (not just the People view).

Repro driven here
-----------------
Open the People category, select a person (so the object-copy path has a handle
to copy — otherwise ``copy_to_clipboard`` opens no window), then focus the
sidebar/filter text entry, type text and select it, and press Ctrl+C. Pre-fix
the Gramps Clipboard window appears (the person was copied); post-fix no
Clipboard window appears (the focused entry owns Copy). The presence of a
showing top-level frame/window titled "Clipboard" is the AT-SPI-observable
red<->green discriminator named by the brief.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory; this GUI test is the
characterisation the human weighs at sign-off. It uses graceful skips when the
test infra cannot drive a widget, so only the delivered #6170 symptom (Clipboard
window stolen from the focused entry) reports a failure.
"""

from __future__ import annotations

import time
import unittest

from .base import GrampsInterfaceTestCase

FILTER_TEXT = "Smith6170"


class Bug6170SidebarFilterCopyTest(GrampsInterfaceTestCase):
    """Ctrl+C with focus in a sidebar/filter text entry copies the text and does
    NOT open the Gramps Clipboard window (Mantis 6170)."""

    TREE_NAME = "TestTree"
    LAUNCH_CONFIG = (
        "interface.main-window-width:1800",
        "interface.main-window-height:1000",
    )

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _is_usable(node) -> bool:
        try:
            if not node.showing:
                return False
            pos, size = node.position, node.size
        except Exception:
            return False
        return pos[0] >= 0 and pos[1] >= 0 and size[0] > 0 and size[1] > 0

    def _click_toggle(self, name: str, timeout: float = 8.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n, _n=name: n.roleName == "toggle button"
                and (n.name or "") == _n
            ):
                if self._is_usable(n):
                    try:
                        n.click()
                        return True
                    except Exception:
                        pass
            time.sleep(0.3)
        return False

    def _open_people_category(self) -> None:
        # People is the default category on launch; clicking its sidebar toggle
        # (if present) makes the test order-independent. Non-fatal either way.
        self._click_toggle("People")
        time.sleep(0.6)

    def _select_a_person(self) -> bool:
        """Select the first row in the People list so an object handle exists to
        copy — without a selection ``copy_to_clipboard`` opens no window and the
        pre-fix red symptom cannot be established."""
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            for table in self.app.findChildren(
                lambda n: n.roleName in ("tree table", "table")
            ):
                if not self._is_usable(table):
                    continue
                for cell in table.findChildren(
                    lambda n: n.roleName == "table cell"
                ):
                    if self._is_usable(cell):
                        try:
                            cell.click()
                            return True
                        except Exception:
                            pass
            time.sleep(0.3)
        return False

    def _sidebar_text_entry(self):
        """The sidebar/filter's editable text entry.

        The People sidebar filter lays out labelled rows ("Name", "ID", ...),
        each a Gtk.Entry rendered as an AT-SPI 'text'/'entry' node. Prefer the
        entry that shares a container with the "Name" label; fall back to the
        first usable text entry that is not inside a dialog.
        """
        entries = [
            t
            for t in self.app.findChildren(
                lambda n: n.roleName in ("text", "entry")
            )
            if self._is_usable(t)
        ]
        if not entries:
            return None
        for label in self.app.findChildren(
            lambda n: n.roleName == "label" and (n.name or "").strip() == "Name"
        ):
            try:
                parent = label.parent
            except Exception:
                continue
            for entry in entries:
                try:
                    if entry.parent == parent:
                        return entry
                except Exception:
                    pass
        return entries[0]

    def _clipboard_window_showing(self) -> bool:
        """True iff a showing top-level frame/window titled 'Clipboard' exists.

        Restricted to window-class roles so the Edit-menu / toolbar 'Clipboard'
        *button* (a push button) is never mistaken for the Clipboard window.
        """
        for w in self.app.findChildren(
            lambda n: n.roleName in ("frame", "dialog", "window")
        ):
            try:
                if w.showing and "Clipboard" in (w.name or ""):
                    return True
            except Exception:
                pass
        return False

    # -------------------------------------------------------------------- test
    def test_ctrl_c_in_sidebar_entry_does_not_open_clipboard(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        self._open_people_category()

        if not self._select_a_person():
            self.skipTest("could not select a person row (infra)")

        entry = self._sidebar_text_entry()
        if entry is None:
            self.skipTest("sidebar/filter text entry not found (infra)")

        from dogtail.rawinput import keyCombo, typeText

        try:
            entry.click()  # move keyboard focus into the editable entry
            time.sleep(0.3)
            typeText(FILTER_TEXT)
            keyCombo("<Control>a")  # select the typed text
            time.sleep(0.3)
        except Exception:
            self.skipTest("could not focus/fill the sidebar entry (infra)")

        # No Clipboard window should be up yet — otherwise the red/green signal
        # is contaminated by prior state.
        if self._clipboard_window_showing():
            self.skipTest("Clipboard window already open before Ctrl+C (infra)")

        keyCombo("<Control>c")
        time.sleep(1.0)

        if self._clipboard_window_showing():
            self._capture_screenshot("bug6170-clipboard-stolen")
        self.assertFalse(
            self._clipboard_window_showing(),
            "Ctrl+C with keyboard focus in the sidebar/filter text entry opened "
            "the Gramps Clipboard window (the selected person was copied) instead "
            "of letting the focused entry copy its selected text to the system "
            "clipboard (Mantis 6170: the view-level Ctrl+C accelerator, connected "
            "on the toplevel window, shadows the focused text-editable widget).",
        )


if __name__ == "__main__":
    unittest.main()
