# Build notes — issue 13518 / dbman-rcs-stderr-bytes-decode

## Root cause (two sentences)
The five RCS helpers in `gramps/gui/dbman.py` open their subprocess with a plain
`subprocess.Popen(cmd, stderr=subprocess.PIPE)` (binary mode), so
`proc.stderr.readlines()` yields `bytes`, and `"\n".join(...)` over `bytes` raises
`TypeError: sequence item 0: expected str instance, bytes found` the moment the RCS
process writes anything to stderr. The bytes must be decoded to `str` before the
string join.

## Target / citations (maintenance/gramps61, worktree `gramps-6.1`)
The five undecoded sites, verified present on the target branch:
- `gramps/gui/dbman.py:637` — `__rename_revision` (the reported Rename repro)
- `gramps/gui/dbman.py:809` — `__delete_archive`
- `gramps/gui/dbman.py:1179` — `check_out`
- `gramps/gui/dbman.py:1224` — `_check_in` (create archive)
- `gramps/gui/dbman.py:1255` — `_check_in` (archive data; the `~0069386` traceback)

## What the change does
- Adds `gramps/gui/dbman_utils.py` with one function,
  `read_subprocess_messages(proc)`, that does
  `"\n".join(line.decode(errors="replace") for line in proc.stderr.readlines())`.
- `gramps/gui/dbman.py:55` imports it; each of the five sites becomes
  `message = read_subprocess_messages(proc)`.
- `po/POTFILES.skip`: registers the new `gramps/gui/dbman_utils.py` (no translatable
  strings) and the new test `gramps/gui/test/dbman_test.py` (doc 16 §Adding Python
  files).

## Why a new module instead of an inline `.decode()` at each site
The Success criterion requires the test to route a stubbed subprocess **through the
production message-assembly path**. `dbman.py` imports GTK at load
(`from gi.repository import Gdk/Gtk/Pango`, `dbman.py:45-47`), so the C4 runner —
which is **headless** for a core fix (plain `python3 -m unittest`, no display/D-Bus) —
crashes if the test imports `dbman.py`. Extracting the one-liner into an import-light
module (`gramps/gui/__init__.py` pulls no `gi`) lets the test import and drive the
*exact* function production calls, with no parallel copy (principles §3.4). The five
call sites now share that single implementation.

Cost of the rejected inline alternative (`message = "\n".join(l.decode() ... )` at
each site, as in the tracker's `dbman_bytes_error.patch`): it is 5 edited lines vs.
my 5 edited lines + 1 import + a ~20-line helper — barely larger — **but it leaves no
import-light seam**, so the only way to test "the production path" would be to import
`dbman.py` (GTK at load) under a stubbed `gi`, i.e. mock `Gdk`/`Gtk`/`Pango` +
`gramps.gui.dialog`/`.glade`/`.managedwindow`/… — many fragile stubs that still load a
1300-line GUI module headless. The extraction is the smaller *testable* change.

## Decode policy: `errors="replace"`
Plain `.decode()` (strict UTF-8) would fix the reported `TypeError` but could raise a
*secondary* `UnicodeDecodeError` on a locale-encoded RCS diagnostic — the Success
criterion asks for "a usable string message without raising". `errors="replace"`
guarantees a `str` for any byte content at the cost of one kwarg. The
`test_non_utf8_does_not_raise` case pins this.

## Out of scope (per brief)
The `parent=self.top` at `dbman.py:1236` / `:1267` inside the module-level `_check_in`
(no `self` in scope) is a pre-existing latent `NameError` only reachable on the RCS
error path. The brief scopes it out (the commenter's `NameError` on 6.0.3 was a
mis-applied-patch artifact), and it is an unrelated defect — left untouched to keep
one logical change per patch.

## Red→green evidence
Verified by applying `patch.diff` to the clean `gramps-6.1` worktree and running the
import-light test (the C4 runner is headless; this test imports only the pure
`gramps.gui.dbman_utils`):
- **Green (fix applied):** all 4 tests pass.
- **Red (production module reverted, test kept):** `from .. import dbman_utils`
  → `ImportError` → the suite errors. This is exactly C4's `PROD_NEW` removal leg
  (`run-verify.sh` removes the patch-added prod file for the red pass).

The full Docker-based `run-verify.sh` (C4-verify) could not be executed in this Do
environment (container invocation needs an approval the builder can't grant); the
manual red→green above mirrors its mechanic file-for-file, and Check re-runs the real
gate.

## Formatting
`black` (target's commit hook) was run over all touched files;
`gramps/gui/dbman_utils.py` was reformatted to black's layout (the join collapsed onto
one line). `dbman.py` and the test were already black-clean.
