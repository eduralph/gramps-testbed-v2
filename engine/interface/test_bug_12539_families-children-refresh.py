"""Regression for Mantis #12539 ("Families view Children tab does not refresh
after a filter/Find changes the current family").

Reported against the Families view: with the bottombar "Children" tab shown,
selecting a family fills the tab with that family's children. After typing a
filter in the sidebar Family Filter (e.g. Father = "Simpson") and pressing Find,
the family list narrows and a different family becomes current -- but the
Children tab keeps showing the *previously* selected family's children (or
nothing) until the user manually re-clicks a row (notes.json: snoiraud
~0065528, prculley discourse note ~0065526).

Root cause (read on maintenance/gramps61)
------------------------------------------
The Children bottombar gramplet (``FamilyChildren``,
gramps/plugins/gramplet/children.py:200) rebuilds only on the Family
``active-changed`` signal (``connect_signal("Family", ...)`` at children.py:229).
A filter/Find runs ``FamilyView.build_tree`` (via the Family Filter gramplet,
gramps/plugins/gramplet/filter.py:76-77, or the quick SearchBar,
gramps/gui/views/listview.py:404-405), which rebuilds the model and calls
``goto_active``. When the previously active family is filtered OUT,
``ListView.goto_handle`` cannot select it and just unselects
(gramps/gui/views/listview.py:485-487); the active family handle never changes,
so ``active-changed`` never fires and the Children tab is left stale.

Fix
---
``FamilyView.build_tree`` (gramps/plugins/view/familyview.py) now resolves the
post-rebuild selection through the gi-free helper
``gramps.plugins.view.familyview_selection.resolve_active_after_filter``: if the
active family was filtered out, it re-points the active family at the first
visible row via ``change_active``, which fires ``active-changed`` so the
Children gramplet rebuilds for the now-current, visible family. The gated
red->green proof of that decision is the headless companion unit
``gramps/plugins/view/test/familyview_selection_test.py``.

Repro driven here
-----------------
Open the Families view and show the Children tab. Scan family rows to find two
families A and B with *distinct, non-empty* children. Select A (the Children tab
shows A's children). Drive the sidebar Family Filter so that A is filtered out
and B remains, press Find, and confirm -- with no manual re-click -- that the
Children tab now shows B's children rather than A's. Pre-fix the tab still shows
A's children.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory; this GUI characterisation is
what the human weighs at sign-off. It uses graceful skips wherever the test
infra cannot drive a widget or the fixture lacks two suitably distinct families,
so only a genuinely stale Children tab reports the #12539 symptom.
"""

from __future__ import annotations

import time
import unittest

from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase


