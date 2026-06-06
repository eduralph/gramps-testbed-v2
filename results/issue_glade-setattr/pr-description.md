# Fix crash on every Glade() construction that blocked GUI startup

Testbed #1. Follow-up to PR #2313 (`f8c1fc0f50`) — the `__setattr__` guard it
added in place of `__slots__` did not work.

## Root cause

`Glade.__setattr__` guards against ad-hoc attributes by comparing the
incoming `name` against a whitelist, but the whitelist holds the source-level
names `__toplevel`/`__filename`/`__dirname` while `__init__` assigns
`self.__dirname` etc., which Python name-mangles inside class `Glade` to
`_Glade__dirname` — so the guard rejects the class's own assignments with
`AttributeError: Ad-hoc attribute _Glade__dirname is not permitted.` at the
first private assignment, and the same method passes `self` twice to the
already-bound `super().__setattr__`, which would raise `TypeError` once the
guard is satisfied. Both faults were introduced by
`f8c1fc0f507b30d2bd4ec949bd8b95de489b7c4d` ("Don't use slots on
GObject-derived classes."), which replaced `__slots__` with this
`__setattr__` and touched only `gramps/gui/glade.py`; every `Glade()` —
opening a tree, the Database Manager, the standard dialogs — aborted before a
window appeared.

Removing `__slots__` was itself the correct, upstream-recommended fix: per
GNOME/pygobject work item #734, PyGObject wrapper objects do not play well with
`__slots__` (slot data lives on the wrapper, not the instance `__dict__`), which
crashed Gramps once pygobject 3.55.1 shortened the wrapper lifecycle. pygobject
`!508` removed slot support and added the `PyGIWarning: GObject derived class
Glade shouldn't use slots` that prompted `f8c1fc0f50`. The problem is only in the
hand-written guard that replaced the slots — and it did not survive review:
petr-fedorov reported on PR #2313 that the fix "does not work" (naming the
name-mangling), and hgohel reproduced the same exception on Windows / Python 3.14.

## Fix

Whitelist the *mangled* names `_Glade__toplevel`/`_Glade__filename`/
`_Glade__dirname` so the guard accepts `__init__`'s own private assignments,
and drop the duplicate `self` from the `super().__setattr__(name, value)`
call. Ad-hoc attributes outside the whitelist are still rejected, so the
guard's purpose is preserved. The change is two lines, contained entirely in
the method the regression created.

## Verified against

- `gramps/gui/glade.py:64-66` (maintenance/gramps61) — whitelist changed from
  the unmangled `__toplevel`/`__filename`/`__dirname` to the mangled
  `_Glade__toplevel`/`_Glade__filename`/`_Glade__dirname`.
- `gramps/gui/glade.py:69` (maintenance/gramps61) — `super().__setattr__(self,
  name, value)` corrected to `super().__setattr__(name, value)`.
- `gramps/gui/glade.py:146` (maintenance/gramps61) —
  `self.__dirname, self.__filename = os.path.split(path)`, the first mangled
  assignment that the broken guard rejected at runtime.
- `f8c1fc0f507b30d2bd4ec949bd8b95de489b7c4d` — `git show --stat` confirms it
  touched only `gramps/gui/glade.py`, so this PR reverses the regression in
  full with no other file to change.

## Test

New regression test `gramps/gui/test/glade_test.py` (alongside the existing
`display_test.py`/`user_test.py`/`utils_test.py`). It drives the real
`Glade.__init__` path end-to-end — loading an actual `.glade` file through
`Gtk.Builder` — the same construction shape GUI startup uses, rather than a
synthetic `__setattr__` bypass. To run on the headless unittest runner (no
display / D-Bus / AT-SPI), the loaded file contains a single non-widget
`GtkListStore` toplevel, which `Gtk.Builder` builds via the GObject type
system without a display connection. `test_real_construction_succeeds` asserts
the construction completes and reads back `dirname`/`filename`/`toplevel`
through the public property getters; `test_adhoc_attr_still_rejected` confirms
the guard still rejects unexpected attributes. The test is red pre-fix (the
real `__init__` raises `AttributeError: Ad-hoc attribute _Glade__dirname is
not permitted.`) and green post-fix.

Fixes #14153
