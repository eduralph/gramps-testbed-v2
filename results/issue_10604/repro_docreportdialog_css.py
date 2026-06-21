#!/usr/bin/env python3
#
# Verify-first reproduction probe for issue 10604 (Mantis #10604):
#   "DocReportDialog crashes with KeyError: -1 when the Webstuff plugin is hidden
#    and the CSS combo is therefore empty."
#
# This drives the *production* DocReportDialog.parse_html_frame (the read that
# performed the crashing index `self.css[self.css_combo.get_active()]["filename"]`)
# against the empty-CSS / get_active() == -1 state — exactly the Webstuff-hidden
# scenario the brief names — and reports whether KeyError: -1 still occurs.
#
# It also re-establishes the *meaning* of the bug by exercising the unguarded read
# the v4.2.8 code performed, confirming it DOES raise KeyError: -1 — so the fact
# that production does not is attributable to the guard, not to the absence of a
# trigger.
#
# parse_html_frame builds no widgets (it only reads self.css_combo / self.css /
# self.style_name), so it runs as an unbound function against a light stub — no
# dialog instantiation, headless-safe.
#
# Run against a clean upstream/maintenance/gramps61 worktree, e.g.:
#   GRAMPS_RESOURCES=. python3 results/issue_10604/repro_docreportdialog_css.py
# (needs gramps on PYTHONPATH; the import pulls in Gtk but creates no display
# objects.)

import sys


class _FakeEmptyCombo:
    """A Gtk.ComboBoxText with an empty model: get_active() returns -1."""

    def get_active(self):
        return -1


class _RecordingHandler:
    def __init__(self):
        self.css_filename = "<unset>"

    def set_css_filename(self, value):
        self.css_filename = value


class _FakeOptions:
    def __init__(self):
        self.handler = _RecordingHandler()


class _Stub:
    """Carries only what parse_html_frame reads/writes — no GUI."""

    def __init__(self):
        # Webstuff hidden -> PLUGMAN.process_plugin_data("WEBSTUFF") yields an
        # empty container; the empty combo reports "no active item".
        self.css = {}
        self.css_combo = _FakeEmptyCombo()
        self.style_name = "default"
        self.css_filename = None
        self.options = _FakeOptions()


def main():
    # 1) The historical (v4.2.8, unguarded) read: prove it raises KeyError: -1.
    unguarded_raises = False
    try:
        {}[(-1)]["filename"]  # what self.css[get_active()]["filename"] did
    except KeyError as err:
        unguarded_raises = True
        print("unguarded read  -> KeyError: %s   (the reported crash)" % err)
    if not unguarded_raises:
        print("unguarded read  -> NO ERROR (unexpected)")

    # 2) The production path on maintenance/gramps61.
    # Pin Gtk 3.0 before the gramps.gui import chain (the real app pins it at
    # startup; a bare probe must do it explicitly or a Gtk-4-default host loads
    # the wrong version and the import chain fails on Gtk4-removed enums).
    import gi

    gi.require_version("Gtk", "3.0")
    from gramps.gui.plug.report._docreportdialog import DocReportDialog

    stub = _Stub()
    try:
        DocReportDialog.parse_html_frame(stub)
    except KeyError as err:
        print("production path -> KeyError: %s   *** STILL REPRODUCES ***" % err)
        return 1

    print(
        "production path -> NO CRASH "
        "(css_filename=%r, handler.css_filename=%r)"
        % (stub.css_filename, stub.options.handler.css_filename)
    )
    print(
        "VERIFY-FIRST RESULT: KeyError: -1 does NOT reproduce on maintenance/"
        "gramps61 — the empty / no-active-item CSS state is tolerated."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
