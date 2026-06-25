## Root cause

The five RCS (archive) helpers in `gramps/gui/dbman.py` open their subprocess with a plain `subprocess.Popen(cmd, stderr=subprocess.PIPE)` (binary mode), so `proc.stderr.readlines()` yields `bytes` objects. The code then attempts to join these bytes directly into a string with `"\n".join(...)`, which raises `TypeError: sequence item 0: expected str instance, bytes found` whenever the subprocess writes anything to stderr, crashing the operation.

## Fix

- Adds `gramps/gui/dbman_utils.py` with a single helper function `read_subprocess_messages(proc)` that reads the binary stderr pipe and decodes each line to `str` before joining. Uses `errors="replace"` to gracefully handle non-UTF-8 locale-encoded diagnostics.
- Updates `gramps/gui/dbman.py` to import this helper and replaces all five call sites (lines 637, 809, 1179, 1224, 1255) with calls to `read_subprocess_messages(proc)`.
- Registers both the new module and the regression test in `po/POTFILES.skip` (no translatable strings).

The extraction into a separate import-light module enables the message-assembly logic to be tested headless (without importing the GTK-dependent `dbman.py`), allowing the regression test to drive the production path directly with a stubbed subprocess.

## Verified against

- `gramps/gui/dbman.py:637` (`__rename_revision`) — `message = "\n".join(proc.stderr.readlines())` joined bytes directly into a string; now routes through `read_subprocess_messages(proc)`.
- `gramps/gui/dbman.py:809` (`__delete_archive`) — same pattern; now calls the helper.
- `gramps/gui/dbman.py:1179` (`check_out`) — same pattern; now calls the helper.
- `gramps/gui/dbman.py:1224` (`_check_in`, archive creation) — same pattern; now calls the helper.
- `gramps/gui/dbman.py:1255` (`_check_in`, archive data) — same pattern; now calls the helper.

## Test

`gramps/gui/test/dbman_test.py` — a headless unittest that stubs a subprocess and drives `read_subprocess_messages()` through four cases: (1) the naive join raises `TypeError` (documents the bug), (2) the helper decodes bytes and returns a usable `str`, (3) empty stderr returns an empty string, and (4) non-UTF-8 bytes decode gracefully without raising `UnicodeDecodeError`. All four tests pass with the fix applied; the suite errors when the helper module is removed (red→green verification).

Fixes #13518
