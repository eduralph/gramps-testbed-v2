"""Regression for Mantis #11786 ("renaming a tag leaves the old name in an
open list view").

Reported against Gramps 5.1.2 / People View: after Tags -> Organize Tags ->
Rename, the People View's Tags column kept showing the *old* tag name; only a
restart refreshed it.

Root cause (read on maintenance/gramps61)
------------------------------------------
The tag's display name is cached in the treemodel keyed by the **tag** handle:
``peoplemodel.PeopleBaseModel.get_tag_name`` ->
``basemodel.BaseModel.get_cached_value(tag_handle, "TAG_NAME")``
(gramps/gui/views/treemodels/peoplemodel.py:511-520, cache at basemodel.py:46).
On rename the DB emits ``tag-update`` -> the view's ``tag_updated``
(gramps/plugins/lib/libpersonview.py:535-550) resolves the tagged *person*
backlinks and calls ``row_update`` (gramps/gui/views/listview.py:927), clearing
the cache for the *person* handles only.  The ``(tag_handle, "TAG_NAME")`` entry
is never dropped, so the re-render reads the stale old name.

Fix: ``tag_updated`` drops the renamed tag's cached entry
(``self.model.clear_cache(tag_handle)``) before re-rendering the rows.

Fixture
-------
TestTree = example.gramps.  Its home person Lewis Anderson Garner
(handle ``_GNUJQCL9MD64AM56OH``, id I0044) carries the tag ``ToDo``
(tag handle ``_bb80c2b235b0a1b3f49``); the only other tag is ``complete``.
The word "ToDo" appears in the People View *only* in the Tags column (the
similarly-named "Number of To Do Notes" column renders an integer), so a
table-cell text match for ``ToDo`` / the new name is unambiguous.

The Tags column is not in the People List View's default visible columns
(``columns.visible`` defaults to Name/ID/Gender/Birth-Date/Death-Date,
gramps/plugins/lib/libpersonview.py:117).  ``setUpClass`` therefore seeds the
view's per-view config ini (``People_personlistview.ini`` under
``gramps.gen.const.VERSION_DIR``) to make COL_TAGS (=13) visible before launch.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory (per-fix interface-level C4 is
staged, not a clean gate); the gated red->green proof is the headless companion
``gramps/plugins/lib/test/libpersonview_test.py``.  This GUI test is the
load-bearing characterisation the human weighs at sign-off.  It uses graceful
skips when test infra cannot drive a widget, so only a delivered-but-stale
Tags column reports the #11786 symptom.
"""

from __future__ import annotations

import time
import unittest

from .base import GrampsInterfaceTestCase

OLD_TAG_NAME = "ToDo"
NEW_TAG_NAME = "ZZRenamed11786"
HOME_PERSON_SURNAME = "Garner"


def _seed_tags_column_visible() -> None:
    """Write the People List View config so the Tags column (COL_TAGS=13) is
    visible. Mirrors libpersonview.CONFIGSETTINGS' default columns.visible plus
    COL_TAGS. Runs before gramps launches so the view paints the column."""
    import os

    from gramps.gen.const import VERSION_DIR

    os.makedirs(VERSION_DIR, exist_ok=True)
    ini = os.path.join(VERSION_DIR, "People_personlistview.ini")
    # ConfigManager reads RawConfigParser ini whose values are Python literals
    # (safe_eval). COL_NAME=0, COL_ID=1, COL_GEN=2, COL_BDAT=3, COL_DDAT=5,
    # COL_TAGS=13 (libpersonview.py:82-95).
    with open(ini, "w", encoding="utf8") as fh:
        fh.write("[columns]\n")
        fh.write("visible=[0, 1, 2, 3, 5, 13]\n")


