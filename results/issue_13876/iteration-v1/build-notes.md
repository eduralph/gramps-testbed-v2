# Build notes — issue 13876 / citation-tree-view-delete-noop

## Root cause (traced, not recalled)

The Citation Tree view (`CitationTreeView`, `gramps/plugins/view/citationtreeview.py:76`)
has no `remove`/delete method of its own — it inherits the delete path from
`LibSourceView` (`gramps/plugins/lib/libsourceview.py:31`), which is placed first in
the MRO (`class CitationTreeView(LibSourceView, ListView)`). The toolbar/menu
`win.Remove` action calls `LibSourceView.remove(...)` (libsourceview.py:42), which
classifies each selected handle as `"Source"` or `"Citation"` (libsourceview.py:48-52)
and routes to `remove_object_from_handle` (libsourceview.py:55).

That handler is where it breaks. After cleaning up back-references it ended with a
**hardcoded**:

```python
# and delete the source
self.dbstate.db.remove_source(handle, trans)   # libsourceview.py:102 (pre-fix)
```

regardless of `obj_type`. So for a selected **Citation** row the code cleaned the
citation's back-refs and then called `remove_source(<citation_handle>)` — which does
nothing to a citation (the handle is not a source handle). The citation survived. A
Source row deletes correctly because its branch (libsourceview.py:71-96) deletes the
child citations explicitly, then `remove_source` removes the matching source — which
is also why a citation only vanished when its parent Source was co-selected.

Contrast the flat Citation list view: it uses the **base** `ListView.remove_object_from_handle`
(`gramps/gui/views/listview.py:712`), which deletes via
`self.dbstate.db.method("remove_%s", obj_type)(...)` — type-correct, so the list view
always removes the citation. The tree-view override diverged from that contract.

## Fix

`gramps/plugins/lib/libsourceview.py:101-102` — replace the hardcoded `remove_source`
with the type-dispatched call already used by the base class:

```python
# and delete the object itself (a Source or a Citation)
self.dbstate.db.method("remove_%s", obj_type)(handle, trans)
```

For `obj_type == "Source"` this is identical behaviour to before (`remove_source`); for
`obj_type == "Citation"` it now calls `remove_citation`, removing the citation. This
restores the brief's invariant — the delete affects the same record regardless of view
mode — with the smallest change that puts the override back in line with the base
handler. One line, no new control flow.

## Alternatives considered / rejected

- **Delete the override entirely and let `CitationTreeView` use the base
  `ListView.remove_object_from_handle`.** Rejected: the override exists for a real
  reason — deleting a *Source* must cascade-delete its child citations and run the
  progress bar (libsourceview.py:71-96), which the base handler does not do. Removing
  it would regress Source-row deletion (explicitly out of scope). The override is
  correct for Source; only its final delete line was type-wrong.
- **Add a `Citation` branch mirroring the Source branch.** Unnecessary: a citation has
  no children to cascade, so the generic back-ref cleanup loop already does the right
  prep; only the terminal `remove_*` call needed to become type-aware. A separate
  branch would be more code (≈4 lines) for no behavioural difference.

## Test

`gramps/plugins/view/test/citationtreeview_test.py` (new). It exercises the **production**
handler `LibSourceView.remove_object_from_handle` directly — `LibSourceView` is a plain
mixin (no `gi`/`gramps.gui` import; libsourceview.py only imports
`gramps.gen.errors.HandleError`), so the test loads under the headless C4 runner without
a display/D-Bus. It builds an in-memory sqlite db, adds a Source + a Citation that
references it, calls the handler with `obj_type="Citation"`, and asserts the citation is
gone (and the parent source — out of scope — is untouched).

The test routes through the same method the GUI delete action invokes (the
`win.Remove` → `LibSourceView.remove` → `remove_object_from_handle` path), not a copy.
Pre-fix it fails (citation still present); post-fix it passes. Verified via
`run-verify.sh`: green-with-fix=PASS / red-without-fix=PASS.

## File registration

New core files have no translatable strings, so per doc 16 they are registered in
`po/POTFILES.skip`: `gramps/plugins/view/test/__init__.py` and
`gramps/plugins/view/test/citationtreeview_test.py` (new `test/` package — there was no
`gramps/plugins/view/test/` directory before).

## Commit-readiness

`black` reports all three touched Python files unchanged (clean).
