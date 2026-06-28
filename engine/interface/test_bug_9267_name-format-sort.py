"""Regression for Mantis #9267 ("changing the Display Name format does not
rebuild a list view's sort order").

Reported against the People (flat) list view: after Edit -> Preferences ->
Display -> "Name format" is changed, every row re-renders with the new format
but the *row order* stays computed from the previous format -- the list is only
re-sorted when the database is reopened.

Root cause (read on maintenance/gramps61)
------------------------------------------
``FlatBaseModel._rebuild_search`` / ``_rebuild_filter``
(gramps/gui/views/treemodels/flatbasemodel.py) reuse the cached
``(sortkey, handle)`` map (``node_map.full_srtkey_hndl_map``) whenever it is
populated, recomputing ``sort_keys()`` only when the cache is empty.  That cache
is correct while the sort *function* is fixed (a search/filter change only
restricts which handles are shown, never their order), but it is stale when the
sort key itself changes.  The People view connects ``nameformat-changed`` to a
plain rebuild (gramps/plugins/lib/libpersonview.py), so the format change redrew
the rows but left the cached order in place.

Fix
---
``FlatBaseModel.rebuild_sort()`` marks the sort dirty so the next rebuild
recomputes ``sort_keys()``; ``BasePersonView`` calls it before rebuilding on a
name/place-format change.  The gated red->green proof is the headless companion
``gramps/gui/views/treemodels/test/flatbasemodel_sort_test.py``.

How this AT-SPI repro discriminates the bug
-------------------------------------------
The People list view's rows ARE exposed via AT-SPI (unlike Cairo charts), and
every row carries a stable Gramps ID cell (``I0001`` ...).  The test launches on
the flat People list with the "Surname, Given" name format (rows sorted by
surname), records the top-to-bottom sequence of visible IDs, changes the
"Name format" preference to one that sorts differently (e.g. "Given"), and reads
the ID sequence again.  Because the IDs are format-independent, a re-sort shows
up as a *changed* ID sequence:

  * pre-fix the order is frozen -> the ID sequence is unchanged -> FAIL,
  * post-fix the rows re-sort -> the ID sequence changes -> PASS.

Driving Edit -> Preferences -> Display -> the "Name format" combo over AT-SPI is
fragile; every step that the accessibility tree does not expose ``skipTest``s
(recorded as UNVERIFIABLE for human sign-off) rather than false-failing.  The
load-bearing proof is the headless unit test named above.
"""

from __future__ import annotations

import re
import time
import unittest

from .base import GrampsInterfaceTestCase

ID_RE = re.compile(r"^I\d+$")


