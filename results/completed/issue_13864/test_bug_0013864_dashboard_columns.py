"""E2E regression for Mantis #13864 ("Dashboard 'Number of Columns' crash
locks the family tree").

Reported against Gramps 6.0.1.  On the Dashboard, ``Configure the active
view`` -> ``Gramplet Layout`` -> ``Number of Columns:`` set to a large value
(the reporter used **1000**) freezes Gramps ("Not responding"); the process
then disappears with no error, and on restart the family tree is **locked**.

Root cause (read on maintenance/gramps61)
------------------------------------------
The "Number of Columns" control is an unbounded positive-integer text entry
(``configure.ConfigureDialog.add_pos_int_entry``,
gramps/gui/configure.py:490-514).  Its ``changed`` callback routes the typed
value through the registered setter ``GrampletPane.set_columns``
(gramps/gui/widgets/grampletpane.py:1628-1642), which floors the value at 1
but imposes **no ceiling**, then builds one ``Gtk.Box`` per column in
``for i in range(self.column_count)`` (grampletpane.py:1397-1402).  A value
like 1000 makes GTK allocate/realize an enormous layout; the main loop never
returns, AT-SPI stops answering, and the process is eventually killed.  Because
it dies without releasing the BSD database lock under
``~/.gramps/grampsdb/<tree>/``, the tree stays locked on the next start.

The same unbounded value also reaches ``column_count`` from a saved ``.ini``
(``load_gramplets``, grampletpane.py:1199-1200) and from ``__init__`` kwargs
(grampletpane.py:1020), so the invariant ("any accepted column value yields a
survivable layout") must hold for all three entry points, not just the live
dialog.

Fix: bound every column-count entry point to ``[1, MAX_GRAMPLET_COLUMNS]``
(=100) via ``clamp_column_count`` before it drives widget allocation
(grampletpane.py), and surface the accepted range as the entry's tooltip.

Advisory tier / unverifiable C4
-------------------------------
The crash lives entirely inside live GTK widget allocation in
``GrampletPane`` -- a ``gi``/``gramps.gui`` module that the headless C4 runner
cannot import without a display, and that cannot be exercised without a running
main loop.  There is therefore no import-light production seam a headless unit
test could drive that would also go red when the production clamp is reverted
(a helper-only unit test would stay green regardless, decoupling C4 from the
fix).  The bundle's C4 red->green mechanic is consequently declared
``PDCA-UNVERIFIABLE`` (patch ships no core ``*_test.py``); this GUI test is the
load-bearing reproduction the human weighs at sign-off.

It uses graceful skips when the harness cannot drive a widget (sidebar toggle,
config button, page tab, entry), so it only reports a *failure* when it has
actually driven the "Number of Columns" entry and Gramps then died or stopped
responding -- which is exactly the #13864 symptom.
"""

from __future__ import annotations

import threading
import time
import unittest

from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase

# A column count in the same "accepted by the control" class as the reporter's
# 1000, chosen large enough that the unbounded-allocation symptom manifests
# within the headless harness's time budget.  The fix clamps ANY such value to
# MAX_GRAMPLET_COLUMNS (=100), so post-fix this is survivable; pre-fix it is the
# freeze/crash the reporter saw.
PATHOLOGICAL_COLUMNS = "100000"

# How long to watch for the freeze/crash after entering the value.
SURVIVE_TIMEOUT = 30.0


