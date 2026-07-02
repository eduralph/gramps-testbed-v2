"""Regression for Mantis #8603 ("Family editor Events tab shows a participant's
old name after that person is edited from the same dialog").

Reported by Daniele (4.1.3), confirmed by dsblank from the reporter's
screenshot: open a family from the Families view, look at the embedded Events
tab's "Main Participants" column, then edit the father from the family window,
change his name and press OK. The Events tab keeps showing the father's OLD
name -- only the top father/mother panel refreshes.

Root cause (read on maintenance/gramps61)
------------------------------------------
``EditFamily`` maps the ``person-update`` db signal to ``topdata_updated``
(gramps/gui/editors/editfamily.py:507), which calls only ``load_data``
(editfamily.py:782-796) -- the top father/mother panel. The embedded event list
(``self.event_list``, an ``EventEmbedList`` created at editfamily.py:816) only
registers ``event-*`` callbacks (gramps/gui/editors/displaytabs/eventembedlist.py:139-150),
never ``person-update``. Its "Main Participants" column is derived from the
referenced persons' names (``column_participant`` ->
``get_participant_from_event``, gramps/gui/editors/displaytabs/eventrefmodel.py:204-205),
so when a participant is renamed and committed the column is left stale. (The
Children tab, by contrast, already rebuilds on ``person-update`` --
editfamily.py:179,185-190 -- which is the pattern the fix mirrors.)

Fix
---
A dedicated ``person-update`` handler ``EditFamily.person_updated`` refreshes the
top panel (``topdata_updated``) *and* rebuilds the embedded event list
(``self.event_list.rebuild_callback()``), so the "Main Participants" column
re-reads the referenced persons' current names.

Repro driven here
-----------------
Open the Families view, then a family whose father is a Main Participant of a
listed event. Rename the father to a unique sentinel surname via the family
window's father Edit button + the Edit Person dialog, press OK, and confirm the
Events tab's cells now contain that sentinel. Pre-fix the sentinel never appears
(the column keeps the old name); post-fix it does.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory; this GUI characterisation is
what the human weighs at sign-off. Every navigation/readout step the
accessibility tree cannot drive is ``skipTest``-ed (recorded UNVERIFIABLE)
rather than false-failing, so only a genuinely stale Main-Participants column
reports the #8603 symptom.
"""

from __future__ import annotations

import re
import time
import unittest
import uuid

from dogtail.rawinput import keyCombo

from .base import GrampsInterfaceTestCase

# A surname unlikely to occur in the example tree, so its presence in the Events
# tab can only be the freshly-renamed father. UNIQUE PER PROCESS: C4-verify-interface
# seeds TestTree ONCE and runs the red (unpatched) then green (patched) legs against
# the SAME database. The red leg's rename COMMITS (the bug only stalls the column
# refresh), so a fixed sentinel would already be present on the green leg and the
# pre-edit guard below would skipTest — reporting green WITHOUT exercising the patched
# refresh (a false green). A fresh value per leg forces the green leg to genuinely
# rename and re-read the column.
SENTINEL = "Zqx8603" + uuid.uuid4().hex[:10]


