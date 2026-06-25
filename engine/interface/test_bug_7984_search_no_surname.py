"""Mantis #7984 — Ctrl+F type-ahead must reach a person in a *collapsed*
"no surname" group without the user expanding the folder by hand.

Reported behaviour (Gramps 4.x, grouped People view)
----------------------------------------------------
On a tree where a person has no surname, that person lands in the
collapsed "[Missing Surname]" group of the grouped People view
(``gramps/gui/views/treemodels/peoplemodel.py:638`` ->
``preferences.no-surname-text``).  The reporter found that Ctrl+F
type-ahead would not descend into that collapsed group: the only
workaround was to expand the "no surname" folder manually first
(notes ~0037726 / ~0044606 on the Mantis thread).

Why this is POSSIBLY-FIXED on maintenance/gramps61
--------------------------------------------------
``InteractiveSearchBox.search_iter_slow`` now documents and implements
searching *both expanded and collapsed* rows and auto-expands to the hit
(``gramps/gui/widgets/interactivesearchbox.py:443-481`` — docstring line
447 "Both expanded and collapsed rows are searched."; the unconditional
descent into children at line 465-466 and the ``expand_to_path`` at line
459).  The match column is the sorted column (``set_search_column`` at
``gramps/gui/views/listview.py:827``), matched ``startswith`` by
``search_equal_func`` (``interactivesearchbox.py:483-488``).

What this repro drives
----------------------
A grouped People view over a tree whose persons ALL have no surname (so
there is exactly one, collapsed, "[Missing Surname]" group), with the
name format set to "Given" (``preferences.name-format:4`` ->
``Name.FN``, ``gramps/gen/lib/name.py:63``) so the searchable Name
column holds the given name directly.  This is precisely the reporter's
own working configuration ("changed name display to Given name only …
But the no-surname-list still needs to be opened manually", note
~0044606) — it isolates the *folder-reaching* defect from the separate,
out-of-scope limitation that a comma-prefixed "Surname, Given" format
can't be matched by a bare given name.

The test:
  1. navigates to the grouped People view,
  2. confirms the precondition — the "[Missing Surname]" group is present
     and COLLAPSED (the person cell "Onni" is not yet realised), then
  3. focuses the tree, presses Ctrl+F and types "Onni", and
  4. asserts the "Onni" cell becomes visible (the collapsed group was
     auto-expanded by ``expand_to_path``) — i.e. the search reached into
     the collapsed no-surname folder on its own.

VERIFY-FIRST.  This is a committed AT-SPI repro for a POSSIBLY-FIXED
bug; it ships with no patch (the fix is already on the target branch),
so the C4 red↔green mechanic cannot run.  It is GREEN on the current
target and the human verifies the GUI at sign-off.  Infra that cannot
drive a widget ``skipTest``s (so only a *delivered* collapsed-folder
miss reports the #7984 symptom), mirroring
``test_bug_0011786_tag_rename_listview.py``.
"""

from __future__ import annotations

import time
import unittest

from dogtail.rawinput import click as raw_click
from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase

# The single no-surname group header (preferences.no-surname-text default,
# gramps/gen/config.py:320 -> "[%s]" % _("Missing Surname")).
NO_SURNAME_GROUP = "[Missing Surname]"
# A NON-first given name in the collapsed group: a hit on it proves the
# search traversed INTO the group, not merely matched its first child.
TARGET_GIVEN = "Onni"