class Bug9267NameFormatSortTest(GrampsInterfaceTestCase):
    """Changing the Name format re-sorts the People list without reopening."""

    TREE_NAME = "TestTree"
    # use-last-view + last-view land startup directly on the FLAT People list
    # view (personlistview), not the default grouped tree (personview).
    # name-format:1 == "Surname, Given ..." (Name.LNFN) -> initial surname sort.
    LAUNCH_CONFIG = (
        "preferences.use-last-view:True",
        "preferences.last-view:personlistview",
        "preferences.name-format:1",
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

    def _id_sequence(self) -> list[str]:
        """Top-to-bottom sequence of the visible Gramps-ID cells (``I0001`` ...).

        IDs are independent of the name format, so the sequence is a faithful
        readout of the *row order* across a format change.
        """
        table = self._tree_table()
        if table is None:
            return []
        rows: list[tuple[int, str]] = []
        for c in table.findChildren(lambda n: n.roleName == "table cell"):
            try:
                name = c.name or ""
                if not ID_RE.match(name) or not self._is_usable(c):
                    continue
                rows.append((c.position[1], name))
            except Exception:
                pass
        rows.sort(key=lambda r: r[0])
        # De-dup any accidental double-read while preserving order.
        seen: set[str] = set()
        seq: list[str] = []
        for _y, name in rows:
            if name not in seen:
                seen.add(name)
                seq.append(name)
        return seq

    def _wait_for_rows(self, timeout: float = 15.0) -> list[str]:
        deadline = time.monotonic() + timeout
        seq: list[str] = []
        while time.monotonic() < deadline:
            seq = self._id_sequence()
            if len(seq) >= 5:
                return seq
            time.sleep(0.3)
        return seq

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

    def _open_preferences(self) -> bool:
        """Open Edit -> Preferences. Gramps exposes the menu either as a classic
        menu bar ("Edit" -> "Preferences") or behind the header-bar main-menu
        button; try both, then click any visible "Preferences" item."""
        # If a Preferences item is already reachable, use it.
        if self._click_named(("menu item", "push button"), "Preferences", timeout=1.0):
            return True
        # Classic menu bar: open Edit, then Preferences.
        if self._click_named("menu", "Edit", timeout=2.0):
            time.sleep(0.4)
            if self._click_named("menu item", "Preferences", timeout=3.0):
                return True
        # Header-bar hamburger / main-menu button.
        for opener in ("Main Menu", "Menu", "Gramps"):
            if self._click_named(("push button", "toggle button"), opener, timeout=1.5):
                time.sleep(0.4)
                if self._click_named("menu item", "Preferences", timeout=3.0):
                    return True
        return False

    def _preferences_dialog(self):
        for n in self.app.findChildren(
            lambda n: n.roleName in ("dialog", "frame")
            and "Preferences" in (n.name or "")
        ):
            if self._is_usable(n):
                return n
        return None

    def _change_name_format(self, dialog) -> bool:
        """In the open Preferences dialog: go to Display, then pick a different
        entry in the "Name format" combo box."""
        # Select the Display category (left-hand list).
        self._click_named(
            ("table cell", "list item", "page tab"), "Display", timeout=4.0
        )
        time.sleep(0.5)

        # Locate the "Name format:" label and the combo box on its row.
        label = None
        for n in dialog.findChildren(
            lambda n: n.roleName == "label" and "Name format" in (n.name or "")
        ):
            if self._is_usable(n):
                label = n
                break
        if label is None:
            return False
        label_y = label.position[1]

        combo = None
        for c in dialog.findChildren(lambda n: n.roleName == "combo box"):
            if not self._is_usable(c):
                continue
            if abs(c.position[1] - label_y) <= max(10, c.size[1]):
                combo = c
                break
        if combo is None:
            return False

        current = combo.name or ""
        try:
            combo.click()
        except Exception:
            return False
        time.sleep(0.5)
        # The popup lists the available formats as menu items / list items.
        # Prefer an explicit "Given" format; otherwise any entry != current.
        for prefer in ("Given", None):
            for item in self.app.findChildren(
                lambda n: n.roleName in ("menu item", "list item")
            ):
                try:
                    text = item.name or ""
                except Exception:
                    continue
                if not self._is_usable(item) or not text:
                    continue
                if prefer is not None and prefer not in text:
                    continue
                if text == current:
                    continue
                try:
                    item.click()
                    return True
                except Exception:
                    continue
        return False

    def _close_preferences(self, dialog) -> None:
        from dogtail.rawinput import keyCombo

        if not self._click_named("push button", "Close", timeout=3.0):
            try:
                keyCombo("Escape")
            except Exception:
                pass

    # -------------------------------------------------------------------- test
    def test_name_format_change_resorts_people_list(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        before = self._wait_for_rows()
        if len(before) < 5:
            self.skipTest(
                "Could not read at least 5 People-list ID cells via AT-SPI "
                "-- cannot establish the pre-change order (infra / not the "
                "flat People list view)."
            )

        if not self._open_preferences():
            self.skipTest("could not open Edit -> Preferences (infra)")
        dialog = self._preferences_dialog()
        if dialog is None:
            self.skipTest("Preferences dialog not visible via AT-SPI (infra)")
        if not self._change_name_format(dialog):
            self._close_preferences(dialog)
            self.skipTest("could not drive Display -> 'Name format' combo (infra)")
        self._close_preferences(dialog)
        time.sleep(1.0)

        # Re-read the order. Post-fix the rows re-sort to the new format, so the
        # ID sequence changes; pre-fix the order is frozen and it does not.
        deadline = time.monotonic() + 10.0
        after = self._id_sequence()
        while time.monotonic() < deadline and after == before:
            time.sleep(0.3)
            after = self._id_sequence()

        if not after:
            self.skipTest("People list rows not readable after the change (infra)")

        if after == before:
            self._capture_screenshot("bug9267-frozen-sort")
        self.assertNotEqual(
            before,
            after,
            "People (flat) list row order is unchanged after switching the "
            "Name format -- the sort was not rebuilt (bug 9267: stale "
            "node_map.full_srtkey_hndl_map cache reused on nameformat-changed).",
        )


if __name__ == "__main__":
    unittest.main()
