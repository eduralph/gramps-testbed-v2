## Root cause

The `EditLink._on_new_callback` method (gramps/gui/editors/editlink.py:156-160) assumes its callback parameter is always an object with a `.handle` attribute. However, some editors including `EditCitation` (editcitation.py:400-401) pass only the handle string via `self.obj.get_handle()`, causing `AttributeError: 'str' object has no attribute 'handle'` when creating a new linked object through the Link Editor.

## Fix

Add a type check at the callback boundary in `_on_new_callback` to distinguish string handles from objects:
- If the callback emits a string: derive the object class from the Link Editor's active selection (`OBJECT_MAP[self.uri_list.get_active()]`)
- If the callback emits an object: extract the class name and handle as before (preserving existing behavior for the majority of editors)

This restores the invariant that the callback reads the value as the reference type it actually is—a handle string or an object—without requiring changes to any editor's save signature. The fix is localized to the single consumer boundary where the type ambiguity occurs.

## Verified against

- `gramps/gui/editors/editlink.py:156-160` — the pre-fix `_on_new_callback` that assumes `.handle` on all inputs
- `gramps/gui/editors/editcitation.py:400-401` — the real editor that emits `self.obj.get_handle()` (a string)
- `gramps/gui/editors/editnote.py:381-383` — the Note editor that emits `self.obj` (an object) as the callback parameter
- `patch.diff:20-27` — the type-guarded fix applied in-place to the production method

## Test

Regression test in `gramps/gui/editors/test/editlink_test.py` (new file):
- `test_handle_string_callback_builds_link` — drives the production `_on_new_callback` with a handle string (as EditCitation emits); **red pre-fix** with `AttributeError: 'str' object has no attribute 'handle'`, **green post-fix** with the link correctly built
- `test_object_callback_still_builds_link` — guards that object-passing editors (the majority) remain unchanged; **green both sides**

The test exercises the real `EditLink._on_new_callback` method on a real instance (instantiated without GTK widget realisation), not a copy or mock.

Fixes #12260
