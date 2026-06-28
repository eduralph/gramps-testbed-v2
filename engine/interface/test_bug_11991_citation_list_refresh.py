"""Regression for Mantis #11991 ("citation list does not refresh after a
citation is edited in the Sources view").

Reported against Gramps 5.x: in the Sources view, selecting a source shows its
references in the bottombar "Source Backlinks" gramplet (the "source reference
list" the reporter describes, notes.json ~0061089). Editing one of those
citations and saving it left the row showing the pre-edit value; the user had to
select another source and come back for the change to appear.

Root cause / status (read on maintenance/gramps61)
--------------------------------------------------
The backlinks gramplets refresh by subscribing to object-change signals. The
``Source Backlinks`` gramplet is ``SourceBacklinks`` (gramplet.gpr.py:1140-1148),
a subclass of ``Backlinks`` (gramps/plugins/gramplet/backlinks.py:53). At the
time the bug was filed, each subclass only connected its OWN object's
``*-update`` signal (e.g. ``SourceBacklinks`` connected ``source-update`` only),
so editing a *citation* that referenced the source emitted ``citation-update``
with no handler and the gramplet never re-ran.

That is exactly the fix Paul Culley described in the Mantis thread
(notes.json ~0061112: "for sources, the only objects that matter would be
Citations ...") and it was implemented upstream by commit 9957506f35
("Fix References Gramplet for inadequate updates when other objects change",
PR 1192 / Mantis #12248): ``Backlinks.db_changed`` now connects ``%s-add`` /
``%s-update`` / ``%s-delete`` for ALL nine object types -- including
``citation-update`` -- to ``self.update`` (backlinks.py:245-263). When a
citation is saved, ``citation-update`` fires, ``Backlinks.update`` re-runs
``main`` while the gramplet is the active bottombar tab (gramps/gen/plug/
_gramplet.py:297-318), ``display_backlinks`` re-reads each backlink from the DB
(backlinks.py:159-181), and ``navigation_label`` rebuilds the Citation row as
``[id] <source title> <page>`` (gramps/gen/utils/db.py:344-348). The edited page
therefore shows immediately, with no navigate-away-and-back.

So on maintenance/gramps61 this bug is ALREADY FIXED. This committed AT-SPI repro
is the GUI characterisation the human weighs at sign-off: it drives the real
Sources-view + Source-Backlinks-gramplet flow and asserts the edited citation
row refreshes in place. It PASSES on the current target (no patch); it would
FAIL on the pre-#12248 code where the citation signal was never connected.

Fixture
-------
TestTree = example.gramps. Source S00001 "All possible citations"
(handle ``_c140d4ef77841``) is referenced by citations C02828.. whose pages are
"page 01", "page 02", ... (the only source in the example whose backlinks carry
editable page text), so a backlinks cell text match for "page NN" is
unambiguous.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory. The backlinks refresh handler
imports ``gi`` at module load, so it is not reachable under the headless core
unit runner -- the C4 (unit) red->green is recorded UNVERIFIABLE; this GUI repro
plus the static citation above are the load-bearing evidence.
"""

from __future__ import annotations

import time
import unittest

from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase

SOURCE_TITLE = "All possible citations"
# A page string present on a citation that references SOURCE_TITLE in
# example.gramps; rendered in the Source Backlinks row as
# "[Cxxxxx] All possible citations page 01".
ORIG_PAGE = "page 01"
NEW_PAGE = "page ZZ11991"


