# Brief — issue 6170 / sidebar-filter-copy-shortcut

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** sidebar-filter-copy-shortcut
- **Defect:** In a list view whose sidebar/filter has a focused text entry, pressing
  Ctrl+C does not copy the selected text — it copies the currently selected list object
  to the Gramps clipboard and pops the Clipboard window up. Ctrl+X (cut) works normally
  in the same entry, and Ctrl+V now works (sam888, master), so the remaining live defect
  is Ctrl+C being stolen from the focused entry. Reproduced by fireman_biff (3.4.2),
  user2418 (4.0.2), and sam888 on master ("CTRL+C pops up the Clipboard").
- **Success criterion:** After the fix, with focus in a sidebar/filter text entry that
  has selected text, Ctrl+C copies that text to the system clipboard and does NOT open
  the Gramps Clipboard window; Ctrl+C still copies the selected list object to the Gramps
  clipboard when focus is on the list/tree itself. Demonstrable by the committed AT-SPI
  repro going red pre-fix (Clipboard window appears / text not copied) and green
  post-fix.
- **Invariant to restore:** A view/window-level accelerator must not shadow the standard
  text-editing keystrokes of a focused text-editable widget — the focused editable owns
  Copy/Cut/Paste. (Gramps GUI focus rule; no external canon required — the view's
  copy accelerator is connected on the toplevel window and currently fires regardless of
  which child widget holds focus.) SELF-TEST: the property must fail for a one-branch
  guard that special-cases only the person view — it holds for every list view whose
  sidebar/bottombar carries a text entry.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium
- **Scope:** The navigation-view Ctrl+C handler, connected to the toplevel window,
  consumes the key event and invokes the object-copy even when a text-editable widget in
  the sidebar/filter holds keyboard focus; it should let the focused editable handle the
  keystroke instead. / out of scope: redesigning the Gramps clipboard, the `<PRIMARY>b`
  clipboard shortcut, Ctrl+V/Ctrl+X behaviour (already correct), and the object-copy
  behaviour when the list/tree itself is focused (must be preserved).
- **Repro instruction:** On `maintenance/gramps61`, People view, select a person, click
  into the sidebar/filter "Name" entry, type text, select it, press Ctrl+C: the Clipboard
  window opens and the person (not the text) is copied.
- **Test file:** `engine/interface/test_bug_0006170_sidebar_filter_copy.py` (committed
  AT-SPI/dogtail repro in the testbed, `AddonInterfaceTestCase`/interface base; NOT in
  `patch.diff`). Red on the unpatched worktree, green on the patched one. If Do extracts
  a focus-aware decision seam, production must route through that same seam the test
  drives (principles §3.4), not a parallel copy.
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause: `gramps/gui/views/navigationview.py:481-489` `key_press_handler` invoking
  `call_copy()` on Ctrl+C; handler connected at
  `gramps/gui/views/pageview.py:130` on `self.uistate.window`).
- **New/removed files:** none in gramps — `patch.diff` modifies existing files only; the
  AT-SPI repro ships in the testbed `engine/interface/`, outside gramps' POTFILES scope.
- **Prior-art check (triage cycles):** searched `gramps/gui/views/navigationview.py` on
  `upstream/maintenance/gramps61` — only navigation/black/license churn, no focus/Ctrl+C
  fix; no open/closed PR found on this path. Not already upstream.
- **Mantis:** 6170
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.
