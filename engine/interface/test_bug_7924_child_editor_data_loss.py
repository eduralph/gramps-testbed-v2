"""Regression for Mantis #7924 ("data lost when a parent editor's OK
cascade-closes a child editor with unsaved edits").

Primary editors in Gramps are non-modal, so a parent editor (EditFamily)
and a child editor it spawned (EditPerson, opened via "Add a new person as
the mother") can be open at once. Confirming the *parent* (its OK button)
saves the family and then tears the whole window group down through
``ManagedWindow.close() -> GrampsWindowManager.close_track()``.

The defect: the cascade tore the child editor's window down without
honouring the child's own unsaved-data guard. Even when the child editor's
"Save Changes?" prompt appeared, cancelling it (the user choosing to keep
editing) was ignored -- ``GrampsWindowManager.close_item`` destroyed the
window regardless of the guard's veto -- so the child's unsaved edits were
discarded without acknowledgement.

Path under test:
  gramps/gui/managedwindow.py — ``GrampsWindowManager.close_item`` /
  ``recursive_action`` / ``close_track`` and ``ManagedWindow.close``. The
  fix makes the cascade honour the same veto the direct-close path already
  enforces (``EditPrimary.close`` -> SaveDialog, returns without closing
  when Cancel is chosen).

Repro flow (matches the Mantis report + the brief's repro instruction):
  Relationships view -> Home (set an active person)
    -> "Add a new family with person as parent"  (Family editor opens)
    -> "Add a new person as the mother"           (Person editor opens)
    -> type a given name in the Person editor      (child now dirty)
    -> click the *Family* editor's OK              (parent cascade close)
    -> a "Save Changes?" prompt should guard the child; choosing Cancel
       ("keep editing") must LEAVE THE PERSON EDITOR OPEN.

Assertion — the invariant, stated as behaviour a user can see:
  After confirming the parent and cancelling the child's save prompt, the
  child Person editor must still be open (its unsaved data preserved).

  * Unpatched: the child window is destroyed regardless of the veto, so the
    Person editor vanishes -> this test FAILS (the #7924 symptom).
  * Patched:   the veto is honoured, the Person editor stays open -> PASS.

Note on verifiability: this is an irreducibly GUI-driven, non-modal
multi-window flow. Navigation steps that cannot be driven in the headless
xvfb/AT-SPI session ``skipTest`` with a clear "infra" marker rather than
reporting a false-positive bug; only the final invariant check is a hard
assertion. Per the brief, the automated red/green may land PDCA-UNVERIFIABLE
and the human verifies the prompt in the GUI at sign-off.
"""

from __future__ import annotations

import time
import unittest

from dogtail.rawinput import keyCombo, typeText

from .base import GrampsInterfaceTestCase


ADD_FAMILY_TOOLTIP = "Add a new family with person as parent"
ADD_MOTHER_TOOLTIP = "Add a new person as the mother"

# Window frame titles ("<menu title> - Gramps"); see editfamily.py /
# editperson.py get_menu_title() and gramps/gui/dialog.py SaveDialog.
FAMILY_FRAME_PREFIX = "New Family"
PERSON_FRAME_PREFIX = "New Person"
SAVE_DIALOG_PREFIX = "Save Changes?"

# A given name that is unlikely to collide with any example.gramps data.
CHILD_GIVEN_NAME = "Zzunsavedchild"


