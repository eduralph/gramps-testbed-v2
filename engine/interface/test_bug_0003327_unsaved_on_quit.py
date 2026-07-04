"""Regression for Mantis #3327 ("unsaved changes in an open editor are lost
without warning when the editor's backing database context is torn down").

A primary-object editor in Gramps (EditPerson, EditFamily, ...) tracks whether
its object has unsaved changes (``EditPrimary.data_has_changed``) and, when its
OWN window is closed with changes pending, shows a "Save Changes?" prompt
(``gramps/gui/dialog.py`` ``SaveDialog``) so the user can save, discard, or
*cancel* the close. That per-editor guard is already in place.

Root cause (maintenance/gramps61)
---------------------------------
The orchestration paths that close an editor's backing *context* -- application
quit (``ViewManager.quit``), family-tree switch (``ViewManager.__open_activate``)
and family-tree close (``ViewManager.close_database``) -- close the database
WITHOUT routing open editors through that guard first. Each open editor is wired
to ``database-changed -> EditPrimary._do_close`` (``editprimary.py``), which
discards the working object *silently*. So switching / closing / quitting with a
dirty editor open loses the change with no prompt, even though closing the same
editor's window WOULD have prompted.

The fix (this bundle)
---------------------
``GrampsWindowManager.close_editors_with_unsaved`` walks the open managed
windows and, for any that expose the editor dirty-tracking contract
(``data_has_changed``) and are dirty, closes them through their own ``close``
method -- reusing the ``data_has_changed`` + ``SaveDialog`` guard. It is called
BEFORE the database is closed in ``ViewManager.quit``, ``__open_activate`` and
``close_database``.

Crucially, ``close_editors_with_unsaved`` RETURNS a boolean: ``False`` when the
user chose *Cancel* on the prompt (the editor is still open/dirty afterwards),
and every caller aborts -- leaving the database open -- when it gets ``False``.
Without that abort signal the callers would tear down the database *underneath*
the still-open editor even after the user pressed Cancel, which is itself a
data-loss bug (this is the defect the first iteration of the fix missed).

Repro flow (the brief's Success criterion, driven at the family-tree-close door)
--------------------------------------------------------------------------------
  People view -> "Add a new person"            (a Person editor opens)
    -> type a given name (the editor is now dirty, unsaved)
    -> refocus the main window and press Ctrl+W (close the family tree,
       ``viewmanager.close_database`` -- the same door the switch/quit paths use)

Two assertions, both behaviour a user can see:

  A. The dirty editor must be offered a "Save Changes?" prompt before its
     database is torn down (the Success criterion: prompt instead of silent
     discard).

       * Unpatched: ``close_database`` closes the DB, the editor's
         ``database-changed`` handler ``_do_close`` runs and the change is
         discarded with no dialog -> no "Save Changes?" frame ever appears ->
         this assertion FAILS (the test is RED).
       * Patched:   ``close_editors_with_unsaved`` runs first, the dirty
         editor's ``close`` shows the modal "Save Changes?" prompt (blocking
         the DB close) -> the frame appears.

  B. Choosing *Cancel* on that prompt must ABORT the close and leave the
     database (and the still-open editor) intact -- not tear the database down
     underneath the editor.

       * A fix that shows the prompt but ignores the Cancel outcome (the first
         iteration) proceeds to ``no_database()`` anyway; the editor's
         ``database-changed -> _do_close`` then destroys the editor window ->
         after Cancel the editor frame is GONE -> this assertion FAILS.
       * This bundle's fix returns ``False`` from ``close_editors_with_unsaved``
         on Cancel and ``close_database`` bails out -> the editor window is
         still showing after Cancel.

``close_database`` (Ctrl+W) is used as the trigger because it exercises the very
same ``close_editors_with_unsaved`` orchestration seam that ``quit`` and the
family-tree switch route through, and it is observable headlessly (the process
survives the prompt and the Cancel), whereas driving ``quit`` tears down the
AT-SPI connection the moment the prompt is answered.

Note on verifiability: this is an irreducibly GUI-driven, non-modal multi-window
flow. Navigation steps that cannot be driven in the headless xvfb/AT-SPI session
``skipTest`` with a clear "infra" marker rather than reporting a false result;
only the two invariant checks (prompt appears; Cancel keeps the editor open) are
hard assertions.
"""

