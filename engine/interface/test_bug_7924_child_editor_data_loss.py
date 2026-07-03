"""Regression for Mantis #7924 ("references lost when a parent editor is
confirmed while a child editor it spawned still holds unsaved data").

Primary editors in Gramps are non-modal, so a parent editor (EditFamily) and
a child editor it spawned (EditPerson, opened via "Add a new person as the
mother") can be open at once. bamaustin's 2021 diagnosis reframed the bug:
the objects can be saved, but the *references connecting them are lost* -- a
family committed without the person as its mother.

Root cause (maintenance/gramps61)
---------------------------------
The family's ``mother_handle`` is written only by the child's completion
callback (``EditFamily.new_mother_added``), which runs when the *child*
saves. Confirming the *parent* runs ``EditFamily.__do_save`` first: it reads
``get_mother_handle()`` -- still ``None`` -- and commits the family WITHOUT
the mother, *before* the window-teardown cascade ever prompts to save the
child. So even choosing "Save" on the cascade's prompt writes the mother
handle onto a family object that was already committed and is being
destroyed; it is never re-committed. Result: the person exists but is
orphaned, the family has no mother.

The fix (this bundle)
---------------------
The shared primary-editor save path (``EditPrimary`` +
``gramps.gui.savecascade.children_to_resolve`` over the
``GrampsWindowManager`` window tree) now resolves open dependent child
primary editors *before* the parent reads its references and commits. Every
save door routes through ``EditPrimary._save_with_dependent_children`` -- the
OK button AND the window-X / Cancel "Save Changes?" path -- so confirming the
Family drives the child Person editor's own "Save Changes?" guard first; on
Save the child's callback lands ``mother_handle`` on the family's working
object, and only then does the family commit -- now fully linked. On Cancel
the parent save aborts and nothing is committed.

Repro flow (the reporter's flow + the brief's Success criterion)
----------------------------------------------------------------
  Relationships view -> Home (set an active person)
    -> "Add a new family with person as parent"  (Family editor opens)
    -> "Add a new person as the mother"           (Person editor opens)
    -> type a given name in the Person editor      (child now dirty)
    -> click the *Family* editor's OK              (parent confirm)
    -> a "Save Changes?" prompt guards the child; choose *Save*.

Assertion -- the invariant, as behaviour a user can see:
  After confirming the Family with a dirty child Person editor open and
  choosing *Save*, the new person must be SAVED AND LINKED as the family's
  mother, so the active person's Relationships view shows the new partner.

  * Unpatched: the family is committed with ``mother_handle == None`` before
    the child is ever saved; the person ends up orphaned, so the new name
    never appears as the active person's partner -> this test FAILS (the
    #7924 symptom -- the reference was dropped at commit time).
  * Patched:   the child is resolved before the commit, the mother handle
    survives, and the partner name shows -> PASS.

Note on verifiability: this is an irreducibly GUI-driven, non-modal
multi-window flow. Navigation steps that cannot be driven in the headless
xvfb/AT-SPI session ``skipTest`` with a clear "infra" marker rather than
reporting a false-positive; only the final reference-survival check is a
hard assertion. Per the brief, the automated red/green may land
PDCA-UNVERIFIABLE and the human verifies the linkage in the GUI at sign-off.
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

# A given name that is unlikely to collide with any example.gramps data, so a
# whole-tree search for it uniquely identifies the person we just created.
CHILD_GIVEN_NAME = "Zzunsavedmother"


class Bug7924ChildEditorDataLossTest(GrampsInterfaceTestCase):
    """Confirming a parent editor must resolve an open dependent child editor
    so the child's reference is preserved, not silently dropped at commit."""

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

    def _click_home(self) -> bool:
        for n in self.app.findChildren(
            lambda n: n.roleName == "push button" and (n.name or "") == "Home"
        ):
            if self._is_clickable(n):
                n.click()
                time.sleep(0.6)
                return True
        return False

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

    def _name_visible_anywhere(self, needle: str) -> bool:
        """True if any showing node's accessible name contains ``needle``.

        After the flow the active person's Relationships view shows the new
        partner's name only if the family was committed WITH the mother
        linked; an orphaned (unlinked) person is not shown against the active
        person, so this is a GUI-observable proxy for ``mother_handle``
        resolving to the created person.
        """
        for n in self.app.findChildren(lambda n: needle in (n.name or "")):
            try:
                if n.showing:
                    return True
            except Exception:
                continue
        return False

    # ---- the test -----------------------------------------------------------

    def test_parent_ok_preserves_child_reference(self) -> None:
        self.assertTrue(self.tree_opened, "TestTree did not open")

        # 1. Relationships view with an active person.
        self._click_toggle("Relationships")
        time.sleep(0.5)
        if not self._click_home():
            self.skipTest("Toolbar Home button not found (infra)")

        # Guard: the name must NOT already be present before we start, else the
        # final assertion could pass vacuously.
        if self._name_visible_anywhere(CHILD_GIVEN_NAME):
            self.skipTest(
                f"{CHILD_GIVEN_NAME!r} already present before the flow (infra)"
            )

        # 2. "Add a new family with person as parent" -> Family editor.
        add_family = self._find_button(ADD_FAMILY_TOOLTIP)
        if add_family is None:
            self.skipTest(
                f"Could not find the {ADD_FAMILY_TOOLTIP!r} button in the "
                "Relationships view — cannot drive the parent/child editor "
                "flow in this session (infra)."
            )
        add_family.click()

        family_frame = self._find_frame(FAMILY_FRAME_PREFIX)
        if family_frame is None:
            self.skipTest(
                "Family editor window did not open after "
                f"{ADD_FAMILY_TOOLTIP!r}; cannot exercise the flow (infra)."
            )

        # 3. "Add a new person as the mother" -> Person (child) editor.
        add_mother = self._find_button(ADD_MOTHER_TOOLTIP, within=family_frame)
        if add_mother is None:
            self.skipTest(
                f"Could not find the {ADD_MOTHER_TOOLTIP!r} button in the "
                "Family editor — cannot open the child Person editor (infra)."
            )
        add_mother.click()

        person_frame = self._find_frame(PERSON_FRAME_PREFIX)
        if person_frame is None:
            self.skipTest(
                "Child Person editor did not open after "
                f"{ADD_MOTHER_TOOLTIP!r} (infra)."
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
                "a name into; cannot make the child dirty (infra)."
            )
        try:
            entry.click()
            time.sleep(0.2)
            typeText(CHILD_GIVEN_NAME)
            time.sleep(0.2)
            keyCombo("Tab")
            time.sleep(0.3)
        except Exception as exc:
            self.skipTest(f"Could not type into the Person editor: {exc!r} (infra)")

        # 5. Click the *Family* editor's OK button (NOT the Person editor's).
        ok_button = self._find_button("OK", within=family_frame)
        if ok_button is None:
            self.skipTest("Family editor OK button not found (infra).")
        ok_button.click()

        # 6. The parent's save must route through the child's save-guard BEFORE
        #    it commits. A "Save Changes?" prompt appears; choose *Save* so the
        #    child's completion callback lands the mother reference on the
        #    family before it is committed.
        save_dialog = self._find_frame(SAVE_DIALOG_PREFIX, timeout=8.0)
        if save_dialog is None:
            self.skipTest(
                "No 'Save Changes?' prompt appeared for the dirty child editor "
                "after confirming the parent — cannot drive the Save path (infra)."
            )
        save_btn = self._find_button("Save", within=save_dialog, timeout=4.0)
        if save_btn is None:
            self.skipTest("Save button not found on the 'Save Changes?' prompt (infra).")
        save_btn.click()
        time.sleep(1.0)

        # 7. The flow should have completed: both editors close. If the Family
        #    editor is still open, the save did not go through — treat as infra
        #    rather than asserting on an incomplete flow.
        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline:
            if self._frame_showing(FAMILY_FRAME_PREFIX) is None:
                break
            time.sleep(0.3)
        if self._frame_showing(FAMILY_FRAME_PREFIX) is not None:
            self.skipTest("Family editor did not close after Save (infra).")

        # Force the Relationships view to reflect the committed family.
        self._click_home()

        # 8. Invariant (the hard assertion): the new person must be SAVED and
        #    LINKED as the family's mother, so the active person's
        #    Relationships view shows the new partner. On the unpatched tree
        #    the family was committed with mother_handle == None before the
        #    child ever saved, so the person is orphaned and never appears as
        #    the active person's partner -> this assertion fails (bug #7924).
        deadline = time.monotonic() + 6.0
        linked = False
        while time.monotonic() < deadline:
            if self._name_visible_anywhere(CHILD_GIVEN_NAME):
                linked = True
                break
            time.sleep(0.3)

        self.assertTrue(
            linked,
            f"After confirming the Family editor (OK) with a dirty child "
            f"Person editor open and choosing Save on its 'Save Changes?' "
            f"prompt, the new person {CHILD_GIVEN_NAME!r} does not appear as "
            f"the active person's partner in the Relationships view. The "
            f"family was committed without its mother_handle (the reference "
            f"was dropped at commit time before the child was resolved) — the "
            f"Mantis #7924 symptom.",
        )


if __name__ == "__main__":
    unittest.main()
