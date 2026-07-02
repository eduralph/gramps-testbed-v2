"""Regression for Mantis #8617 ("Filter gramplet in the Bottombar is ignored
when the sidebar is hidden").

Reported by sam888 (4.1.3) and confirmed by bamaustin (5.1.3) across multiple
views: the Filter gramplet added to the Bottombar filters the list view *only*
while the sidebar filter is also visible. When the sidebar is hidden — so the
Bottombar gramplet is the user's only filter UI, and the Search bar is enabled
in the sidebar's place — pressing Find in the gramplet does nothing; the list is
not filtered. bamaustin correctly suspected the Search bar (enabled precisely
when the sidebar is hidden) was bypassing the filter.

Root cause (read on maintenance/gramps61)
------------------------------------------
``ListView.build_tree`` chooses between the gramplet's ``generic_filter`` and
the Search bar's value purely on Search-bar visibility
(``gramps/gui/views/listview.py:335``); the same pattern is in
``column_clicked`` (``listview.py:786``). ``sidebar_toggled`` shows the Search
bar exactly when the sidebar is hidden (``listview.py:432-440``). So when the
sidebar is hidden the Search bar is visible, ``build_tree`` takes the Search-bar
branch and the gramplet's ``view.generic_filter`` (set in
``gramps/plugins/gramplet/filter.py:76``) is silently dropped.

Fix
---
A *set* ``generic_filter`` takes effect regardless of Search-bar visibility:
the branch condition becomes ``self.generic_filter is not None or not
self.search_bar.is_visible()``. This is in the shared ``ListView`` base, so it
holds for every list view (People, Events, Sources, ...), not one special case.

Repro driven here
-----------------
The People view is configured (via its bottombar/sidebar gramplet-bar .ini,
seeded before launch) with the Filter gramplet in the Bottombar and the sidebar
hidden — precisely the reporter's configuration. The Gramps status bar shows the
view's applied filter as ``<title>: matched/total`` (``ListView.build_tree`` ->
``uistate.show_filter_results`` -> ``Statusbar.set_filter``,
``gramps/gui/widgets/statusbar.py:137``). The test records the matched count with
no filter, sets the gramplet's Name field to a common surname and applies it,
then reads the matched count again.

  * PRE-FIX (red): applying the filter changes nothing — matched stays == total
    (the gramplet's generic_filter was dropped because the Search bar is visible).
  * POST-FIX (green): matched drops below total — the gramplet's filter is
    applied even though the Search bar is visible.

The matched/total status text reflects ``model.displayed()``/``model.total()``,
so it is immune to GtkTreeView row virtualisation (only on-screen rows surface as
AT-SPI cells) and works for the grouped People view as well as flat list views.

Advisory tier
-------------
Per INTEGRATION.md the interface tier is advisory; this GUI repro is the
characterisation the human weighs at sign-off, and the behavioral C4
(run-verify-interface.sh) runs it red-unpatched / green-patched. It skips
gracefully when the test infra cannot drive a widget or establish the
sidebar-hidden precondition, so only a delivered #8617 symptom (the applied
filter leaving the row count unchanged) reports a failure.
"""

from __future__ import annotations

import os
import re
import time
import unittest

from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase

# A common surname in the canonical example.gramps tree (example/gramps/
# example.gramps): filtering the People Name field to it must leave far fewer
# than the whole tree's people, so matched < total is an unambiguous signal.
FILTER_SURNAME = "Warner"

# matched/total as painted by Statusbar.set_filter ("<title>: matched/total").
_COUNT_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