from __future__ import annotations

import time
import unittest

from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase


ADD_PERSON_TOOLTIP = "Add a new person"

# Window frame titles ("<menu title> - Gramps"); see editperson.py
# get_menu_title() ("New Person" / "New Person: <name>") and
# gramps/gui/dialog.py SaveDialog ("Save Changes?").
PERSON_FRAME_PREFIX = "New Person"
SAVE_DIALOG_PREFIX = "Save Changes?"

# Buttons on the SaveDialog; see the ``savedialog`` object in
# gramps/gui/glade/dialog.glade: "Close _without saving" (discard),
# "_Cancel" (abort the close), "_Save". Accessible names drop the "_"
# mnemonic marker.
DISCARD_BTN_SUB = "without saving"
CANCEL_BTN_SUB = "Cancel"

# A given name unlikely to collide with any example.gramps data.
GIVEN_NAME = "Zzunsavedquit"


class Bug3327UnsavedOnQuitTest(GrampsInterfaceTestCase):
    """Closing an editor's backing database context (quit / family-tree
    change / close) must offer the editor's save/discard prompt for unsaved
    changes, and must honour *Cancel* on that prompt by aborting the close --
    not discard the changes silently, and not tear the database down under the
    still-open editor when the user cancels."""

    TREE_NAME = "TestTree"
    # xvfb has no window manager to honour fullscreen(); set a large saved
    # geometry so the toolbar + editor dialogs paint fully on screen.
    LAUNCH_CONFIG = (
        "interface.main-window-width:1800",
        "interface.main-window-height:1000",
        # The "Save Changes?" guard is gated by interface.dont-ask; a prior
        # test/session may have persisted it True. Force it False so the
        # prompt is actually asked.
        "interface.dont-ask:False",
    )

    # ---- generic helpers ----------------------------------------------------

    @staticmethod
    def _is_clickable(node) -> bool:
        try:
            if not node.showing:
                return False
            pos = node.position
            size = node.size
        except Exception:
            return False
        return pos[0] >= 0 and pos[1] >= 0 and size[0] > 0 and size[1] > 0

    def _click_toggle(self, name: str, timeout: float = 10.0) -> bool:
        """Click a sidebar category toggle button (e.g. "People"). Returns
        True if it was clicked. Also serves to move keyboard focus back to
        the main Gramps window."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n, _n=name: n.roleName == "toggle button"
                and (n.name or "") == _n
            ):
                if self._is_clickable(n):
                    n.click()
                    return True
            time.sleep(0.3)
        return False

    def _find_button(self, name_or_sub: str, within=None, timeout: float = 10.0):
        """Find a showing push button whose accessible name equals or
        contains ``name_or_sub``. ``within`` scopes the search to a frame."""
        root_node = within if within is not None else self.app
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            exact = None
            partial = None
            for n in root_node.findChildren(lambda n: n.roleName == "push button"):
                if not self._is_clickable(n):
                    continue
                nm = n.name or ""
                if nm == name_or_sub:
                    exact = n
                    break
                if name_or_sub in nm and partial is None:
                    partial = n
            hit = exact or partial
            if hit is not None:
                return hit
            time.sleep(0.3)
        return None

    def _frame_showing(self, prefix: str):
        for f in self.app.findChildren(lambda n: n.roleName in ("frame", "dialog")):
            try:
                if f.showing and (f.name or "").startswith(prefix):
                    return f
            except Exception:
                continue
        return None

    def _find_frame(self, prefix: str, timeout: float = 12.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            frame = self._frame_showing(prefix)
            if frame is not None:
                return frame
            time.sleep(0.3)
        return None

    def _frame_gone(self, prefix: str, timeout: float = 8.0) -> bool:
        """True if no showing frame with ``prefix`` remains within timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._frame_showing(prefix) is None:
                return True
            time.sleep(0.3)
        return False

    # ---- the test -----------------------------------------------------------

    def test_close_tree_prompts_then_cancel_aborts(self) -> None:
        self.assertTrue(self.tree_opened, "TestTree did not open")

        # 1. People view (has the "Add a new person" toolbar button).
        if not self._click_toggle("People"):
            self.skipTest("People category toggle not found/clickable (infra)")
        time.sleep(0.5)

        # 2. Open a new Person editor.
        add_person = self._find_button(ADD_PERSON_TOOLTIP)
        if add_person is None:
            self.skipTest(
                f"Could not find the {ADD_PERSON_TOOLTIP!r} button in the People "
                "view — cannot open a Person editor (infra)."
            )
        add_person.click()

        person_frame = self._find_frame(PERSON_FRAME_PREFIX)
        if person_frame is None:
            self.skipTest(
                f"Person editor did not open after {ADD_PERSON_TOOLTIP!r} (infra)."
            )

        # 3. Make the editor dirty: type a given name into its first editable
        #    text field (the "Given" entry) and Tab to commit the change onto
        #    the working object.
        entry = None
        for n in person_frame.findChildren(lambda n: n.roleName == "text"):
            if self._is_clickable(n):
                entry = n
                break
        if entry is None:
            self.skipTest(
                "No editable text field found in the Person editor to type a "
                "name into; cannot make the editor dirty (infra)."
            )
        try:
            entry.click()
            time.sleep(0.2)
            typeText(GIVEN_NAME)
            time.sleep(0.2)
            keyCombo("Tab")
            time.sleep(0.3)
        except Exception as exc:
            self.skipTest(f"Could not type into the Person editor: {exc!r} (infra)")

        # Guard: a "Save Changes?" prompt must NOT already be up, else the
        # assertion below could pass vacuously.
        if self._frame_showing(SAVE_DIALOG_PREFIX) is not None:
            self.skipTest("'Save Changes?' prompt already showing before close (infra)")

        # 4. Move keyboard focus back to the main window (the Ctrl+W
        #    close-database accelerator lives on the main window, not the
        #    editor), leaving the non-modal editor open and dirty.
        if not self._click_toggle("People"):
            self.skipTest("Could not refocus the main window before Ctrl+W (infra)")
        time.sleep(0.4)

        # 5. Close the family tree: Ctrl+W -> viewmanager.close_database. This
        #    is the same orchestration seam (close_editors_with_unsaved) that
        #    the quit and family-tree-switch paths route through.
        keyCombo("<Control>w")

        # 6. Invariant A (Success criterion): the dirty editor must be offered a
        #    "Save Changes?" prompt before its database is torn down. On the
        #    unpatched tree close_database discards the editor via its
        #    database-changed -> _do_close handler with no prompt, so this frame
        #    never appears (bug #3327) and the test is RED here.
        save_dialog = self._find_frame(SAVE_DIALOG_PREFIX, timeout=8.0)
        self.assertIsNotNone(
            save_dialog,
            "After making a Person editor dirty and closing the family tree "
            "(Ctrl+W -> close_database), no 'Save Changes?' prompt appeared — "
            "the unsaved change was discarded silently when the database was "
            "torn down under the open editor (the Mantis #3327 symptom).",
        )

        # 7. Invariant B (Cancel must abort): press *Cancel* on the prompt. The
        #    close must be aborted and the editor left open — the database must
        #    NOT be torn down underneath it. A fix that shows the prompt but
        #    ignores the Cancel outcome proceeds to no_database(), whose
        #    database-changed signal destroys the editor window via _do_close,
        #    so after Cancel the editor frame would be gone.
        cancel_btn = self._find_button(
            CANCEL_BTN_SUB, within=save_dialog, timeout=4.0
        )
        if cancel_btn is None:
            self.skipTest(
                "'Save Changes?' prompt appeared but its Cancel button was not "
                "found/clickable; cannot verify the Cancel-abort path (infra)."
            )
        cancel_btn.click()
        time.sleep(0.6)

        # The prompt itself must be dismissed by Cancel...
        self.assertTrue(
            self._frame_gone(SAVE_DIALOG_PREFIX, timeout=6.0),
            "The 'Save Changes?' prompt was still showing after clicking Cancel.",
        )
        # ...and, decisively, the editor window must STILL be open — proof the
        # database was not closed underneath it when the user cancelled.
        self.assertIsNotNone(
            self._frame_showing(PERSON_FRAME_PREFIX),
            "After clicking Cancel on the 'Save Changes?' prompt, the Person "
            "editor window was gone — the family-tree close was NOT aborted and "
            "the database was torn down under the still-open editor (Mantis "
            "#3327 Cancel-path data loss).",
        )


if __name__ == "__main__":
    unittest.main()
