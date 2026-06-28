"""E2E verification for Mantis bug 12932 (2-Way Fan chart startup crash).

Mantis 12932: with "Remember last view displayed" enabled, the last view set
to the **2-Way Fan** chart, and that view's background configured to
**Time period based gradient**, Gramps fails to start::

    File ".../gramps/gui/widgets/fanchart2way.py", line ..., in main
        self.fan.reset()
    File ".../gramps/gui/widgets/fanchart2way.py", line ..., in reset
        self.prepare_background_box(self.generations_asc + ...)
    File ".../gramps/gui/widgets/fanchart.py", line ..., in prepare_background_box
        self.set_userdata_timeperiod(person, userdata)
    File ".../gramps/gui/widgets/fanchart.py", line ..., in set_userdata_timeperiod
        userdata.append(period)
        ^^^^^^^^^^^^^^^
    AttributeError: 'NoneType' object has no attribute 'append'

Root cause (== Mantis 13395, a different background setting selects the same
faulty path): ``FanChartWidget.set_generations`` /
``FanChart2WayWidget.set_generations`` initialised each ``self.data[i]`` slot
with the userdata element left as ``None``.  At startup there is no active
("root") person yet, so ``_fill_data_structures`` short-circuits
(``if not self.rootpersonh: return``) and never replaces the placeholder slots.
``prepare_background_box``'s BACKGROUND_GRAD_PERIOD path then calls
``set_userdata_timeperiod(person, userdata)`` -> ``userdata.append(period)`` on
that ``None`` and crashes.

The fix (upstream ``maintenance/gramps61`` commit 0f3830a6e8, "Fix fan chart
crash at startup with age-gradient background", Fixes #13395) gives every slot
its own empty userdata list at init time
(``gramps/gui/widgets/fanchart.py`` set_generations,
``gramps/gui/widgets/fanchart2way.py`` set_generations), so the period/age
gradient append paths can never hit ``None`` regardless of whether
``_fill_data_structures`` short-circuits.

This repro restores exactly the reported startup scenario:

  * ``preferences.use-last-view = True`` and
    ``preferences.last-view = fanchart2wayview`` (set via the launch ``-c``
    flags) make Gramps re-open on the 2-Way Fan chart at startup, just as
    "Remember last view displayed" + last-view = 2-Way Fan would; and
  * the per-view config file ``Ancestry_fanchart2wayview.ini`` is seeded with
    ``[interface] fanview-background = 7`` (BACKGROUND_GRAD_PERIOD), i.e.
    "Time period based gradient" -- this setting lives in the view's own
    ConfigManager (``ident = "Ancestry_fanchart2wayview"``,
    ``pageview.PageView.init_config``), not in the global gramps.ini, so it is
    not reachable through the launcher's ``-c`` flags and must be seeded on
    disk before launch.

On the UNPATCHED widget the startup view-switch raises the AttributeError,
which Gramps' uncaught-exception handler logs to stderr ("Unhandled exception"
+ the fanchart traceback) and surfaces as an "Error Report" window; this test
fails until the slot-userdata fix is present.  On the PATCHED (current upstream)
widget Gramps starts cleanly on the 2-Way Fan chart with no such exception, and
this test passes -- which is the verification evidence that Mantis 12932 is
fixed.
"""

from __future__ import annotations

import os
import subprocess
import time
import unittest

from .base import GrampsInterfaceTestCase

# BACKGROUND_GRAD_PERIOD == 7 (gramps/gen/const.py); "Time period based
# gradient" in the 2-Way Fan view's Configure > Background options.
BACKGROUND_GRAD_PERIOD = 7

# The 2-Way Fan view: id "fanchart2wayview", category ("Ancestry", "Charts")
# (gramps/plugins/view/view.gpr.py).  Its per-view ConfigManager ident is
# "<category>_<id>" == "Ancestry_fanchart2wayview"
# (gramps/gui/views/pageview.py PageView.ident / init_config).
FAN2WAY_VIEW_ID = "fanchart2wayview"
FAN2WAY_CONFIG_IDENT = "Ancestry_fanchart2wayview"

# The crash signature this bug produces in Gramps' stderr (the uncaught-exception
# handler logs the traceback there in addition to the GUI Error Report window).
CRASH_TEXT = "'NoneType' object has no attribute 'append'"