class Bug11786TagRenameListViewTest(GrampsInterfaceTestCase):
    """Renaming a tag refreshes the People View's Tags column without restart."""

    TREE_NAME = "TestTree"
    # Give the list view room so its rows/columns actually paint under Xvfb
    # (no WM to honour fullscreen()); see bug 8594 test for the rationale.
    LAUNCH_CONFIG = (
        "interface.main-window-width:1800",
        "interface.main-window-height:1000",
    )

    @classmethod
    def setUpClass(cls) -> None:
        _seed_tags_column_visible()
        super().setUpClass()

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

    def _tree_table(self):
        for n in self.app.findChildren(lambda n: n.roleName == "tree table"):
            if self._is_usable(n):
                return n
        return None

    def _tag_cell_texts(self) -> set[str]:
        """Text of every table cell in the People view's tree table."""
        table = self._tree_table()
        if table is None:
            return set()
        texts = set()
        for c in table.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if c.name:
                    texts.add(c.name)
            except Exception:
                pass
        return texts

    def _wait_for_cell(self, text: str, present: bool, timeout: float = 8.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            has = text in self._tag_cell_texts()
            if has == present:
                return True
            time.sleep(0.3)
        return text in self._tag_cell_texts() if present else (
            text not in self._tag_cell_texts()
        )

    def _click_named(self, role: str, name: str, timeout: float = 8.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n, _r=role, _n=name: n.roleName == _r
                and _n in (n.name or "")
            ):
                if self._is_usable(n):
                    try:
                        n.click()
                        return True
                    except Exception:
                        pass
            time.sleep(0.3)
        return False

    def _open_organize_tags(self) -> bool:
        """Tags toolbar button -> 'Organize Tags...'. The Tags control is a
        Gtk.MenuToolButton; its arrow opens a menu containing the per-tag
        toggles and the 'Organize Tags...' item."""
        # Open the Tags menu (button or menu labelled "Tags").
        if not (
            self._click_named("push button", "Tags")
            or self._click_named("toggle button", "Tags")
            or self._click_named("menu", "Tags")
        ):
            return False
        time.sleep(0.5)
        return self._click_named("menu item", "Organize Tags")

    def _rename_in_organize_dialog(self) -> bool:
        """In the Organize Tags dialog: select the ToDo row, Rename, enter the
        new name, OK, then close the dialog."""
        # Select the ToDo row inside the Organize Tags dialog's table.
        if not self._click_named("table cell", OLD_TAG_NAME):
            return False
        if not self._click_named("push button", "Rename"):
            return False
        time.sleep(0.5)
        # The rename prompt is a text-entry dialog; clear and type the new name.
        from dogtail.rawinput import keyCombo, typeText

        for t in self.app.findChildren(lambda n: n.roleName == "text"):
            if self._is_usable(t):
                try:
                    t.click()
                    keyCombo("<Control>a")
                    typeText(NEW_TAG_NAME)
                    break
                except Exception:
                    pass
        else:
            return False
        if not self._click_named("push button", "OK"):
            return False
        time.sleep(0.5)
        # Close the Organize Tags dialog.
        self._click_named("push button", "Close")
        return True

    # -------------------------------------------------------------------- test
    def test_tag_rename_refreshes_tags_column(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        # Precondition: the Tags column shows the old tag name for the home
        # person. If we cannot even see it, the infra (column visibility /
        # rendering) is the problem, not the bug -- skip rather than false-fail.
        if not self._wait_for_cell(OLD_TAG_NAME, present=True, timeout=15.0):
            self.skipTest(
                f"Tags column with {OLD_TAG_NAME!r} not visible in People View "
                "-- cannot exercise the rename repro"
            )

        if not self._open_organize_tags():
            self.skipTest("could not open Tags -> Organize Tags (infra)")
        if not self._rename_in_organize_dialog():
            self.skipTest("could not drive the Organize Tags rename flow (infra)")

        # Post-fix: the renamed tag's new name appears in the Tags column with
        # no restart. Pre-fix the cell still reads the stale old name.
        appeared = self._wait_for_cell(NEW_TAG_NAME, present=True, timeout=10.0)
        stale_gone = self._wait_for_cell(OLD_TAG_NAME, present=False, timeout=2.0)
        if not appeared:
            self._capture_screenshot("bug11786-stale-tag-name")
        self.assertTrue(
            appeared and stale_gone,
            f"Tags column still shows {OLD_TAG_NAME!r} after rename to "
            f"{NEW_TAG_NAME!r} (bug 11786: stale (tag_handle, 'TAG_NAME') cache "
            "not invalidated on tag-update)",
        )


if __name__ == "__main__":
    unittest.main()