class Bug12539FamiliesChildrenRefreshTest(GrampsInterfaceTestCase):
    """The Families Children tab tracks the active family after a filter/Find."""

    TREE_NAME = "TestTree"
    # Give the view room so the family list, the sidebar filter and the
    # bottombar gramplet all paint under Xvfb (no WM honours fullscreen) --
    # same rationale as the bug 11991 / 13716 interface tests.
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

    def _table_with_header(self, header_name: str):
        """Return the first usable (tree) table that carries the given column
        header -- "Father" identifies the family list, "Child" the Children
        gramplet's tree."""
        for tbl in self.app.findChildren(
            lambda n: n.roleName in ("tree table", "table")
        ):
            try:
                headers = [
                    h.name
                    for h in tbl.findChildren(
                        lambda n: n.roleName == "table column header"
                    )
                ]
            except Exception:
                continue
            if header_name in headers and self._is_usable(tbl):
                return tbl
        return None

    def _children_names(self) -> set[str]:
        """The child names currently shown in the Children bottombar gramplet.

        The ``FamilyChildren`` gramplet's tree has a column titled "Child"
        (gramps/plugins/gramplet/children.py:218); the main family list has no
        such column, so the header uniquely identifies the gramplet's table.
        """
        tbl = self._table_with_header("Child")
        if tbl is None:
            return set()
        names: set[str] = set()
        for cell in tbl.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if cell.name and cell.name.strip():
                    names.add(cell.name.strip())
            except Exception:
                pass
        return names

    def _father_cells(self):
        """The clickable father-name cells of the family list, in order."""
        tbl = self._table_with_header("Father")
        if tbl is None:
            return []
        cells = []
        for cell in tbl.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if cell.name and cell.name.strip() and self._is_usable(cell):
                    cells.append(cell)
            except Exception:
                pass
        return cells

    def _select_cell(self, cell) -> bool:
        try:
            cell.click()
        except Exception:
            return False
        time.sleep(0.4)
        return True

    def _open_families_view(self) -> bool:
        if not self._click_named("toggle button", "Families"):
            return False
        time.sleep(0.6)
        return self._table_with_header("Father") is not None

    def _show_children_tab(self) -> bool:
        return (
            self._click_named("page tab", "Family Children")
            or self._click_named("page tab", "Children")
        )

    def _apply_father_filter(self, token: str) -> bool:
        """Type ``token`` into the sidebar Family Filter's Father entry and press
        Find. Returns False (caller skips) if the filter widgets aren't found."""
        # The sidebar Family Filter lays out a "Father" label next to a text
        # entry. Find a usable text entry adjacent to a "Father" label by
        # scanning labels and matching the nearest entry on the same row.
        father_entry = None
        labels = self.app.findChildren(
            lambda n: n.roleName == "label" and (n.name or "").strip() == "Father"
        )
        for lab in labels:
            if not self._is_usable(lab):
                continue
            try:
                ly = lab.position[1]
            except Exception:
                continue
            for t in self.app.findChildren(lambda n: n.roleName == "text"):
                if not self._is_usable(t):
                    continue
                try:
                    if abs(t.position[1] - ly) <= 6:
                        father_entry = t
                        break
                except Exception:
                    pass
            if father_entry is not None:
                break
        if father_entry is None:
            return False
        try:
            father_entry.click()
            keyCombo("<Control>a")
            typeText(token)
        except Exception:
            return False
        # Press the sidebar filter's Find/Apply button.
        return self._click_named("push button", "Find") or self._click_named(
            "push button", "Apply"
        )

    # -------------------------------------------------------------------- test
    def test_children_tab_follows_filter_selection(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_families_view():
            self.skipTest("Families view / family list did not render (infra)")
        if not self._show_children_tab():
            self.skipTest("Children gramplet tab not reachable (infra)")

        # Discover two families A and B with distinct, non-empty children, and
        # remember a father-name token unique to B so we can filter A out.
        cells = self._father_cells()
        if len(cells) < 2:
            self.skipTest("fewer than two family rows to exercise the repro (infra)")

        scanned = []  # (father_text, frozenset(children))
        for cell in cells[:12]:
            father_text = (cell.name or "").strip()
            if not self._select_cell(cell):
                continue
            kids = frozenset(self._children_names())
            if kids:
                scanned.append((father_text, kids))

        family_a = family_b = None
        for i in range(len(scanned)):
            for j in range(len(scanned)):
                fa, ka = scanned[i]
                fb, kb = scanned[j]
                if ka == kb or fa == fb:
                    continue
                token = fb.split(",")[0].split()[0] if fb else ""
                # token must identify B but not appear in A's father text
                if token and token not in fa:
                    family_a, family_b = (fa, ka), (fb, kb, token)
                    break
            if family_a is not None:
                break
        if family_a is None:
            self.skipTest(
                "fixture lacks two families with distinct children and a "
                "father token that filters one out (infra)"
            )

        fa_text, kids_a = family_a
        fb_text, kids_b, token = family_b

        # Select A; the Children tab must show A's children.
        a_cell = next((c for c in self._father_cells() if (c.name or "").strip() == fa_text), None)
        if a_cell is None or not self._select_cell(a_cell):
            self.skipTest(f"could not re-select family A {fa_text!r} (infra)")
        if frozenset(self._children_names()) != kids_a:
            self.skipTest("Children tab for family A not stable across reselect (infra)")

        # Filter on B's father token so A is removed and B becomes current.
        if not self._apply_father_filter(token):
            self.skipTest("could not drive the sidebar Father filter (infra)")
        time.sleep(0.8)

        after = frozenset(self._children_names())
        if after == kids_a:
            self._capture_screenshot("bug12539-stale-children-tab")
        self.assertNotEqual(
            after,
            kids_a,
            f"Children tab still shows family A {fa_text!r}'s children "
            f"{sorted(kids_a)} after filtering Father={token!r} removed A and "
            f"made {fb_text!r} current -- the tab did not refresh (bug 12539).",
        )
        self.assertEqual(
            after,
            kids_b,
            f"Children tab should show family B {fb_text!r}'s children "
            f"{sorted(kids_b)} after the filter made it current, but shows "
            f"{sorted(after)}.",
        )


if __name__ == "__main__":
    unittest.main()