class Bug7984SearchNoSurnameTest(GrampsInterfaceTestCase):
    """Ctrl+F reaches a person in the collapsed no-surname group."""

    TREE_NAME = "Bug7984NoSurname"
    # Name format "Given" (Name.FN = 4): the grouped Name column then holds
    # the given name verbatim, so a typed given name matches it startswith.
    # Roomy window so the tree's rows/columns actually paint under Xvfb
    # (no WM to honour fullscreen); see the #8594 / #11786 tests.
    LAUNCH_CONFIG = (
        "preferences.name-format:4",
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

    def _click_node(self, node) -> bool:
        """raw_click the centre of an AT-SPI node (raw X click — AT-SPI
        ``.click()`` sticks unreliably past the first hop; see #2092 test)."""
        if not self._is_usable(node):
            return False
        try:
            pos, size = node.position, node.size
        except Exception:
            return False
        raw_click(pos[0] + size[0] // 2, pos[1] + size[1] // 2, button=1)
        return True

    def _click_sidebar_category(self, name: str) -> bool:
        for n in self.app.findChildren(
            lambda n, _n=name: n.roleName == "toggle button" and (n.name or "") == _n
        ):
            if self._click_node(n):
                return True
        return False

    def _tree_table(self):
        for n in self.app.findChildren(lambda n: n.roleName == "tree table"):
            if self._is_usable(n):
                return n
        return None

    def _cell_texts(self) -> set[str]:
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
                if c.name == text and self._is_usable(c):
                    return c
            except Exception:
                pass
        return None

    @staticmethod
    def _is_selected(node) -> bool:
        # dogtail exposes AT-SPI states as boolean Node attributes
        # (mirrors base.py's use of ``node.showing``).
        try:
            return bool(getattr(node, "selected", False))
        except Exception:
            return False

    def _focus_name_column_search(self) -> bool:
        """Click the "Name" column header so the type-ahead search column is
        the Name column.

        Gramps wires ``set_search_column`` to the *clicked/sorted* column only
        (``gramps/gui/views/listview.py:826-827`` in ``column_clicked``); it is
        not set at view build. A GtkTreeView's ``search-column`` therefore
        defaults to -1 until a header is clicked, so the search column is NOT
        deterministically the Name column on a fresh view. Clicking the Name
        header pins it (and rebuilds → collapses the groups), making the typed
        given name match the Name cell. Returns True iff the header was
        clicked."""
        for h in self.app.findChildren(
            lambda n: n.roleName in ("table column header", "column header")
            and (n.name or "").strip() == "Name"
        ):
            if self._click_node(h):
                time.sleep(0.8)
                return True
        return False

    # -------------------------------------------------------------------- test
    def test_typeahead_reaches_collapsed_no_surname_group(self):
        self.assertTrue(self.tree_opened, f"{self.TREE_NAME} did not open")

        # Navigate to the (grouped) People view. personview / PersonTreeView
        # is registered first in its category (view.gpr.py:198-211), so it is
        # the default People view.
        if not self._click_sidebar_category("People"):
            self.skipTest("People sidebar category not found / not clickable (infra)")
        time.sleep(1.5)

        if self._tree_table() is None:
            self.skipTest("People view tree table not visible (infra)")

        # Make the Name column the search column (required: the type-ahead
        # search column is not deterministic until a header is clicked — see
        # _focus_name_column_search). Skip rather than risk a false red if the
        # header can't be driven.
        if not self._focus_name_column_search():
            self.skipTest(
                "could not click the 'Name' column header to pin the "
                "type-ahead search column (infra)"
            )

        # Precondition 1: the single no-surname group exists.
        if not self._wait_for_cell(NO_SURNAME_GROUP, present=True, timeout=15.0):
            self.skipTest(
                f"{NO_SURNAME_GROUP!r} group not visible in the People view — "
                "cannot exercise the #7984 collapsed-folder repro (infra/fixture)"
            )

        # Precondition 2: the group is COLLAPSED — the target person's cell is
        # not realised. If it is already showing, the tree opened expanded and
        # this repro cannot demonstrate the collapsed-reach fix.
        if not self._wait_for_cell(TARGET_GIVEN, present=False, timeout=3.0):
            self.skipTest(
                f"{TARGET_GIVEN!r} already visible — the {NO_SURNAME_GROUP!r} "
                "group is not collapsed, so the collapsed-reach path is untested"
            )

        # Drive the type-ahead: focus the tree body (raw-click the group
        # header row), Ctrl+F, type the given name.
        header = self._find_cell(NO_SURNAME_GROUP)
        if header is None or not self._click_node(header):
            self.skipTest("could not focus the People tree body (infra)")
        time.sleep(0.5)
        keyCombo("<Control>f")
        time.sleep(0.6)
        typeText(TARGET_GIVEN)

        # search_init fires ~150ms after the last keystroke
        # (interactivesearchbox.py:_SEARCH_DIALOG_LAUNCH_TIMEOUT); give it
        # room plus the expand/scroll.
        appeared = self._wait_for_cell(TARGET_GIVEN, present=True, timeout=10.0)
        if not appeared:
            self._capture_screenshot("bug7984-no-surname-unreached")
        self.assertTrue(
            appeared,
            f"Ctrl+F type-ahead for {TARGET_GIVEN!r} did NOT reach the "
            f"collapsed {NO_SURNAME_GROUP!r} group — the person's row never "
            "became visible, i.e. search_iter_slow did not descend into the "
            "collapsed group / expand_to_path did not fire (Mantis #7984; "
            "gramps/gui/widgets/interactivesearchbox.py:443-481).",
        )

        # Stronger oracle when the AT-SPI selection state is readable: the
        # reached person is also SELECTED (search_iter_slow -> select_path +
        # set_cursor, interactivesearchbox.py:461-462). Advisory — selection
        # state is flakier to read than cell presence, so don't fail on it.
        cell = self._find_cell(TARGET_GIVEN)
        if cell is not None and not self._is_selected(cell):
            print(
                f"NOTE bug7984: {TARGET_GIVEN!r} became visible but its "
                "selected-state was not observable via AT-SPI (presence is "
                "the load-bearing oracle here)."
            )


if __name__ == "__main__":
    unittest.main()