class Bug13864DashboardColumnsTest(GrampsInterfaceTestCase):
    """A large Dashboard column count must not crash Gramps or freeze it."""

    TREE_NAME = "TestTree"
    # Give the Dashboard room so its config button/dialog actually paint under
    # Xvfb (no window manager to honour a maximised default).
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

    def _click_named(
        self, roles, name_contains, exact=False, timeout: float = 8.0
    ) -> bool:
        if isinstance(roles, str):
            roles = (roles,)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n: n.roleName in roles and bool(n.name)
            ):
                nm = n.name or ""
                ok = nm == name_contains if exact else name_contains in nm
                if ok and self._is_usable(n):
                    try:
                        n.click()
                        return True
                    except Exception:
                        pass
            time.sleep(0.3)
        return False

    def _open_dashboard(self) -> bool:
        """Switch to the Dashboard category (category ("Dashboard",
        "Dashboard"); the sidebar toggle is named "Dashboard")."""
        # The default launch view is usually the Dashboard already; clicking
        # the toggle is a no-op then, and makes the test robust if it is not.
        for name in ("Dashboard", "Gramplets"):
            if self._click_named("toggle button", name, exact=True, timeout=4.0):
                time.sleep(0.5)
                return True
        # Even if no toggle was clickable, the Dashboard may be the active
        # view; proceed and let the config-button step decide.
        return True

    def _open_view_config(self) -> bool:
        """Click the 'Configure the active view' toolbar button (label
        '_Configure...', tooltip 'Configure the active view')."""
        return self._click_named(
            ("push button", "toggle button"), "Configure", timeout=8.0
        )

    def _select_gramplet_layout(self) -> bool:
        """Select the 'Gramplet Layout' page in the configure dialog's
        notebook (the config_panel page, grampletpane.py:1643)."""
        return self._click_named("page tab", "Gramplet Layout", timeout=8.0)

    def _number_of_columns_entry(self, timeout: float = 8.0):
        """The single text entry on the Gramplet Layout page (the 'Number of
        Columns' Gtk.Entry; AT-SPI role 'text')."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            entries = [
                n
                for n in self.app.findChildren(lambda n: n.roleName == "text")
                if self._is_usable(n)
            ]
            if len(entries) == 1:
                return entries[0]
            # If several text widgets show, prefer one sitting just right of a
            # 'Number of Columns' label.
            labels = [
                n
                for n in self.app.findChildren(lambda n: n.roleName == "label")
                if self._is_usable(n) and "Number of Columns" in (n.name or "")
            ]
            if labels and entries:
                ly = labels[0].position[1]
                entries.sort(key=lambda e: abs(e.position[1] - ly))
                return entries[0]
            time.sleep(0.3)
        return None

    def _type_value(self, entry, value: str) -> None:
        entry.click()
        keyCombo("<Control>a")
        typeText(value)

    def _process_alive(self) -> bool:
        proc = getattr(type(self), "_proc", None)
        return proc is not None and proc.poll() is None

    def _atspi_responsive(self, timeout: float = 10.0) -> bool:
        """True iff an AT-SPI round-trip completes within `timeout` -- i.e.
        the Gramps main loop is still servicing requests (not frozen building
        thousands of column boxes). The query runs in a daemon thread so a
        frozen app blocks the thread, not the test."""
        result: dict[str, object] = {}

        def probe() -> None:
            try:
                result["frames"] = [
                    f.name
                    for f in self.app.findChildren(lambda n: n.roleName == "frame")
                ]
            except Exception as exc:  # AT-SPI error still means "answered"
                result["err"] = exc

        t = threading.Thread(target=probe, daemon=True)
        t.start()
        t.join(timeout)
        return not t.is_alive()

    def _wait_survival(self, timeout: float) -> bool:
        """Gramps must stay alive for `timeout`s AND remain responsive."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self._process_alive():
                return False  # process died -> the #13864 crash
            time.sleep(0.5)
        return self._process_alive() and self._atspi_responsive()

    # -------------------------------------------------------------------- test
    def test_large_column_count_does_not_crash_or_freeze(self) -> None:
        self.assertTrue(self.tree_opened, "TestTree did not open")

        if not self._open_dashboard():
            self.skipTest("could not switch to the Dashboard view (infra)")
        if not self._open_view_config():
            self.skipTest("could not open 'Configure the active view' (infra)")
        if not self._select_gramplet_layout():
            self.skipTest("could not select the 'Gramplet Layout' config page (infra)")
        entry = self._number_of_columns_entry()
        if entry is None:
            self.skipTest("could not find the 'Number of Columns' entry (infra)")

        # Drive the repro: enter a pathological column count, just as the
        # reporter did with 1000.
        self._type_value(entry, PATHOLOGICAL_COLUMNS)

        survived = self._wait_survival(SURVIVE_TIMEOUT)
        if not survived:
            self._capture_screenshot("bug13864-crash-or-freeze")
        self.assertTrue(
            survived,
            "Gramps crashed or stopped responding after the Dashboard "
            f"'Number of Columns' was set to {PATHOLOGICAL_COLUMNS} "
            "(Mantis 13864: unbounded column_count drives GTK widget "
            "allocation in GrampletPane.set_columns). The fix must clamp the "
            "value to MAX_GRAMPLET_COLUMNS before building column boxes.",
        )


if __name__ == "__main__":
    unittest.main()
