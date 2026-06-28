"""Regression for Mantis #13876 ("Citation Tree view: Delete does not delete a
citation").

Reported against the Citations view's **Citation Tree** view mode: selecting a
citation row (under its source group) and choosing Delete pops two confirmation
dialogs, but after confirming the citation is still present.

Root cause (read on maintenance/gramps61)
------------------------------------------
The Citation Tree view's delete path runs through the shared helper
``gramps.plugins.lib.libsourceview.LibSourceView.remove_object_from_handle``.
After cleaning up back-references its final line was unconditionally
``self.dbstate.db.remove_source(handle, trans)`` (libsourceview.py:102) — so for
a *citation* it asked the DB to remove a *source* with the citation's handle, a
no-op, and the citation survived.  Source deletion happened to work because the
hard-coded call matched the object type.

Fix: dispatch on the selected object's type —
``self.dbstate.db.method("remove_%s", obj_type)(handle, trans)`` — exactly as the
base ``ListView.remove_object_from_handle`` does (listview.py:712).

Fixture
-------
TestTree = example.gramps.  Source S00002 "World of the Wierd"
(handle ``_VUBKMQTA2XZG1V6QP8``) has two child citations: C00973 ("Page 11 2/3.")
and **C02324 ("Page pi")**.  The Citation Tree view shows the ID column by
default (citationtreeview.py:116), so the citation row's ID ``C02324`` is a
unambiguous table-cell text to target and to check for after deletion.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory (per-fix interface-level C4 is
staged, not a clean gate); the gated red->green proof is the headless companion
``gramps/plugins/lib/test/libsourceview_test.py`` which drives the production
``LibSourceView`` delete helper directly.  This GUI test is the load-bearing
characterisation the human weighs at sign-off; it uses graceful skips when the
test infra cannot drive a widget, so only a delivered-but-undeleted citation
reports the #13876 symptom.
"""

from __future__ import annotations

import time
import unittest

from .base import GrampsInterfaceTestCase

SOURCE_TITLE = "World of the Wierd"
CITATION_ID = "C02324"
CITATION_PAGE = "Page pi"


class Bug13876CitationTreeDeleteTest(GrampsInterfaceTestCase):
    """Deleting a citation row in the Citation Tree view removes the citation."""

    TREE_NAME = "TestTree"
    # Give the tree view room so its rows/columns actually paint under Xvfb
    # (no WM to honour fullscreen()); see the bug 11786 test for the rationale.
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

    def _tree_table(self):
        for n in self.app.findChildren(lambda n: n.roleName == "tree table"):
            if self._is_usable(n):
                return n
        return None

    def _cell_texts(self) -> set[str]:
        """Text of every visible table cell in the active tree table."""
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
            if (text in self._cell_texts()) == present:
                return True
            time.sleep(0.3)
        return (text in self._cell_texts()) == present

    def _find_cell(self, text: str):
        table = self._tree_table()
        if table is None:
            return None
        for c in table.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if (c.name or "") == text and self._is_usable(c):
                    return c
            except Exception:
                pass
        return None

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

    def _open_citation_tree_view(self) -> bool:
        """Select the Sources category, then its Citation Tree view mode."""
        # The category button is in the navigator sidebar; its view buttons
        # carry the view names. Names are localized, but the default English
        # build is what CI runs.
        self._click_named("radio button", "Sources") or self._click_named(
            "page tab", "Sources"
        ) or self._click_named("push button", "Sources")
        time.sleep(0.5)
        # Switch to the "Citation Tree" view mode.
        return (
            self._click_named("radio button", "Citation Tree")
            or self._click_named("toggle button", "Citation Tree")
            or self._click_named("push button", "Citation Tree")
        )

    def _expand_source(self) -> bool:
        """Expand the 'World of the Wierd' source node so its citations show."""
        cell = self._find_cell(SOURCE_TITLE)
        if cell is None:
            return False
        try:
            cell.doubleClick()
        except Exception:
            return False
        return self._wait_for_cell(CITATION_ID, present=True, timeout=6.0)

    def _confirm_delete_dialogs(self) -> None:
        """Confirm the (up to two) deletion confirmation dialogs."""
        deadline = time.monotonic() + 8.0
        confirms = 0
        while time.monotonic() < deadline and confirms < 3:
            clicked = False
            for modal in self.app.findChildren(
                lambda n: n.roleName in ("dialog", "alert")
            ):
                for btn in modal.findChildren(
                    lambda n: n.roleName == "push button"
                    and (n.name or "") in ("_Delete", "Delete", "Yes", "OK")
                    and getattr(n, "showing", False)
                ):
                    try:
                        btn.click()
                        clicked = True
                        confirms += 1
                        break
                    except Exception:
                        pass
                if clicked:
                    break
            time.sleep(0.5)

    # -------------------------------------------------------------------- test
    def test_delete_citation_row_removes_it(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_citation_tree_view():
            self.skipTest("could not switch to the Citation Tree view mode (infra)")

        if not self._expand_source():
            self.skipTest(
                f"could not expand {SOURCE_TITLE!r} to reveal its citation rows "
                "(infra)"
            )

        # Precondition: the citation row is present.
        if not self._wait_for_cell(CITATION_ID, present=True, timeout=8.0):
            self.skipTest(
                f"citation row {CITATION_ID!r} not visible in the Citation Tree "
                "view -- cannot exercise the delete repro"
            )

        # Select the citation row and delete it.
        cell = self._find_cell(CITATION_ID)
        if cell is None:
            self.skipTest(f"citation cell {CITATION_ID!r} vanished before select")
        try:
            cell.click()
        except Exception:
            self.skipTest("could not select the citation row (infra)")

        if not self._click_named("push button", "_Delete") and not self._click_named(
            "push button", "Delete"
        ):
            self.skipTest("could not press the Delete button (infra)")

        self._confirm_delete_dialogs()

        # Post-fix: the citation row is gone from the view (and the DB).
        gone = self._wait_for_cell(CITATION_ID, present=False, timeout=10.0)
        if not gone:
            self._capture_screenshot("bug13876-citation-not-deleted")
        self.assertTrue(
            gone,
            f"citation {CITATION_ID!r} ({CITATION_PAGE!r}) still present after "
            "Delete (bug 13876: LibSourceView.remove_object_from_handle called "
            "remove_source for a Citation, a no-op)",
        )


if __name__ == "__main__":
    unittest.main()
