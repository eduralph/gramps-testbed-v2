# Citation Tree view: Fix silent delete failure for citation nodes

## Root cause

Citation Tree view's delete operation routes through the shared helper `LibSourceView.remove_object_from_handle()`, which resolves the selected row to its citation handle and then delegates to the database layer. However, the final deletion statement unconditionally called `remove_source(handle, trans)` (libsourceview.py:102), treating the handle as a source key regardless of the selected object's actual type. For a citation node (selected row representing a Citation, not a Source), this was a silent no-op since no source with that citation handle exists.

## Fix

Replace the hard-coded `remove_source()` call (libsourceview.py:101-102) with a type-aware dispatcher: `self.dbstate.db.method("remove_%s", obj_type)(handle, trans)`. The `obj_type` variable already holds the resolved type ("Source" or "Citation") from the same method's earlier resolution step (libsourceview.py:42-53). For a Source this produces identical behavior to the old code; for a Citation it now correctly calls `remove_citation()`. This is the minimal change that restores the delete invariant (a selected row's delete acts on that row's object type) while preserving the Source branch's existing child-citation and back-reference cleanup logic (libsourceview.py:55-102).

## Verified against

- gramps/plugins/lib/libsourceview.py:42-53 — type resolution (Source vs Citation) in `LibSourceView.remove()`
- gramps/plugins/lib/libsourceview.py:101-102 — the buggy unconditional `remove_source()` call
- gramps/gui/views/listview.py:712 — base `ListView.remove_object_from_handle()` using the correct dispatch pattern
- gramps/plugins/view/citationtreeview.py:76 — `CitationTreeView` inherits `LibSourceView.remove_object_from_handle()`

## Test

Two regression tests ship with this fix:

1. **Headless unit test** (`gramps/plugins/lib/test/libsourceview_test.py`): A headless, GUI-free test that drives the production `LibSourceView` methods directly against an in-memory database. `test_delete_citation_removes_it_from_db` is the red-green leg: before the fix, `remove_source(citation_handle)` is a no-op so the citation survives (RED); after the fix, `remove_citation()` is called and the citation is deleted (GREEN). Additional tests verify the resolution invariant and that source deletion (the path that already worked) remains unbroken.

2. **Committed AT-SPI repro** (`engine/interface/test_bug_13876_citation-tree-delete.py`, testbed repo): An advisory interface-level test that navigates the Citation Tree view mode, selects a citation row by name, deletes it via the UI, and asserts it no longer appears. This is separate from the patch and runs under the C4-verify-interface gate on the unpatched (RED) and patched (GREEN) worktrees.

Fixes #13876