class Bug8617BottombarFilterTest(GrampsInterfaceTestCase):
    """A filter applied via the Bottombar Filter gramplet filters the People
    list even when the sidebar is hidden and the Search bar is visible
    (Mantis 8617)."""

    TREE_NAME = "TestTree"
    # The default People view is the grouped person view (view.gpr.py:198 —
    # ``personview`` registered first in the People category). Its gramplet-bar
    # config files are keyed by ``<category>_<view-id>`` (pageview.py:127,160,168).
    VIEW_IDENT = "People_personview"
    LAUNCH_CONFIG = (
        "interface.main-window-width:1800",
        "interface.main-window-height:1000",
    )

    # ------------------------------------------------------------- config seed
    @classmethod
    def _version_dir(cls) -> str | None:
        """The Gramps per-version config directory (VERSION_DIR) where the
        gramplet-bar .ini files live. Prefer the value Gramps itself computes;
        fall back to the XDG layout so a seed is still attempted."""
        try:
            from gramps.gen.const import VERSION_DIR  # GUI-free (used by the CLI)

            return VERSION_DIR
        except Exception:
            base = os.environ.get(
                "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
            )
            # Best-effort: match gramps%s%s for a 6.x line.
            for name in ("gramps61", "gramps60", "gramps52", "gramps51"):
                cand = os.path.join(base, "gramps", name)
                if os.path.isdir(os.path.dirname(cand)):
                    return cand
            return os.path.join(base, "gramps", "gramps61")

    @classmethod
    def _seed_gramplet_bars(cls) -> None:
        """Put the Filter gramplet in the Bottombar and hide the sidebar for the
        People view, by writing the gramplet-bar .ini files GrampletBar.__load
        reads (grampletbar.py:113,198). This is the reporter's configuration; it
        makes the Bottombar gramplet the only filter UI and forces the Search bar
        visible (sidebar_toggled shows it when the sidebar is hidden)."""
        vdir = cls._version_dir()
        if not vdir:
            return
        os.makedirs(vdir, exist_ok=True)
        # Bottombar: hold the Person Filter gramplet, visible. The section
        # ``name`` must be the gramplet id registered in gramplet.gpr.py:1220.
        with open(
            os.path.join(vdir, "%s_bottombar.ini" % cls.VIEW_IDENT),
            "w",
            encoding="utf-8",
        ) as fp:
            fp.write(
                ";; Gramplet bar configuration file\n"
                "[Bar Options]\n"
                "visible=True\n"
                "page=0\n\n"
                "[Person Filter]\n"
                "name=Person Filter\n"
                "page=0\n"
            )
        # Sidebar: hidden. With visible=False the sidebar GrampletBar is not
        # shown, so build_interface calls sidebar_toggled(False) -> the Search
        # bar is shown (listview.py:432-440) — the exact #8617 trigger.
        with open(
            os.path.join(vdir, "%s_sidebar.ini" % cls.VIEW_IDENT),
            "w",
            encoding="utf-8",
        ) as fp:
            fp.write(
                ";; Gramplet bar configuration file\n"
                "[Bar Options]\n"
                "visible=False\n"
                "page=0\n"
            )

    @classmethod
    def setUpClass(cls) -> None:
        # Seed BEFORE gramps launches: GrampletBar reads the .ini when the
        # People view is first built.
        try:
            cls._seed_gramplet_bars()
        except Exception:
            # A failed seed only means the precondition may not hold; the test
            # method verifies it and skips (unverifiable) rather than mis-report.
            pass
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

    def _showing_name_labels(self) -> list:
        return [
            lbl
            for lbl in self.app.findChildren(
                lambda n: n.roleName == "label" and (n.name or "").strip() == "Name"
            )
            if self._is_usable(lbl)
        ]

    def _search_bar_visible(self) -> bool:
        """True iff the Search bar is showing. The Search bar carries a "_Clear"
        button (searchbar.py:60 -> AT-SPI name "Clear"); the sidebar filter's
        reset button is named "Reset" (_sidebarfilter.py:120) — so a showing
        "Clear" push button uniquely means the Search bar (hence: sidebar hidden,
        the #8617 trigger). ``search_bar.is_visible()`` gates the buggy branch."""
        for b in self.app.findChildren(
            lambda n: n.roleName == "push button" and (n.name or "").strip() == "Clear"
        ):
            if self._is_usable(b):
                return True
        return False

    def _ensure_sidebar_hidden(self, timeout: float = 8.0) -> bool:
        """The #8617 precondition: the sidebar filter is hidden so the Search bar
        is visible, and the Bottombar Filter gramplet is loaded (its single "Name"
        label). If the sidebar is up (Search bar absent, or a second sidebar
        "Name" label), toggle it off with the Sidebar accelerator (<Shift><Ctrl>R,
        pageview.py:479). Holds when: Search bar visible AND exactly one showing
        "Name" label (the Bottombar gramplet)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._search_bar_visible() and len(self._showing_name_labels()) == 1:
                return True
            try:
                keyCombo("<Shift><Control>r")
            except Exception:
                pass
            time.sleep(1.0)
        return self._search_bar_visible() and len(self._showing_name_labels()) == 1

    def _filter_name_entry(self):
        """The Bottombar Filter gramplet's "Name" text entry.

        SidebarFilter.add_entry attaches the "Name" BasicLabel and its BasicEntry
        to the same Gtk.Grid on the same row (_sidebarfilter.py:243-248). With the
        sidebar hidden there is exactly one showing "Name" label; pick the text
        entry sharing that label's parent grid and lying on its row (same y)."""
        labels = self._showing_name_labels()
        if not labels:
            return None
        label = labels[0]
        try:
            label_y = label.position[1]
            parent = label.parent
        except Exception:
            return None
        candidates = []
        for ent in self.app.findChildren(
            lambda n: n.roleName in ("text", "entry")
        ):
            if not self._is_usable(ent):
                continue
            try:
                same_parent = ent.parent == parent
                ey = ent.position[1]
            except Exception:
                continue
            if same_parent:
                candidates.append((abs(ey - label_y), ent))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]

    def _gramplet_find_button(self, near):
        """The Filter gramplet's own "_Find" apply button (_sidebarfilter.py:77,
        134). Walk up from the Name entry to the nearest ancestor that also holds
        a showing "Find" push button — that ancestor is the gramplet's vbox, so
        this returns the gramplet's Find, never the Search bar's (which lives in a
        separate subtree only shared at a higher common ancestor)."""
        node = near
        for _ in range(6):
            try:
                node = node.parent
            except Exception:
                return None
            if node is None:
                return None
            try:
                btns = [
                    b
                    for b in node.findChildren(
                        lambda n: n.roleName == "push button"
                        and (n.name or "").replace("_", "") == "Find"
                    )
                    if self._is_usable(b)
                ]
            except Exception:
                btns = []
            if btns:
                return btns[0]
        return None

    def _filter_counts(self):
        """(matched, total) parsed from the status-bar filter label
        ("<title>: matched/total"), or None if not readable yet."""
        best = None
        for lbl in self.app.findChildren(lambda n: n.roleName == "label"):
            try:
                if not self._is_usable(lbl):
                    continue
                text = lbl.name or ""
            except Exception:
                continue
            m = _COUNT_RE.search(text)
            if not m:
                continue
            pair = (int(m.group(1)), int(m.group(2)))
            # The filter label carries a ':' ("<title>: n/m"); prefer it.
            if ":" in text:
                return pair
            best = pair
        return best

    def _wait_counts(self, timeout: float = 8.0):
        deadline = time.monotonic() + timeout
        counts = self._filter_counts()
        while counts is None and time.monotonic() < deadline:
            time.sleep(0.3)
            counts = self._filter_counts()
        return counts

    # -------------------------------------------------------------------- test
    def test_bottombar_filter_applies_with_sidebar_hidden(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._click_toggle("People"):
            self.skipTest("could not switch to the People category (infra)")
        time.sleep(1.5)

        # Precondition: the sidebar is hidden (so the Search bar is visible — the
        # #8617 trigger) and the Bottombar Filter gramplet is present (its single
        # "Name" label).
        if not self._ensure_sidebar_hidden():
            self.skipTest(
                "could not establish the sidebar-hidden precondition — either the "
                "Bottombar Filter gramplet did not load or the sidebar stayed "
                "visible (infra/config seed)"
            )

        before = self._wait_counts()
        if before is None:
            self.skipTest("could not read the filter results count before filtering (infra)")
        matched_before, total = before
        if matched_before != total:
            self.skipTest(
                f"a filter is already active at start ({matched_before}/{total}); "
                "cannot establish the unfiltered baseline (infra)"
            )

        entry = self._filter_name_entry()
        if entry is None:
            self.skipTest("Bottombar Filter gramplet 'Name' entry not found (infra)")

        try:
            entry.click()
            time.sleep(0.3)
            keyCombo("<Control>a")
            typeText(FILTER_SURNAME)
            time.sleep(0.3)
        except Exception:
            self.skipTest("could not type into the Bottombar filter Name entry (infra)")

        # Apply the filter. Prefer the gramplet's own Find button (deterministic);
        # fall back to Return in the Name entry, which SidebarFilter.key_press
        # routes to clicked() (_sidebarfilter.py:229-233). Either path runs
        # Filter.__filter_clicked -> view.generic_filter = get_filter();
        # view.build_tree() — the production code under test.
        applied = False
        btn = self._gramplet_find_button(entry)
        if btn is not None:
            try:
                btn.click()
                applied = True
            except Exception:
                applied = False
        if not applied:
            try:
                entry.click()
                keyCombo("<Return>")
                applied = True
            except Exception:
                self.skipTest("could not apply the Bottombar filter (infra)")
        time.sleep(1.2)

        # The applied filter must reduce the displayed rows below the total.
        deadline = time.monotonic() + 8.0
        after = self._filter_counts()
        while time.monotonic() < deadline:
            after = self._filter_counts()
            if after is not None and after[0] < after[1]:
                break
            time.sleep(0.3)

        if after is None:
            self.skipTest("could not read the filter results count after filtering (infra)")
        matched_after, total_after = after

        if not (matched_after < total_after):
            self._capture_screenshot("bug8617-bottombar-filter-ignored")
        self.assertLess(
            matched_after,
            total_after,
            f"Applying the Bottombar Filter gramplet (Name={FILTER_SURNAME!r}) with "
            f"the sidebar hidden did NOT filter the People list: displayed count "
            f"stayed at {matched_after}/{total_after} (was {matched_before}/{total} "
            "before). The gramplet's view.generic_filter was dropped because the "
            "Search bar is visible (Mantis 8617; gramps/gui/views/listview.py:335).",
        )


if __name__ == "__main__":
    unittest.main()