class Bug8603FamilyEventParticipantRefreshTest(GrampsInterfaceTestCase):
    """The Family editor Events tab refreshes a renamed participant's name."""

    TREE_NAME = "TestTree"
    # Give the editor room so the Events tab table paints under Xvfb (no WM
    # honours fullscreen) -- same rationale as the bug 11991 / 12539 tests.
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

    def _first_usable(self, root, predicate, timeout: float = 8.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in root.findChildren(predicate):
                if self._is_usable(n):
                    return n
            time.sleep(0.3)
        return None

    def _click_named(self, root, roles, name_substr: str, timeout: float = 8.0) -> bool:
        if isinstance(roles, str):
            roles = (roles,)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in root.findChildren(
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

    def _table_with_header(self, root, header_name: str):
        """First usable (tree) table under ``root`` carrying the given column
        header. "Father" identifies the family list; "Main Participants" the
        family editor's embedded Events tab."""
        for tbl in root.findChildren(lambda n: n.roleName in ("tree table", "table")):
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

    def _cell_blob(self, table) -> str:
        """Concatenate the text of every cell of ``table`` (one lower-cased
        blob to substring-search for a participant name)."""
        if table is None:
            return ""
        parts = []
        for cell in table.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if cell.name and cell.name.strip():
                    parts.append(cell.name.strip())
            except Exception:
                pass
        return " ".join(parts)

    def _open_families_view(self) -> bool:
        if not self._click_named(self.app, "toggle button", "Families"):
            return False
        time.sleep(0.6)
        return self._table_with_header(self.app, "Father") is not None

    def _column_x_range(self, table, header_name: str):
        """The horizontal extent (x_lo, x_hi) of the named column's header, or
        None if it can't be resolved — used to keep cell selection to one column."""
        for h in table.findChildren(
            lambda n: n.roleName == "table column header"
        ):
            try:
                if header_name in (h.name or "") and self._is_usable(h):
                    x, w = h.position[0], h.size[0]
                    if w > 0:
                        return (x, x + w)
            except Exception:
                pass
        return None

    def _father_cells(self):
        tbl = self._table_with_header(self.app, "Father")
        if tbl is None:
            return []
        cells = []
        for cell in tbl.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if cell.name and cell.name.strip() and self._is_usable(cell):
                    cells.append(cell)
            except Exception:
                pass
        # Restrict to the FATHER column so the matched token is genuinely the
        # father's name (the person renamed below). A mother/date/ID cell whose
        # token happens to appear in Main Participants would otherwise select a
        # family whose FATHER isn't a listed participant, so renaming him could
        # never surface the sentinel → a false red on a correctly-fixed build.
        # Fall back to all cells when the column geometry can't be resolved, so
        # this never regresses to selecting nothing.
        col = self._column_x_range(tbl, "Father")
        if col is not None:
            lo, hi = col
            in_col = []
            for c in cells:
                try:
                    cx = c.position[0] + c.size[0] / 2
                except Exception:
                    continue
                if lo <= cx <= hi:
                    in_col.append(c)
            if in_col:
                return in_col
        return cells

    def _family_dialog(self, timeout: float = 12.0):
        """A dialog/frame that owns an "Events" page tab -- the Family editor."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for d in self.app.findChildren(
                lambda n: n.roleName in ("dialog", "frame")
            ):
                if not self._is_usable(d):
                    continue
                if d.findChildren(
                    lambda n: n.roleName == "page tab" and "Events" in (n.name or "")
                ):
                    return d
            time.sleep(0.3)
        return None

    def _person_dialog(self, timeout: float = 12.0):
        """The Edit Person dialog opened over the family editor."""
        return self._first_usable(
            self.app,
            lambda n: n.roleName in ("dialog", "frame")
            and "Person" in (n.name or ""),
            timeout=timeout,
        )

    def _entry_near_label(self, dialog, label_substr: str):
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
        keyCombo("Tab")
        time.sleep(0.3)

    @staticmethod
    def _tokens(text: str):
        return [t for t in re.split(r"[\s,\[\]]+", text or "") if len(t) >= 3]

    def _close_dialog(self, dialog) -> None:
        if dialog is None:
            return
        # Nothing was changed on a skipped family, so Cancel/Escape closes it
        # cleanly (no save prompt).
        if not self._click_named(dialog, "push button", "Cancel", timeout=3.0):
            try:
                keyCombo("Escape")
            except Exception:
                pass
        time.sleep(0.5)

    # -------------------------------------------------------------------- test
    def test_event_tab_refreshes_renamed_participant(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_families_view():
            self.skipTest("Families view / family list did not render (infra)")

        cells = self._father_cells()
        if not cells:
            self.skipTest("no family rows to exercise the repro (infra)")

        # Find a family whose father is a Main Participant of a listed event:
        # open its editor, show the Events tab, and confirm a father-name token
        # appears in that table before we touch anything. Otherwise the sentinel
        # could never appear even post-fix, which would be an infra false-red.
        family_dialog = None
        for cell in cells[:12]:
            father_text = (cell.name or "").strip()
            tokens = self._tokens(father_text)
            if not tokens:
                continue
            try:
                cell.doubleClick()
            except Exception:
                continue
            dialog = self._family_dialog()
            if dialog is None:
                continue
            self._click_named(dialog, "page tab", "Events", timeout=4.0)
            time.sleep(0.5)
            table = self._table_with_header(dialog, "Main Participants")
            blob = self._cell_blob(table)
            if table is not None and any(tok in blob for tok in tokens):
                family_dialog = dialog
                break
            # Not usable for the repro -- close and try the next family.
            self._close_dialog(dialog)

        if family_dialog is None:
            self.skipTest(
                "could not open a family whose father is a listed Main "
                "Participant via AT-SPI (infra)"
            )

        # Sanity: the sentinel must not already be present.
        table = self._table_with_header(family_dialog, "Main Participants")
        if SENTINEL in self._cell_blob(table):
            self.skipTest("sentinel unexpectedly present before the edit (infra)")

        # Edit the father: the family window's father Edit button is the topmost
        # "Edit" push button (glade fbutton_edit-atkobject, accessible-name
        # "Edit"; the mother's is below it).
        edit_buttons = [
            b
            for b in family_dialog.findChildren(
                lambda n: n.roleName == "push button" and (n.name or "") == "Edit"
            )
            if self._is_usable(b)
        ]
        if not edit_buttons:
            self.skipTest("could not locate the father Edit button (infra)")
        edit_buttons.sort(key=lambda b: b.position[1])
        try:
            edit_buttons[0].click()
        except Exception:
            self.skipTest("could not activate the father Edit button (infra)")

        person_dialog = self._person_dialog()
        if person_dialog is None:
            self.skipTest("Edit Person dialog did not open via AT-SPI (infra)")

        surname = self._entry_near_label(person_dialog, "Surname")
        if surname is None:
            self.skipTest("could not locate the Surname entry in Edit Person (infra)")
        self._set_entry(surname, SENTINEL)

        if not self._click_named(person_dialog, "push button", "OK", timeout=6.0):
            self.skipTest("could not press OK in the Edit Person dialog (infra)")

        # Let the person-update signal propagate and the family editor react.
        time.sleep(1.5)

        table = self._table_with_header(family_dialog, "Main Participants")
        after = self._cell_blob(table)
        if SENTINEL not in after:
            self._capture_screenshot("bug8603-stale-participant")
        self.assertIn(
            SENTINEL,
            after,
            "The Family editor Events tab's Main Participants column still shows "
            "the father's old name after he was renamed and saved from the same "
            "dialog -- the embedded event list did not refresh on person-update "
            "(bug 8603).",
        )


if __name__ == "__main__":
    unittest.main()
