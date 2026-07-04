"""Injected via PYTHONPATH by ``scripts/try-app.sh`` — tags GTK window titles with the
bundle currently under ``pdca try``, so the running GUI *visibly* confirms it is the
PATCHED build (and which bundle), not the clean base.

Launcher-side only: this lives outside the target checkout and is added to the container's
PYTHONPATH, so it never appears in the worktree or the ``patch.diff`` under test. It is a
no-op unless ``PDCA_TRY_TAG`` is set, and it is wrapped so a failure can never block the app
launch (advisory, like ``pdca try`` itself). ``sitecustomize`` is auto-imported by the
``site`` module at interpreter startup, before gramps' own code runs.
"""

import os

_TAG = os.environ.get("PDCA_TRY_TAG", "").strip()

if _TAG:
    try:
        import gi

        try:
            gi.require_version("Gtk", "3.0")  # match gramps; avoid the version warning
        except ValueError:
            pass
        from gi.repository import Gtk

        _orig_set_title = Gtk.Window.set_title

        def _tagged_set_title(self, title, _o=_orig_set_title, _t=_TAG):
            # Append the tag once; gramps updates the main window title dynamically (tree
            # name), so re-tag on each call but never stack duplicates.
            try:
                base = title or ""
                if _t not in base:
                    title = f"{base}   —   {_t}" if base else _t
            except Exception:
                pass
            return _o(self, title)

        Gtk.Window.set_title = _tagged_set_title
    except Exception:
        # The banner is advisory: never let it break the launch.
        pass
