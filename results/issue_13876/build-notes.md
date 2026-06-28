# Build notes — issue 13876 / citation-tree-delete-citation

## Root cause (two sentences)

The Citation Tree view's delete runs through the shared helper
`gramps.plugins.lib.libsourceview.LibSourceView.remove_object_from_handle`
(citationtreeview.py:76 mixes in `LibSourceView`; its `remove`/`remove_object_from_handle`
override the `ListView` versions). After cleaning up back-references, that helper's
final statement was unconditionally `self.dbstate.db.remove_source(handle, trans)`
(libsourceview.py:102 on maintenance/gramps61) — so when the selected row is a
**citation**, it asked the DB to remove a *source* with the citation's handle, which
is a no-op, and the citation survived. Source deletion appeared to work only because
the hard-coded `remove_source` happened to match the object type.

## The fix

libsourceview.py:101-102 → dispatch on the resolved object type, exactly as the base
class already does (`ListView.remove_object_from_handle`, listview.py:712):

```
-        # and delete the source
-        self.dbstate.db.remove_source(handle, trans)
+        # and delete the object (Source or Citation)
+        self.dbstate.db.method("remove_%s", obj_type)(handle, trans)
```

`obj_type` is the type `LibSourceView.remove` already resolves for each selected
handle (libsourceview.py:46-52: `has_source_handle` → "Source" else "Citation"). For a
Source this is identical to the old `remove_source`; for a Citation it now correctly
calls `remove_citation`. This is the smallest change that restores the brief's
**Invariant**: a delete acts on exactly the object the selected row represents (the
selected node → its handle → the matching `remove_<type>`).

Note the Source branch (libsourceview.py:71-96) still removes child citations and
back-refs; only the final object-deletion line was type-blind. The two-dialog
duplication noted in the report is explicitly out of scope (cosmetic).

## Why this and not an alternative

- **Override `_citation_row_delete` instead** — rejected: that method is only the
  *view-refresh* callback for the `citation-delete` DB signal (citationtreeview.py:216,
  `row_delete`); it fires *after* a successful DB delete and never runs here because no
  delete happens. Touching it would not delete anything.
- **Give CitationTreeView its own `remove_object_from_handle`** — rejected: it would
  duplicate the ~40-line Source/back-ref cleanup in libsourceview.py:55-102 (a second
  copy to drift), where `LibSourceView` is the one shared helper for both SourceView
  and CitationTreeView. SourceView never selects citations so the one-line dispatch is
  safe and correct for both.
- The chosen one-liner mirrors the base `ListView` helper verbatim, so it is the
  least-surprising form a reviewer can confirm against listview.py:712.

## Tests

Two tests ship, per the brief.

1. **Headless gated proof (C4-verify):**
   `gramps/plugins/lib/test/libsourceview_test.py` (+ empty `test/__init__.py`). It is
   import-light — imports only `gramps.gen.db`, `gramps.gen.lib`,
   `gramps.plugins.lib.libsourceview` (no `gi` / `gramps.gui`), so it runs under the
   headless C4 runner. It drives the **production** `LibSourceView` methods directly via
   a minimal GUI-free `_Probe(LibSourceView)` carrier (no re-implementation): it calls
   the real `remove()` (resolution invariant) and the real `remove_object_from_handle()`
   (the deletion). Uses the same in-memory sqlite db pattern as
   `gramps/plugins/db/dbapi/test/db_test.py` (`make_database("sqlite")` + `load(":memory:")`).

   - `test_delete_citation_removes_it_from_db` is the **red→green** leg:
     pre-fix the final `remove_source(citation_handle)` is a no-op, so
     `has_citation_handle` stays True and `assertFalse` FAILS (RED); post-fix
     `remove_citation` deletes it, so it PASSES (GREEN). It also asserts the source
     survives.
   - `test_remove_resolves_selected_citation_to_citation` pins the resolution
     invariant (passes both legs).
   - `test_delete_source_removes_source_and_its_citation` guards that the
     already-working Source path keeps working (passes both legs).

2. **Committed AT-SPI repro (advisory C4-verify-interface):**
   `engine/interface/test_bug_13876_citation-tree-delete.py` (testbed repo, NOT in
   `patch.diff`). Navigates Sources category → Citation Tree view mode → expands the
   "World of the Wierd" source (S00002) → selects its citation row C02324 ("Page pi") →
   Delete → confirms the dialogs → asserts the C02324 row is gone. Uses graceful skips
   for infra-driving failures so only a delivered-but-undeleted citation reports the
   symptom (the established pattern, e.g. test_bug_0011786). It is advisory; the gated
   proof is the headless companion above.

## POTFILES

New core `.py` files registered in `po/POTFILES.skip` (doc 16 §Adding and removing
Python files; they hold no translatable strings): `gramps/plugins/lib/test/__init__.py`
and `gramps/plugins/lib/test/libsourceview_test.py`, in a new `plugins/lib/test`
section. T2-potfiles is satisfied.

## Verification status

I could not execute `run-verify.sh` or `python3 -m unittest` from this Do session: the
engine runner needs interactive Docker approval, and the pinned `gramps-6.1` worktree
is outside this session's allowed exec scope (it is also a shared lane that an external
process reverted my edit on mid-session — `patch.diff` was captured before the revert
and is self-contained, so this does not affect the deliverable). The red→green is
deterministic from the diff (argued above) and Check's C4-verify gate runs it for real
on a clean upstream worktree. `patch.diff` applies to clean
`upstream/maintenance/gramps61` (context verified against HEAD:po/POTFILES.skip and the
unmodified libsourceview.py).

## Commit-readiness

The fix is a one-line replacement; the test file is written in black style (double
quotes, trailing commas in multi-line calls). Both should pass the gramps `black`
pre-commit hook unchanged. (Could not run black here for the same exec-scope reason;
flagged for the human at sign-off.)

## Citations (maintenance/gramps61)

- gramps/plugins/lib/libsourceview.py:101-102 — the buggy `remove_source` line (the fix site)
- gramps/plugins/lib/libsourceview.py:42-53 — `remove()` resolves Source vs Citation
- gramps/gui/views/listview.py:712 — base `ListView.remove_object_from_handle` (the correct dispatch pattern mirrored)
- gramps/gui/views/listview.py:651-663 — `delete_object_response` → `remove_object_from_handle("Citation"|"Source", ...)`
- gramps/plugins/view/citationtreeview.py:76 — `class CitationTreeView(LibSourceView, ListView)`
- gramps/plugins/view/citationtreeview.py:216-218 — `_citation_row_delete` (view-refresh callback, not the delete)
- gramps/plugins/db/dbapi/test/db_test.py:60-63 — in-memory sqlite db test pattern reused
- example/gramps/example.gramps:58811 (S00002 "World of the Wierd"), :51253 (C00973), :56665/C02324 — fixture data for the interface repro
