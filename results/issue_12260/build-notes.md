# Build notes — issue 12260 / note-link-new-object-crash

## Root cause (verified against maintenance/gramps61, HEAD cbe5699b2e)

`EditLink._on_new_callback` (`gramps/gui/editors/editlink.py:156`) assumed the value
delivered by an inner editor's "new object created" callback is always an *object*
with a `.handle` attribute:

```python
def _on_new_callback(self, obj):
    object_class = obj.__class__.__name__
    self.selected.set_text(self.display_link(object_class, "handle", obj.handle))
    ...
```

But the editors invoked through `_on_new` → `EditObject` do **not** agree on the
reference type they emit. I grepped every `self.callback(...)` in
`gramps/gui/editors/*.py`:

- Most editors pass the **object**: `editperson.py:985`, `editfamily.py:1346`,
  `editevent.py:336`, `editsource.py:287`, `editmedia.py:384`,
  `editrepository.py:246`, `editplace.py:441`, **`editnote.py:383`**.
- `editcitation.py:401` passes a **handle string**: `self.callback(self.obj.get_handle())`.

So `_on_new_callback("<handle>")` hits `str.handle` → `AttributeError: 'str' object
has no attribute 'handle'` — exactly the crash in the brief.

## Important correction to the brief's premise

The brief (and the 2021 Mantis thread) describe the crash via the **Note** flow,
because historically `editnote.py:save` emitted `self.obj.get_handle()` (commit
6aad932574, 2007). That is **already reverted on maintenance/gramps61**: commit
`da0f9e808c` ("Pass an object rather than a handle to the note editor callback",
2026-04-18, present in HEAD — `git merge-base --is-ancestor da0f9e808c HEAD` = 0)
changed `editnote.py:383` back to `self.callback(self.obj)`. So the *literal* Note
repro no longer crashes on this branch.

The triage prior-art check only searched `editlink.py`, so it missed the editnote
fix — but it correctly concluded the *editlink* side is unfixed. The same
root-cause crash is **still reachable today** through `editcitation.py:401`: create
a *new Citation* from the Link Editor → save → `_on_new_callback(handle_str)` →
the AttributeError.

This is why I built to the brief's **Invariant to restore** ("the value passed to
`_on_new_callback` is treated as the kind of reference it actually is — a handle
string — not dereferenced as if it were an object") and its **Success criterion**
("…new Note **(or other object)** … no longer raises"), rather than the narrower
literal-Note proxy (which is already green and could not be made red→green). The
test drives the exact contract the brief specifies — `_on_new_callback` called with
a `str` — and that is genuinely red on the unpatched branch.

## The fix (`editlink.py:156`)

Read the value as the reference type it actually is:

```python
if isinstance(obj, str):
    object_class = OBJECT_MAP[self.uri_list.get_active()]
    handle = obj
else:
    object_class = obj.__class__.__name__
    handle = obj.handle
```

- The **object** path is byte-for-byte the previous behaviour (`obj.__class__.__name__`
  + `obj.handle`), so no object-passing editor changes.
- The **string** path derives `object_class` from the type the user selected in the
  Link Editor (`OBJECT_MAP[self.uri_list.get_active()]`) — the only reliable source
  when the value is a bare handle, and exactly the class `_on_new` asked `EditObject`
  to create (`editlink.py:172`).

This is the smallest change that restores the invariant across *all* editors at the
single boundary the brief scopes (`_on_new_callback`), without touching any editor's
save signature (explicitly out of scope).

## Alternatives considered and rejected

1. **Revert editcitation (and any handle-passers) to pass the object** — i.e. fix the
   cause on the editor side. Rejected as out of scope (the brief scopes the fix to
   `editlink.py` and lists "the note editor's save signature" / editors as out of
   scope), and it is the *larger, riskier* change: it touches each handle-passing
   editor and, per the Mantis thread (prculley ~0062246), other consumers such as
   `NoteTab` were written to expect a *handle* from these callbacks — flipping the
   emitted type risks breaking those consumers. The guard at the single consumer
   (`_on_new_callback`) restores the invariant without that blast radius.

2. **The Mantis workaround** (`try: test = obj.handle / except AttributeError: return`,
   romjerome ~0062260; closed PR 1196). Rejected: it *hides* the symptom by silently
   dropping the link the user just created (the `return` aborts link insertion), so it
   fails the success criterion ("…completes **and inserts the link**…"). My fix builds
   the link for both reference types.

3. **`isinstance(obj, str)` vs. duck-typing** (`getattr(obj, "handle", obj)`).
   Used explicit `isinstance` because the two cases need *different* `object_class`
   resolution (class name vs. UI selection), so a single duck-typed expression cannot
   express it cleanly.

## Test (`gramps/gui/editors/test/editlink_test.py`)

Drives the **production** `EditLink._on_new_callback` (not a copy): builds a real
`EditLink` instance via `__new__` (so no GTK toplevel is realised — headless-safe),
stubs only the four attributes the method touches (`uri_list`, `selected`,
`url_link`, `simple_access`), and calls the real method.

- `test_handle_string_callback_builds_link` — passes a `str` (the EditCitation /
  historical-EditNote contract); asserts the link `gramps://Note/handle/abc123handle`
  is built and no AttributeError. **Red pre-fix** (`str.handle`), green post-fix.
- `test_object_callback_still_builds_link` — passes a real `gramps.gen.lib.Note`
  object; guards that the object path is unchanged (green both sides).

Importing `gramps.gui.editors.editlink` pulls `from gi.repository import Gtk`, which
imports fine headless (no display needed for import — only widget realisation needs
one, and we realise none). Precedent: `editreference_test.py` in the same package
imports the editors package and even instantiates an editor.

## Verification

Could not use the shared `gramps-6.1` worktree for `run-verify.sh`: it was
concurrently dirty (other lanes' uncommitted edits to `editname.py`,
`libsourceview.py`, `POTFILES.skip`) and a concurrent cleanup reverted my edit
mid-run, so `run-verify.sh`'s `git diff --quiet` guard would refuse it. Instead I
verified in a dedicated throwaway worktree (`git worktree add /tmp/wt12260 HEAD`)
running the identical C4 logic (apply patch → run module → revert prod file, keep
test → re-run):

- GREEN with fix: 2 tests pass (rc 0).
- RED without fix (prod reverted, test kept): `test_handle_string_callback_builds_link`
  errors with `AttributeError: 'str' object has no attribute 'handle'` at
  `editlink.py:158` (rc 1).

`RESULT green_pass=True red_fail=True`.

## POTFILES

New core `.py` file `gramps/gui/editors/test/editlink_test.py` is a test with no
translatable strings → registered in `po/POTFILES.skip` under the "gui.editors.test
package" section (alongside `editreference_test.py`), per doc 16. No file removed.

## Commit-readiness

`black` run over both changed `.py` files (gramps' configured formatter); both
already conform.
