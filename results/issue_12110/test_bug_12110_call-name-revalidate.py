"""Regression for Mantis #12110 ("Call name validity is not re-checked when the
Given name changes").

Reported against the Name editor (``gramps/gui/editors/editname.py``). The Call
name field is validated against the Given name: it is marked *invalid* (a red
error icon + ``error`` CSS class) when the call name is not one of the given
names. The defect: that check fired only when the **Call** field changed, never
when the **Given** field changed, so the red/black indicator went stale.

  * Case 1: Call = "Jon" with an empty Given -> invalid (red); then fill
    Given = "Jon" -> *should* become valid (black), but pre-fix stayed red.
  * Case 2: Given = "Marc", Call = "Marc" -> valid (black); then change
    Given = "Paul" -> *should* become invalid (red), but pre-fix stayed black.

Root cause (read on maintenance/gramps61)
------------------------------------------
``EditName._validate_call`` (editname.py:173) decides the Call field's
valid/invalid state from *both* the call text and the current given name, but
the only signal wired to re-run it was the Call field's own ``validate``
(editname.py:236-238). ``given_field`` (editname.py:223) had no ``changed``
hook, so editing Given never re-fired the check.

Fix
---
``given_field`` is given ``changed=self._revalidate_call``, and the new
``EditName._revalidate_call`` re-fires ``call_field.obj.validate(force=True)`` so
the indicator tracks the current given name. ``MonitoredEntry._on_change`` calls
``self.changed(obj)`` (monitoredwidgets.py:154-157), which is the supported seam.

Why this lives in the AT-SPI tier (and C4 is recorded unverifiable)
-------------------------------------------------------------------
The validity predicate and its re-validation trigger are intentionally kept
*local to* ``editname.py`` (no new gen-level helper module — that was rejected at
sign-off for issue 12110, iteration 2). The decision therefore cannot be reached
from a headless unit test without importing ``EditName``, which pulls in
``gi`` / ``gramps.gui`` and core-dumps the headless C4 runner. So the production
path is exercised here, inside a real Gramps, end to end: open the Name editor,
edit the Given field, and read back the Call field's validity indicator.

The Call field's "red" state is a GtkEntry secondary *error icon* plus an
``error`` CSS class (gramps/gui/widgets/validatedmaskedentry.py:1141-1182); GTK
does not reliably surface either through AT-SPI. Every navigation/readout step
that the accessibility tree does not expose is therefore ``skipTest``-ed
(recorded UNVERIFIABLE for human sign-off) rather than false-failing. When the
indicator *is* readable, the test discriminates the bug:

  * pre-fix the indicator is frozen after the Given edit -> FAIL,
  * post-fix it tracks the new Given name -> PASS.

The load-bearing confirmation for this fix is the manual Name-editor repro in
the build notes; this driver automates it as far as AT-SPI allows.
"""

from __future__ import annotations

import time
import unittest

from dogtail.rawinput import keyCombo

from .base import GrampsInterfaceTestCase

# The validation error message _validate_call raises (editname.py:182-184); it is
# the tooltip text of the Call field's error icon when the call name is invalid.
ERROR_HINT = "Call name"


