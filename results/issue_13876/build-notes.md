# Build notes — issue 13876 / citation-tree-view-delete-noop

## Root cause (verified on the target branch)

`gramps/plugins/lib/libsourceview.py` (the `LibSourceView` mixin shared by
`SourceView` and `CitationTreeView`) ends `remove_object_from_handle` with, on
the target branch `maintenance/gramps61` (verified at lane0 / 674e3be80a,
`libsourceview.py:101-102`):

```python
        # and delete the source
        self.dbstate.db.remove_source(handle, trans)
```

The method receives `obj_type` ∈ {`"Source"`, `"Citation"`} and is supposed to
delete *that* object. The final line is hard-coded to `remove_source`. When a
**Citation** row is selected in Citation Tree view, `obj_type == "Citation"` but
the code still calls `remove_source(citation_handle, …)`.

`remove_source` dispatches to `_do_remove(handle, transaction, SOURCE_KEY)`
(`gramps/gen/db/generic.py:2335`, impl `gramps/plugins/db/dbapi/dbapi.py:845`).
`_do_remove` guards with `if self._has_handle(obj_key, handle)` — a citation
handle is not in the **source** table, so the guard is false and `_do_remove`
returns without deleting anything. Net effect: confirming Delete on a citation
row removes nothing — exactly the reported symptom.

Why Source rows "work" and "a citation deletes only if its parent source is also
selected": deleting a Source runs the `obj_type == "Source"` branch
(`libsourceview.py:71-96`), which explicitly walks the source's back-linked
citations and calls `remove_citation` on each. So the child citation is removed
as a side effect of the source deletion — never via the citation's own delete
path.

## The fix (invariant-restoring, 1 line)

`libsourceview.py:101-102` →

```python
        # and delete the object itself (a Source or a Citation)
        self.dbstate.db.method("remove_%s", obj_type)(handle, trans)
```

`db.method("remove_%s", obj_type)` is the same dynamic-dispatch idiom this exact
function already uses for `get_%s_from_handle` / `commit_%s` (lines 62, 89, 98,
100), so it routes to `remove_source` for a Source and `remove_citation` for a
Citation. This restores the brief's **Invariant**: a selected Citation is
removed regardless of view mode — the tree-view delete now performs the same
citation removal the flat list view does. It is the smallest change that
restores the invariant, not merely the smallest diff.

### Alternatives considered and rejected

- **`if obj_type == "Citation": remove_citation(...) else: remove_source(...)`** —
  a 4-line conditional that hard-codes the only two types instead of dispatching.
  More lines (4 vs 1) and it re-introduces the same brittleness (a third type
  would silently fall into the `else`). The `method("remove_%s", obj_type)`
  dispatch is consistent with the four sibling `method(...)` calls already in
  this function, so it is both smaller and more uniform.
- **Fixing it in `citationtreeview.py`'s `remove` override instead** — the
  defect is in the *shared* base `remove_object_from_handle`, which both views
  call. Patching the subclass would leave the base wrong and could diverge
  Source vs Citation behaviour; the base is the correct single point.

## Test (production path, headless)

`gramps/plugins/view/test/citationtreeview_test.py` drives the **production**
handler `LibSourceView.remove_object_from_handle("Citation", handle, trans,
in_use_prompt=False)` against a real in-memory sqlite db — not a re-implemented
copy of the delete logic (avoids the issue-8653 "test mirrors production" trap).
It asserts the citation is gone afterward and the parent source remains.

`LibSourceView` is import-light: `libsourceview.py:23` imports only
`gramps.gen.errors` (which has no imports), and `gramps/plugins/__init__.py` /
`gramps/plugins/lib/__init__.py` are both empty. So importing the mixin pulls in
**no** `gi` / `gramps.gui` — it runs under the headless C4 runner (plain
`python3 -m unittest`, no display/D-Bus/AT-SPI). The Citation delete path never
touches `self.uistate` (that is only the `obj_type == "Source"` progressbar
branch at `libsourceview.py:81-86`), so a bare `_Handler(db)` instance with just
`dbstate` set exercises the real code path.

Red/green is exact: with the fix `remove_citation` deletes the citation (GREEN);
without it `remove_source(citation_handle)` no-ops and the citation survives, so
the assertion fails (RED).

## Addressing Iteration-1 carry-forward

The sign-off rationale claimed `LibSourceView` "is a GUI view mixin with
gi/gramps.gui imports … never headlessly importable". That is **not** the case
on the target branch — verified above: the only import is `gramps.gen.errors`
(no imports) and both package `__init__.py` files are empty. The real cause of
the v1 C4 failure was the **patch itself**: v1's `po/POTFILES.skip` hunk carried
~40 lines of mass deletions of *unrelated* test entries plus an erroneous
`undoablestyledbuffer_test.py` line belonging to another bundle, so `git apply`
could not land the patch on the pristine upstream/essential worktrees → C4 failed
on both legs (not an import or environment problem).

This iteration therefore keeps the correct 1-line `libsourceview.py` fix and the
production-path test, and **scopes `POTFILES.skip` to only the two new entries**
(`gramps/plugins/view/test/__init__.py` and `…/citationtreeview_test.py`),
inserted in the `plugins/view` section. The db-method-dispatch behaviour the
carry-forward suggested testing *is* what the test checks — but it does so by
routing through the production handler (principles §3.4), not by calling
`db.method(...)` directly on a hand-built copy.

## Verification

`./engine/scripts/ubuntu/run-verify.sh` (C4, headless core, PDCA_LANE=0):

```
→ C4-verify (core, core 6.1.0): gramps.plugins.view.test.citationtreeview_test
→ green check (fix applied):    Ran 1 test ... OK
→ red check (production change reverted, test kept): FAILED (failures=1)
C4-verify: green-with-fix=PASS / red-without-fix=PASS
```

`black --check` is clean on the three touched files (the target repo's
pre-commit formatter), so the patch is commit-ready.

## File registration (doc 16 §Adding and removing Python files)

Two new core `.py` files, both with no translatable strings → registered in
`po/POTFILES.skip` (not POTFILES.in): the empty package marker
`gramps/plugins/view/test/__init__.py` and the test
`gramps/plugins/view/test/citationtreeview_test.py`.
