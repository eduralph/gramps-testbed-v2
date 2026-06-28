"""Regression for Mantis #13532 ("Fan Chart view ignores the Name format").

Reported (example.gramps, person I1200 "Avis Fernandez"): setting
Edit -> Preferences -> Display -> "Name format" to "Given" updates the list
views but leaves the Fan Chart person labels unchanged — the chart keeps
showing "Fernandez ... Avis III" instead of just "Avis".

Root cause (read on maintenance/gramps61)
------------------------------------------
The fan chart widget renders names on two lines via two *hard-pinned* name
formats registered in ``gramps/gui/widgets/fanchart.py``
(``TWO_LINE_FORMAT_1 = "%l"`` / ``TWO_LINE_FORMAT_2 = "%f %s"``), so the chart
always drew surname / given-suffix regardless of the user's "Name format"
preference, and the view never re-rendered when that preference changed.

Fix
---
``gramps.gen.display.name.NameDisplay`` gains ``get_two_line_format`` /
``display_two_lines``, which split the *active* name format at the
surname/given comma; ``FanChartBaseWidget.draw_person`` renders the two lines
through that, and the three fan-chart views connect ``nameformat-changed`` to
re-render. The gated red->green proof is the headless companion
``gramps/gen/display/test/fanchart_name_format_test.py``.

Why this AT-SPI repro is best-effort
------------------------------------
The fan chart paints its person labels onto a Cairo ``Gtk.DrawingArea``; that
drawn text is NOT exposed through AT-SPI, so a dogtail driver cannot read the
individual chart labels back. This test launches Gramps with the "Given" name
format active, opens the Fan Chart view, and tries to read any chart text the
accessibility tree exposes. When the canvas text is not observable (the usual
case) it ``skipTest``s — which the interface gate records as UNVERIFIABLE for
human sign-off — rather than asserting against text it cannot see. The
behavioural proof for this bug is the headless unit test named above; this
file documents the GUI repro and gives the human a launch path to confirm
visually.
"""

from __future__ import annotations

import time
import unittest

from .base import GrampsInterfaceTestCase

# example.gramps person used in the Mantis report (Avis Fernandez).
REPORT_PERSON_ID = "I1200"
# A surname fragment that MUST NOT appear in a chart rendered with the "Given"
# name format (it only shows given names).
SURNAME_FRAGMENT = "Fernandez"
GIVEN_FRAGMENT = "Avis"


class Bug13532FanchartNameFormatTest(GrampsInterfaceTestCase):
    """With the "Given" name format active, the Fan Chart labels follow that
    format (no surname), reflecting the user's preference (Mantis 13532)."""

    TREE_NAME = "TestTree"
    # preferences.name-format:4 == the standard "Given" format (Name.FN).
    LAUNCH_CONFIG = (
        "preferences.name-format:4",
        "interface.main-window-width:1800",
        "interface.main-window-height:1000",
    )

    # --------------------------------------------------------------- helpers
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

    def _open_fan_chart(self) -> bool:
        """Switch to the Charts category and select the Fan Chart view."""
        # The category toggle is labelled "Charts"; the fan chart view button
        # is labelled "Fan Chart" (it may already be the active chart view).
        self._click_toggle("Charts")
        time.sleep(0.6)
        self._click_toggle("Fan Chart")
        time.sleep(1.0)
        # Confirm a fan chart drawing surface is present.
        return bool(
            self.app.findChildren(
                lambda n: n.roleName in ("drawing area", "canvas", "layered pane")
                and self._is_usable(n)
            )
        )

    def _readable_chart_text(self) -> set[str]:
        """Any text the accessibility tree exposes for the fan chart area.

        Cairo-drawn labels are normally invisible to AT-SPI; this returns
        whatever names/labels/text descendants the chart container does expose
        (often nothing), so the test can tell "observable" from "not".
        """
        found: set[str] = set()
        for area in self.app.findChildren(
            lambda n: n.roleName in ("drawing area", "canvas", "layered pane")
        ):
            try:
                if area.name:
                    found.add(area.name)
                if getattr(area, "description", ""):
                    found.add(area.description)
            except Exception:
                pass
            for sub in area.findChildren(
                lambda n: n.roleName in ("label", "text", "static")
            ):
                try:
                    if sub.name:
                        found.add(sub.name)
                    txt = sub.queryText().getText(0, -1) if hasattr(sub, "queryText") else ""
                    if txt:
                        found.add(txt)
                except Exception:
                    pass
        return found

    # ------------------------------------------------------------------ test
    def test_fanchart_labels_follow_given_name_format(self):
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_fan_chart():
            self.skipTest("could not open the Fan Chart view (infra)")

        texts = self._readable_chart_text()
        readable = {t for t in texts if GIVEN_FRAGMENT in t or SURNAME_FRAGMENT in t}
        if not readable:
            self.skipTest(
                "Fan Chart person labels are Cairo-drawn and not exposed via "
                "AT-SPI — per-label text is not observable here. The gated "
                "red->green proof is the headless unit test "
                "gramps/gen/display/test/fanchart_name_format_test.py; verify "
                "visually: with 'Name format: Given', person "
                f"{REPORT_PERSON_ID} must read '{GIVEN_FRAGMENT}', not "
                f"'{SURNAME_FRAGMENT} ... {GIVEN_FRAGMENT} III'."
            )

        # If the chart text IS observable, the "Given" format must not leak the
        # surname into the chart labels.
        leaked = sorted(t for t in readable if SURNAME_FRAGMENT in t)
        if leaked:
            self._capture_screenshot("bug13532-fanchart-name-format")
        self.assertEqual(
            [],
            leaked,
            "Fan Chart shows surname text "
            f"{leaked!r} while the active 'Name format' is 'Given' — the chart "
            "ignores the name-format preference (Mantis 13532).",
        )


if __name__ == "__main__":
    unittest.main()