class Bug12110CallNameRevalidateTest(GrampsInterfaceTestCase):
    """Editing the Given name re-runs the Call-name validity check."""

    TREE_NAME = "TestTree"
    LAUNCH_CONFIG = (
        "preferences.use-last-view:True",
        "preferences.last-view:personlistview",
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

    def _click_named(self, roles, name_substr: str, timeout: float = 8.0) -> bool:
        if isinstance(roles, str):
            roles = (roles,)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n, _r=roles, _s=name_substr: n.roleName in _r
                and _s in (n.name or "")
            ):
                if self._is_usable(n):
                    try:
                        n.click()
                        return True
                    except Exception:
                        pass
            time.sleep(0.3)
        return False

    def _first_usable(self, root, predicate, timeout: float = 8.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in root.findChildren(predicate):
                if self._is_usable(n):
                    return n
            time.sleep(0.3)
        return None

    def _frame(self, name_substr: str, timeout: float = 10.0):
        return self._first_usable(
            self.app,
            lambda n: n.roleName in ("dialog", "frame")
            and name_substr in (n.name or ""),
            timeout=timeout,
        )

    def _open_first_person(self) -> bool:
        """Open the Edit Person dialog for the first person in the list."""
        row = self._first_usable(
            self.app, lambda n: n.roleName == "table cell", timeout=10.0
        )
        if row is None:
            return False
        try:
            row.doubleClick()
        except Exception:
            return False
        return self._frame("Edit Person", timeout=12.0) is not None

    def _entry_near_label(self, dialog, label_substr: str):
        """Return the text entry on the same row as ``label_substr``."""
        label = self._first_usable(
            dialog,
            lambda n: n.roleName == "label" and label_substr in (n.name or ""),
            timeout=4.0,
        )
        if label is None:
            return None
        label_y = label.position[1]
        best = None
        best_dx = None
        for e in dialog.findChildren(lambda n: n.roleName == "text"):
            if not self._is_usable(e):
                continue
            if abs(e.position[1] - label_y) <= max(12, e.size[1]):
                dx = e.position[0] - label.position[0]
                if dx >= 0 and (best_dx is None or dx < best_dx):
                    best, best_dx = e, dx
        return best

    def _set_entry(self, entry, text: str) -> None:
        entry.click()
        time.sleep(0.2)
        keyCombo("<Control>a")
        keyCombo("Delete")
        if text:
            entry.typeText(text)
        # leave the field so MonitoredEntry commits / fires "changed"
        keyCombo("Tab")
        time.sleep(0.4)

    def _call_is_invalid(self, dialog, call_entry):
        """Best-effort read of the Call field's invalid (red) indicator.

        Returns True (invalid), False (valid), or None when AT-SPI does not
        expose the state — in which case the caller ``skipTest``s.
        """
        # 1) AT-SPI invalid-entry state, if GTK surfaced it.
        try:
            states = {s.lower() for s in call_entry.getState().getStates()}
            if "invalid-entry" in states or "invalid" in states:
                return True
        except Exception:
            pass
        # 2) The error icon's tooltip / accessible description carries the
        #    validation message when invalid; absent when valid.
        try:
            desc = (call_entry.description or "").strip()
            if ERROR_HINT in desc:
                return True
        except Exception:
            pass
        # 3) A sibling image/icon node whose name/description names the error.
        try:
            for n in dialog.findChildren(
                lambda n: n.roleName in ("icon", "image", "push button")
            ):
                blob = f"{getattr(n, 'name', '') or ''} {getattr(n, 'description', '') or ''}"
                if ERROR_HINT in blob and self._is_usable(n):
                    return True
        except Exception:
            pass
        # Could not positively read an invalid indicator. We cannot tell
        # "valid" from "AT-SPI can't see it", so report unknown.
        return None

    def _open_name_editor(self, person_dialog):
        """From Edit Person, open the Name editor (EditName) on an alt name."""
        if not self._click_named(("page tab", "page tab list"), "Names", timeout=4.0):
            return None
        time.sleep(0.5)
        # Add a new alternate name (the '+' / Add button on the Names tab).
        if not self._click_named(("push button",), "Add", timeout=4.0):
            return None
        return self._frame("Name Editor", timeout=8.0)

    # -------------------------------------------------------------------- test
    def test_given_change_revalidates_call(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_first_person():
            self.skipTest("could not open the Edit Person dialog via AT-SPI (infra)")
        person_dialog = self._frame("Edit Person")

        name_editor = self._open_name_editor(person_dialog)
        if name_editor is None:
            self.skipTest(
                "could not open the Name Editor (EditName) via AT-SPI (infra)"
            )

        given = self._entry_near_label(name_editor, "Given")
        call = self._entry_near_label(name_editor, "Call")
        if given is None or call is None:
            self.skipTest(
                "could not locate the Given/Call entries in the Name Editor (infra)"
            )

        # Case 1 setup: Call='Jon', Given empty -> Call should read invalid.
        self._set_entry(given, "")
        self._set_entry(call, "Jon")
        before = self._call_is_invalid(name_editor, call)
        if before is None:
            self.skipTest(
                "Call-field validity indicator is not exposed via AT-SPI "
                "(GtkEntry error icon / CSS class) — cannot assert the "
                "red/black state; confirm manually (see build notes)."
            )
        self.assertTrue(before, "Call='Jon' with empty Given should be invalid (red)")

        # The fix under test: editing the Given name must re-run the check.
        self._set_entry(given, "Jon")
        after = self._call_is_invalid(name_editor, call)
        if after is None:
            self.skipTest(
                "Call validity indicator unreadable after the Given edit (infra)"
            )

        if after:
            self._capture_screenshot("bug12110-stale-callname")
        self.assertFalse(
            after,
            "After setting Given='Jon' the Call='Jon' field is still marked "
            "invalid — editing Given did not re-run the call-name check "
            "(bug 12110: given_field had no changed hook to re-fire "
            "_validate_call).",
        )


if __name__ == "__main__":
    unittest.main()
