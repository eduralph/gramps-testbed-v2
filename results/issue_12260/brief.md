# Brief — issue 12260 / note-link-new-object-crash

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** note-link-new-object-crash
- **Defect:** Creating a new linked object from the link-edit dialog (e.g. a new Note via
  the ToDo gramplet's link editor) crashes with
  `AttributeError: 'str' object has no attribute 'handle'`. Traceback:
  `editnote.py:save` → `self.callback(self.obj.get_handle())` →
  `editlink.py:_on_new_callback` does `(object_class, "handle", obj.handle)` where `obj`
  is already the **handle string** the callback was passed, not an object — so `.handle`
  on a `str` raises.
- **Success criterion:** Creating a new Note (or other object) through the link-edit
  "new" path completes and inserts the link without raising; the AttributeError no longer
  occurs for that flow.
- **Invariant to restore:** A "new object created" callback receives, and is read as, a
  consistent reference type — the value passed to `_on_new_callback` is treated as the
  kind of reference it actually is (a handle string), not dereferenced as if it were an
  object. (Behavioural / reference-integrity invariant; rationale: the editor's save
  callback emits a handle, so the consumer must consume a handle, not assume an object.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — the bug is at the editnote→editlink callback boundary; the fix
  is local to `editlink.py` but a reviewer must confirm the handle/object contract on both
  sides of the callback.
- **Scope:** the wrong assumption in `gramps/gui/editors/editlink.py` `_on_new_callback`
  that the saved-object callback yields an object with `.handle` rather than a handle
  string. / out of scope: the note editor's save signature, the ToDo gramplet, the link
  format/parsing of existing links.
- **Repro instruction:** Add the ToDo gramplet; use its link-edit feature to create a link
  to a **new** Note (one that does not yet exist) → on save of the new note the dialog
  raises `AttributeError: 'str' object has no attribute 'handle'`.
- **Test file:** gramps/gui/editors/test/editlink_test.py (core, `*_test.py` suffix).
  Drive the production `_on_new_callback` with the handle value the note editor actually
  emits (a `str`) — assert no AttributeError and that the link is built. Exercise the same
  callback the editor invokes, not a copy (principles §3.4). If unreachable headlessly,
  ship `engine/interface/test_bug_12260_note-link-new.py` and mark C4 (unit) unverifiable.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected (test in existing `test/` package; a new module →
  `po/POTFILES.skip`).
- **Prior-art check (triage cycles):** searched by path `gramps/gui/editors/editlink.py`
  on `upstream/maintenance/gramps61` — only license/black/msgctxt commits; no crash fix on
  the new-object callback. No matching fork PR by this path. → unfixed.
- **Mantis:** 12260
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