class FanChart2WayStartupTest(GrampsInterfaceTestCase):
    """Restore the 2-Way Fan chart (time-period gradient) as the last view and
    assert Gramps starts without the Mantis 12932 AttributeError."""

    TREE_NAME = "TestTree"

    # Restore the 2-Way Fan view at startup, exactly as "Remember last view
    # displayed" + last-view = 2-Way Fan does (both keys are in the global
    # gramps config, so -c reaches them).
    LAUNCH_CONFIG = (
        "preferences.use-last-view:True",
        "preferences.last-view:" + FAN2WAY_VIEW_ID,
    )

    # ---- per-view config seeding ------------------------------------------

    @classmethod
    def _gramps_version_dir(cls) -> str:
        """Gramps' versioned config directory (where the per-view .ini lives).

        Asked of Gramps itself in a subprocess -- the same technique the
        interface runner uses for USER_PLUGINS -- so the path is whatever this
        Gramps build resolves (XDG / GRAMPSHOME / version), never guessed.
        """
        out = subprocess.check_output(
            [
                "python3",
                "-c",
                "from gramps.gen.const import VERSION_DIR; print(VERSION_DIR)",
            ],
            text=True,
        )
        return out.strip()

    @classmethod
    def _seed_fan_background(cls) -> None:
        """Write the 2-Way Fan view's per-view .ini so its background is the
        time-period gradient before Gramps reads it at view load.

        ``PageView.init_config`` registers a ConfigManager at
        ``<config_dir>/Ancestry_fanchart2wayview.ini`` and ``init()`` loads it
        if it exists, so seeding the file pre-launch makes the view start with
        BACKGROUND_GRAD_PERIOD selected.
        """
        vdir = cls._gramps_version_dir()
        os.makedirs(vdir, exist_ok=True)
        ini = os.path.join(vdir, FAN2WAY_CONFIG_IDENT + ".ini")
        with open(ini, "w", encoding="utf-8") as fh:
            fh.write(";; Gramps key file\n")
            fh.write("[interface]\n")
            fh.write("fanview-background=%d\n" % BACKGROUND_GRAD_PERIOD)
        cls._seeded_ini = ini

    @classmethod
    def setUpClass(cls) -> None:
        # Seed the period-gradient background BEFORE launching Gramps; the base
        # setUpClass starts the process and waits for the TestTree frame, by
        # which point the startup fan-chart build has already run.
        cls._seed_fan_background()
        super().setUpClass()

    # ---- evidence helpers --------------------------------------------------

    @classmethod
    def _stderr_text(cls) -> str:
        """Everything Gramps has written to stderr so far.

        base.py launches Gramps with stderr redirected to ``cls._stderr_file``
        (a tempfile, kept open until tearDownClass); read it without disturbing
        the write position.
        """
        tmp = getattr(cls, "_stderr_file", None)
        if tmp is None:
            return ""
        try:
            tmp.flush()
            pos = tmp.tell()
            tmp.seek(0)
            data = tmp.read()
            tmp.seek(pos)
        except Exception:
            return ""
        return data.decode("utf-8", errors="replace")

    def _drawing_area_showing(self) -> bool:
        """True once the fan chart canvas is present.

        ``FanChartBaseWidget`` is a ``Gtk.DrawingArea``
        (gramps/gui/widgets/fanchart.py), so a showing "drawing area" confirms
        the 2-Way Fan view actually loaded -- the guard that keeps a green
        result honest (a config that silently failed to restore the fan view
        would leave Gramps on the People tree-table view, with no drawing
        area, and fail here rather than pass vacuously).
        """
        for n in self.app.findChildren(lambda n: n.roleName == "drawing area"):
            try:
                if n.showing:
                    return True
            except Exception:
                continue
        return False

    def _error_report_window(self):
        """Gramps' uncaught-exception 'Error Report' window, if surfaced."""
        for d in self.app.findChildren(
            lambda n: n.roleName in ("dialog", "frame", "window")
        ):
            try:
                if d.showing and (d.name or "").startswith("Error Report"):
                    return d
            except Exception:
                continue
        return None

    # ---- the test ----------------------------------------------------------

    def test_2way_fanchart_restores_at_startup_without_crash(self) -> None:
        self.assertTrue(
            self.tree_opened,
            "TestTree did not open -- cannot exercise the 2-Way Fan startup path.",
        )

        # Positive guard: the fan chart canvas must appear, proving the 2-Way
        # Fan view was actually restored and its startup build ran (the canvas
        # is created before reset()/main(), so it appears on both the unpatched
        # and patched widgets; only the stderr signature below distinguishes
        # the crash).
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not self._drawing_area_showing():
            time.sleep(0.3)
        self.assertTrue(
            self._drawing_area_showing(),
            "The 2-Way Fan view never produced a drawing-area canvas; the "
            "startup fan-chart path was not exercised (last-view restore did "
            "not select fanchart2wayview?), so the result would be vacuous.",
        )

        stderr = self._stderr_text()
        err_win = self._error_report_window()
        crashed = (CRASH_TEXT in stderr and "fanchart" in stderr.lower()) or (
            err_win is not None
        )
        self.assertFalse(
            crashed,
            "Mantis 12932 reproduced: restoring the 2-Way Fan chart at startup "
            "with the time-period gradient background raised AttributeError: "
            "'NoneType' object has no attribute 'append' in "
            "fanchart.set_userdata_timeperiod -- userdata was None because "
            "set_generations left the data slots' userdata unset and "
            "_fill_data_structures short-circuited with no root person at "
            "startup. The slot-userdata fix (upstream 0f3830a6e8) is missing.\n"
            f"crash signature in stderr: {CRASH_TEXT in stderr}\n"
            f"Error Report window present: {err_win is not None}\n"
            f"stderr tail:\n{stderr[-2000:]}",
        )


if __name__ == "__main__":
    unittest.main()
