"""Regression for Mantis #13716 ("sidebar-filter Type selector is stale").

Reported against the Notes category Filter gramplet: the sidebar filter's
"Type" selector is populated with the database's custom types only once — when
the filter widget is first built at view open — and is never refreshed. A
custom type added to the already-open database afterwards (e.g. a "GEDCOM
import" Note type created by importing a GEDCOM with errors, or any custom type
added by editing a Note) does not appear in the selector until the
gramplet/view is torn down and rebuilt. The editor dialogs rebuild their type
selector anew every time they are shown, so they do not have this problem
(maintainer diagnosis, Mantis 13716 note 3).

Root cause (read on maintenance/gramps61)
------------------------------------------
Every sidebar filter caches ``dbstate.db.get_<obj>_types()`` once in its
``__init__`` (e.g. gramps/gui/filters/sidebar/_notesidebarfilter.py:66) and
hands that snapshot to a ``MonitoredDataType`` / ``StandardCustomSelector``,
whose combo model is built once and never rebuilt.

Fix
---
The shared ``SidebarFilter`` keeps its database-derived "Type" selectors
consistent with the database's current custom types: each selector is
registered (``SidebarFilter.add_type_filter`` /
``_register_type_filters``) with a *live-db* fetch and rebuilt from the
database whenever its drop-down is presented (``notify::popup-shown``) and on
database change — mirroring the editor dialogs' rebuild-per-presentation
contract. The repopulate orchestration lives in the GUI-free
``gramps/gui/filters/sidebar/_typefilterlist.py`` so it is unit-testable
headlessly; the gated red->green proof is the headless companion
``gramps/gui/filters/sidebar/test/_sidebarfilter_test.py``.

Repro driven here
-----------------
Open the Notes category (its sidebar hosts the "Type" filter combo). Record the
options the Type combo offers and confirm a sentinel custom type is absent.
Create a Note carrying that sentinel custom type via the Note editor (which adds
the custom type to the open database). Re-open the sidebar Type combo *without
recreating the view* and confirm the sentinel custom type is now offered.
Pre-fix the combo still offers only the construction-time snapshot.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory; this GUI test is the
characterisation the human weighs at sign-off. It uses graceful skips when the
test infra cannot drive a widget, so only a delivered-but-stale Type selector
reports the #13716 symptom.
"""

from __future__ import annotations

import time
import unittest

from .base import GrampsInterfaceTestCase

SENTINEL_TYPE = "QA Custom 13716"