class Bug11991CitationListRefreshTest(GrampsInterfaceTestCase):
    """Editing a citation refreshes the Source Backlinks list without a restart."""

    TREE_NAME = "TestTree"
    # Give the view room so the list rows and the bottombar gramplet actually
    # paint under Xvfb (no WM to honour fullscreen) -- same rationale as the
    # bug 8594 / 11786 interface tests.
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

    def _all_cell_texts(self) -> set[str]:
        texts: set[str] = set()
        for c in self.app.findChildren(lambda n: n.roleName == "table cell"):
            try:
                if c.name:
                    texts.add(c.name)
            except Exception:
                pass
        return texts

    def _find_cell(self, substring: str):
        for c in self.app.findChildren(
            lambda n, _s=substring: n.roleName == "table cell" and _s in (n.name or "")
        ):
            if self._is_usable(c):
                return c
        return None

    def _wait_cell(self, substring: str, present: bool, timeout: float = 10.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            has = any(substring in t for t in self._all_cell_texts())
            if has == present:
                return True
            time.sleep(0.3)
        return any(substring in t for t in self._all_cell_texts()) == present

    def _open_sources_view(self) -> bool:
        # The Sources view registers category ("Sources", _("Sources")); its
        # sidebar toggle is named "Sources".
        if not self._click_named("toggle button", "Sources"):
            return False
        time.sleep(0.5)
        return self._wait_cell(SOURCE_TITLE, present=True, timeout=10.0)

    def _select_source(self) -> bool:
        cell = self._find_cell(SOURCE_TITLE)
        if cell is None:
            return False
        try:
            cell.click()
        except Exception:
            return False
        time.sleep(0.4)
        return True

    def _show_source_backlinks(self) -> bool:
        # The bottombar carries the Source Backlinks gramplet by default; click
        # its page tab so its tree of references is on screen.
        return self._click_named("page tab", "Source Backlinks") or self._click_named(
            "page tab", "Backlinks"
        )

    def _edit_citation_page(self) -> bool:
        """Double-click the citation backlink row, change Volume/Page, save."""
        cell = self._find_cell(ORIG_PAGE)
        if cell is None:
            return False
        try:
            cell.doActionNamed("activate")  # double-click equivalent -> editor
        except Exception:
            try:
                cell.click()
                cell.click()
            except Exception:
                return False
        time.sleep(0.8)
        # In the citation editor, the Volume/Page entry currently holds ORIG_PAGE.
        # Find the text entry whose value matches and replace it.
        entry = None
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and entry is None:
            for t in self.app.findChildren(lambda n: n.roleName == "text"):
                if not self._is_usable(t):
                    continue
                try:
                    if (t.text or "") == ORIG_PAGE:
                        entry = t
                        break
                except Exception:
                    pass
            if entry is None:
                time.sleep(0.3)
        if entry is None:
            return False
        try:
            entry.click()
            keyCombo("<Control>a")
            typeText(NEW_PAGE)
        except Exception:
            return False
        # Save the citation editor (the OK button is labelled "_OK").
        return self._click_named("push button", "OK")

    # -------------------------------------------------------------------- test
    def test_citation_edit_refreshes_backlinks_list(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_sources_view():
            self.skipTest("Sources view / source list did not render (infra)")
        if not self._select_source():
            self.skipTest(f"could not select source {SOURCE_TITLE!r} (infra)")
        if not self._show_source_backlinks():
            self.skipTest("Source Backlinks gramplet tab not reachable (infra)")
        if not self._wait_cell(ORIG_PAGE, present=True, timeout=10.0):
            self.skipTest(
                f"citation backlink {ORIG_PAGE!r} not visible in Source Backlinks "
                "-- cannot exercise the refresh repro (infra)"
            )

        if not self._edit_citation_page():
            self.skipTest("could not drive the citation edit/save flow (infra)")

        # Post-fix: the edited page appears in the Source Backlinks row with no
        # navigate-away-and-back. Pre-#12248 the row still reads the stale page.
        appeared = self._wait_cell(NEW_PAGE, present=True, timeout=10.0)
        stale_gone = self._wait_cell(ORIG_PAGE, present=False, timeout=3.0)
        if not appeared:
            self._capture_screenshot("bug11991-stale-citation-row")
        self.assertTrue(
            appeared and stale_gone,
            f"Source Backlinks still shows {ORIG_PAGE!r} after editing the "
            f"citation page to {NEW_PAGE!r} (bug 11991: the gramplet never "
            "subscribed to citation-update). On maintenance/gramps61 this is "
            "fixed by Backlinks.db_changed (backlinks.py:245-263).",
        )


if __name__ == "__main__":
    unittest.main()