class Bug7924ChildEditorDataLossTest(GrampsInterfaceTestCase):
    """Confirming a parent editor must not silently discard a child
    editor's unsaved data via the window-manager close cascade."""

    TREE_NAME = "TestTree"
    # xvfb has no window manager to honour fullscreen(); set a large saved
    # geometry so the relview toolbar + editor dialogs paint fully on
    # screen (mirrors the sizing other interface tests use).
    LAUNCH_CONFIG = (
        "interface.main-window-width:1800",
        "interface.main-window-height:1000",
        # Make sure the "Save Changes?" guard is actually asked; a prior
        # test/session may have persisted interface.dont-ask=True.
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

    def _click_toggle(self, name: str, timeout: float = 10.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for n in self.app.findChildren(
                lambda n, _n=name: n.roleName == "toggle button"
                and (n.name or "") == _n
            ):
                if self._is_clickable(n):
                    n.click()
                    return
            time.sleep(0.3)
        self.skipTest(f"Sidebar toggle button {name!r} not found / not clickable")

    def _click_home(self) -> None:
        for n in self.app.findChildren(
            lambda n: n.roleName == "push button" and (n.name or "") == "Home"
        ):
            if self._is_clickable(n):
                n.click()
                time.sleep(0.6)
                return
        self.skipTest("Toolbar Home button not found")

    def _find_button(self, name_or_sub: str, within=None, timeout: float = 10.0):
        """Find a showing push button whose accessible name equals or
        contains ``name_or_sub``. ``within`` scopes the search to a frame."""
        root_node = within if within is not None else self.app
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            # Prefer an exact-name match, fall back to substring.
            exact = None
            partial = None
            for n in root_node.findChildren(
                lambda n: n.roleName == "push button"
            ):
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

    def _find_frame(self, prefix: str, timeout: float = 12.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            frame = self._frame_showing(prefix)
            if frame is not None:
                return frame
            time.sleep(0.3)
        return None

    def _frame_showing(self, prefix: str):
        for f in self.app.findChildren(
            lambda n: n.roleName in ("frame", "dialog")
        ):
            try:
                if f.showing and (f.name or "").startswith(prefix):
                    return f
            except Exception:
                continue
        return None

    # ---- the test -----------------------------------------------------------

    def test_parent_ok_does_not_silently_discard_child_edits(self) -> None:
        # 1. Relationships view with an active person.
        self._click_toggle("Relationships")
        time.sleep(0.5)
        self._click_home()

        # 2. "Add a new family with person as parent" -> Family editor.
        add_family = self._find_button(ADD_FAMILY_TOOLTIP)
        if add_family is None:
            self.skipTest(
                f"Could not find the {ADD_FAMILY_TOOLTIP!r} button in the "
                "Relationships view — cannot drive the parent/child editor "
                "flow in this session."
            )
        add_family.click()

        family_frame = self._find_frame(FAMILY_FRAME_PREFIX)
        if family_frame is None:
            self.skipTest(
                "Family editor window did not open after "
                f"{ADD_FAMILY_TOOLTIP!r}; cannot exercise the cascade."
            )

        # 3. "Add a new person as the mother" -> Person (child) editor.
        add_mother = self._find_button(ADD_MOTHER_TOOLTIP, within=family_frame)
        if add_mother is None:
            self.skipTest(
                f"Could not find the {ADD_MOTHER_TOOLTIP!r} button in the "
                "Family editor — cannot open the child Person editor."
            )
        add_mother.click()

        person_frame = self._find_frame(PERSON_FRAME_PREFIX)
        if person_frame is None:
            self.skipTest(
                "Child Person editor did not open after "
                f"{ADD_MOTHER_TOOLTIP!r}."
            )

        # 4. Make the child editor dirty: type a given name into its first
        #    editable text field (the "Given" entry is at the top of the
        #    Person editor). Focus it, type, and Tab to commit the change.
        entry = None
        for n in person_frame.findChildren(lambda n: n.roleName == "text"):
            if self._is_clickable(n):
                entry = n
                break
        if entry is None:
            self.skipTest(
                "No editable text field found in the Person editor to type "
                "a name into; cannot make the child dirty."
            )
        try:
            entry.click()
            time.sleep(0.2)
            typeText(CHILD_GIVEN_NAME)
            time.sleep(0.2)
            keyCombo("Tab")
            time.sleep(0.3)
        except Exception as exc:
            self.skipTest(f"Could not type into the Person editor: {exc!r}")

        # 5. Click the *Family* editor's OK button (NOT the Person editor's).
        ok_button = self._find_button("OK", within=family_frame)
        if ok_button is None:
            self.skipTest("Family editor OK button not found.")
        ok_button.click()

        # 6. The cascade should route through the child's save-guard. A
        #    "Save Changes?" prompt appears; choose Cancel ("keep editing").
        save_dialog = self._find_frame(SAVE_DIALOG_PREFIX, timeout=8.0)
        if save_dialog is not None:
            cancel = self._find_button("Cancel", within=save_dialog, timeout=4.0)
            if cancel is None:
                # Fall back to Escape, which maps to the Cancel response.
                keyCombo("Escape")
            else:
                cancel.click()
            time.sleep(0.8)

        # 7. Invariant: cancelling the guard must leave the child Person
        #    editor OPEN with its unsaved data intact. On the unpatched
        #    cascade the window is destroyed regardless of the veto, so the
        #    Person editor vanishes -> this assertion fails (bug #7924).
        deadline = time.monotonic() + 5.0
        person_still_open = False
        while time.monotonic() < deadline:
            if self._frame_showing(PERSON_FRAME_PREFIX) is not None:
                person_still_open = True
                break
            time.sleep(0.3)

        self.assertTrue(
            person_still_open,
            "After confirming the Family editor (OK) with a dirty child "
            "Person editor open and CANCELLING its 'Save Changes?' prompt, "
            "the Person editor was destroyed and its unsaved data discarded "
            "without acknowledgement. This is the Mantis #7924 symptom: the "
            "parent's cascade close (GrampsWindowManager.close_item) tore the "
            "child window down without honouring the child editor's "
            "save-guard veto.",
        )


if __name__ == "__main__":
    unittest.main()
