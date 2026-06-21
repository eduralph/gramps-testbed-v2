# Fix media path whitespace stripping in XML export

## Root cause

The XML export serializer (`exportxml.py:1395`) routes media paths through `self.fix(path)`, which strips leading and trailing whitespace via `.strip()`. However, the package archiver (`exportpkg.py:192`) stores the media file under the un-stripped name (`archname = str(mobject.get_path())`), so the `<file src>` attribute disagrees with the archived filename, causing media to show as "missing" on re-import.

## Fix

Adds a dedicated `fix_media_path(path)` function to `libgrampsxml.py` that preserves whitespace while still removing XML-illegal control characters (via `_STRIP_DICT`) and escaping XML metacharacters (`&`, `<`, `>`) so the attribute value round-trips correctly on parse. Updates `exportxml.py:1395` to use this path-specific serializer instead of the general free-text `fix()` function, whose `.strip()` behavior is appropriate for descriptive fields but not for paths. Registers the new test in `po/POTFILES.skip`.

## Verified against

- `gramps/plugins/export/exportxml.py:1395` — media path serialized via `self.fix(path)`, now changed to `libgrampsxml.fix_media_path(path)`
- `gramps/plugins/lib/libgrampsxml.py:37` — end of module, where the import and new function are added (lines 22, 32–55)
- `gramps/plugins/export/exportpkg.py:192` — archiver stores file as `archname = str(mobject.get_path())`, confirming the invariant: `<file src>` must equal the archived name
- `po/POTFILES.skip:568` — entry for `gramps/plugins/export/test/exportvcard_test.py`, where the new test registration goes (line +569)

## Test

New regression test: `gramps/plugins/export/test/exportxml_mediapath_test.py`. Exercises the production path serializer (`libgrampsxml.fix_media_path`) directly, ensuring it preserves leading/trailing/interior whitespace while still removing control chars and escaping XML metacharacters. Includes a source-level guard that verifies the export plugin actually routes the `<file src>` path through the new serializer (so the test covers the real export path, not a parallel reimplementation). Old behavior is confirmed to be caught: `fix(" image.png")` → `"image.png"` (stripped), differing from the preserved path, making whitespace assertions genuine regressions.

Fixes #6698
