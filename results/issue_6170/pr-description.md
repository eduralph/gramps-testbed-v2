# Sidebar/filter text entries now own Ctrl+C instead of list view

## Summary

**User-visible issue:** In list views with sidebar/filter text entries (People, Families, Events, Places, etc.), pressing Ctrl+C when focus is in a text entry copies the *selected list object* to the Gramps Clipboard and opens the Clipboard window, instead of copying the *selected text* to the system clipboard. Ctrl+X (cut) and Ctrl+V (paste) work correctly in the same entry. This prevents standard text-editing copy operations in the sidebar/filter while a list view is open.

**Fix:** Added a focus check before the view-level Ctrl+C handler invokes object-copy. If the focused widget is a text-editable widget (Gtk.Editable or Gtk.TextView), the handler returns False to let the event propagate to the editable, which performs the standard text copy. When the list/tree itself (a Gtk.TreeView, not an editable) holds focus, object-copy is preserved.

## What to look at

The change is in one method in one file:

- `gramps/gui/views/navigationview.py:481–490` — `NavigationView.key_press_handler()` is the window-level Ctrl+C handler.
- Added lines 488–498 (after `if event.keyval == Gdk.KEY_c ...:`): check `self.uistate.window.get_focus()` and return `False` if it's a `Gtk.Editable` or `Gtk.TextView`.

To exercise the fix:
1. Open Gramps and switch to the **People** view.
2. Select a person in the list (so object-copy has a target).
3. Click in the **sidebar/filter "Name" entry** to focus it.
4. Type any text, then select it (e.g. Ctrl+A).
5. Press **Ctrl+C**:
   - *Pre-fix:* The Clipboard window opens and the person is copied (text not copied).
   - *Post-fix:* No Clipboard window; the text is on the system clipboard (paste it elsewhere to verify).
6. Click the person **list/tree row** to focus it, then press **Ctrl+C**:
   - Both before and after: the person is copied to the Gramps Clipboard (object-copy preserved).

## Root cause

`PageView.\_\_init\_\_()` at `pageview.py:131` connects the key_press_handler to the toplevel window:

```python
self.uistate.window.connect("key-press-event", self.key_press_handler)
```

GTK delivers key-press events to the toplevel **before** the focused child widget, so a window-level handler runs first. `NavigationView` overrides this handler and, for Ctrl+C, unconditionally invokes `call_copy()` and consumes the event (`return True` at lines 487–489):

```python
if event.keyval == Gdk.KEY_c and match_primary_mask(event.get_state()):
    self.call_copy()
    return True
```

The `return True` stops propagation, so a focused sidebar/filter entry never sees Ctrl+C. `call_copy()` then opens a `ClipboardWindow` when a list object is selected, which is why the symptom is "Ctrl+C pops up the Clipboard."

## Fix

Before invoking object-copy, check whether the focused widget is a text-editable. If it is, return `False` to let GTK propagate the event to the focused editable, which performs standard text copy to the system clipboard.

The fix (lines 488–498) is:

```python
# Do not shadow the standard Copy of a focused
# text-editable widget (e.g. a sidebar/filter entry).
# The focused editable owns Copy/Cut/Paste, so let the
# key event propagate to it instead of copying the
# selected list object to the Gramps clipboard.  The
# object copy is still performed when the list/tree
# itself (not a text entry) holds the focus.  (Mantis
# #6170)
focus = self.uistate.window.get_focus()
if isinstance(focus, (Gtk.Editable, Gtk.TextView)):
    return False
self.call_copy()
return True
```

This restores the invariant that a window/view-level accelerator must not shadow the standard text-editing keystrokes of a focused text-editable widget — the focused editable owns Copy/Cut/Paste. The fix lives in the shared `NavigationView.key_press_handler`, so it holds for all navigation list views (People, Families, Events, Places, Sources, Citations, Repositories, Media, Notes), not a single view.

## Verified against

**Claim:** The patch lets focused text-editable widgets own Ctrl+C, while list/tree focus still copies the selected object.

**Evidence:**

- **Code path — window-level handler:** `gramps/gui/views/pageview.py:131` connects `key_press_handler` to the toplevel window; `navigationview.py:481–490` is the handler override. The fix (lines 488–498) checks focus type before `call_copy()` at line 499 (unchanged).

- **Code path — focused editable's role:** `Gtk.Editable` and `Gtk.TextView` are the standard GTK text-editable base types; all sidebar/filter entries (e.g. `_searchbar.py` line 57 builds a `Gtk.Entry`) are `Gtk.Editable` instances. Returning `False` lets the toplevel's default key-press handler propagate the event to the focused child.

- **Regression test (AT-SPI/dogtail, committed in testbed):** `engine/interface/test_bug_0006170_sidebar_filter_copy.py` drives the real Gramps process and asserts that no showing top-level frame titled "Clipboard" exists after pressing Ctrl+C in the focused sidebar entry. This test goes **red on the unpatched target** (the Clipboard window appears and the handler consumes Ctrl+C) and **green when the patch is applied** (the editable owns Ctrl+C, no Clipboard window).

- **Object-copy preservation:** The patch preserves the pre-fix behaviour when list/tree focus holds: the check `isinstance(focus, (Gtk.Editable, Gtk.TextView))` returns `False` for a `Gtk.TreeView`, so `call_copy()` (line 499) and `return True` (line 500) execute unchanged, and the object copy to the Gramps Clipboard is performed.

## Test

No core unit test ships in this patch — the behaviour is GUI focus/event-propagation, not headless-testable. Coverage is a committed AT-SPI/dogtail regression in the gramps-testbed harness (not part of this PR), `engine/interface/test_bug_0006170_sidebar_filter_copy.py`, asserting no "Clipboard" window appears after Ctrl+C in a focused sidebar entry. Manual repro: People view → select a person → focus the sidebar Name entry → type and select text → Ctrl+C copies the text to the system clipboard (pre-fix: the Clipboard window opens and the person is copied).

---

Fixes [#6170](https://gramps-project.org/bugs/view.php?id=6170)