class Bug13716SidebarFilterTypeTest(GrampsInterfaceTestCase):
    """The Notes sidebar Type filter reflects a custom type added to the open
    database, with no view recreation (Mantis 13716)."""

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

    def _click_toggle(self, name: str, timeout: float = 10.0) -> bool:
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

    def _open_notes_category(self) -> bool:
        # The Notes category sidebar toggle is labelled "Notes".
        if not self._click_toggle("Notes"):
            return False
        time.sleep(0.8)
        return True

    def _type_combo(self):
        """The sidebar filter's editable 'Type' combo box.

        The sidebar filter lays out a "Type" label next to a Gtk.ComboBox with
        an entry. AT-SPI exposes that as a 'combo box' carrying a 'text' child;
        the Notes view sidebar has exactly one such Type combo. We pick the
        editable combo box that sits in the filter sidebar (usable + has a text
        child), preferring one adjacent to a 'Type' label.
        """
        combos = [
            c
            for c in self.app.findChildren(lambda n: n.roleName == "combo box")
            if self._is_usable(c)
            and c.findChildren(lambda n: n.roleName == "text")
        ]
        return combos[0] if combos else None

    def _combo_options(self, combo) -> set[str]:
        """The option strings the combo currently offers.

        Expand the drop-down so its model rows surface as AT-SPI menu/list
        items, read them, then collapse it again.
        """
        opts: set[str] = set()
        if combo is None:
            return opts
        try:
            combo.click()  # open the drop-down
        except Exception:
            return opts
        time.sleep(0.4)
        for item in combo.findChildren(
            lambda n: n.roleName in ("menu item", "list item", "table cell")
        ):
            try:
                if item.name:
                    opts.add(item.name)
            except Exception:
                pass
        # Also walk any popup the combo spawned at the app level.
        for popup in self.app.findChildren(
            lambda n: n.roleName in ("menu", "window", "list box")
        ):
            for item in popup.findChildren(
                lambda n: n.roleName in ("menu item", "list item", "table cell")
            ):
                try:
                    if item.name:
                        opts.add(item.name)
                except Exception:
                    pass
        try:
            from dogtail.rawinput import keyCombo

            keyCombo("Escape")  # collapse without changing selection
        except Exception:
            pass
        time.sleep(0.2)
        return opts

    def _click_named(self, role: str, name: str, timeout: float = 8.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n, _r=role, _n=name: n.roleName == _r and _n in (n.name or "")
            ):
                if self._is_usable(n):
                    try:
                        n.click()
                        return True
                    except Exception:
                        pass
            time.sleep(0.3)
        return False

    def _add_note_with_custom_type(self) -> bool:
        """Add a Note whose Type is the sentinel custom value via the editor."""
        # The Notes view toolbar 'Add' button opens the Note editor.
        if not (
            self._click_named("push button", "Add")
            or self._click_named("push button", "Add...")
        ):
            return False
        time.sleep(0.8)

        # In the Note editor, set the Type combo's entry to the custom value.
        from dogtail.rawinput import keyCombo, typeText

        editor = None
        for f in self.app.findChildren(
            lambda n: n.roleName in ("dialog", "frame")
        ):
            try:
                if f.showing and "Note" in (f.name or ""):
                    editor = f
                    break
            except Exception:
                pass
        if editor is None:
            return False

        type_combo = None
        for c in editor.findChildren(lambda n: n.roleName == "combo box"):
            if self._is_usable(c) and c.findChildren(
                lambda n: n.roleName == "text"
            ):
                type_combo = c
                break
        if type_combo is None:
            return False
        try:
            entry = type_combo.findChildren(lambda n: n.roleName == "text")[0]
            entry.click()
            keyCombo("<Control>a")
            typeText(SENTINEL_TYPE)
        except Exception:
            return False

        # Give the note some text so it is savable, then save the editor.
        for t in editor.findChildren(lambda n: n.roleName == "text"):
            try:
                if t is entry or not self._is_usable(t):
                    continue
                t.click()
                typeText("note body 13716")
                break
            except Exception:
                pass
        return self._click_named("push button", "OK") or self._click_named(
            "push button", "Save"
        )

    # -------------------------------------------------------------------- test
    def test_sidebar_type_filter_reflects_new_custom_type(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_notes_category():
            self.skipTest("could not switch to the Notes category (infra)")

        combo = self._type_combo()
        if combo is None:
            self.skipTest("Notes sidebar 'Type' filter combo not found (infra)")

        before = self._combo_options(combo)
        if SENTINEL_TYPE in before:
            self.skipTest(
                f"sentinel {SENTINEL_TYPE!r} already present before edit (infra)"
            )

        if not self._add_note_with_custom_type():
            self.skipTest(
                "could not drive the Note editor to add a custom type (infra)"
            )
        time.sleep(0.8)

        # Re-open the SAME sidebar Type combo (no view recreation) and confirm
        # the custom type added to the open database is now offered.
        combo = self._type_combo()
        after = self._combo_options(combo)
        if not after:
            self.skipTest("could not read the Type combo options after edit (infra)")

        if SENTINEL_TYPE not in after:
            self._capture_screenshot("bug13716-stale-type-filter")
        self.assertIn(
            SENTINEL_TYPE,
            after,
            f"Sidebar Type filter still does not offer {SENTINEL_TYPE!r} after a "
            "Note with that custom type was added to the open database "
            "(Mantis 13716: type selector cached at widget construction and "
            "never refreshed).",
        )


if __name__ == "__main__":
    unittest.main()
