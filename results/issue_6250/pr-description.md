## Root cause

When `GtkDocParagraph.divide` splits a styled paragraph (e.g. across a page break), it rebuilds the second part's `Pango.AttrList` by re-parsing markup via a 2012 workaround (bug 6208 / gnome 646788). The workaround walks the markup string and counts plaintext bytes to re-index the runs, but it miscounts escaped markup entities (`&amp;`, `&lt;`, `&gt;`) as multiple plaintext bytes instead of the single byte they represent in parsed plaintext — Pango attribute offsets are defined against the **parsed plaintext**, not the markup serialisation. Any paragraph with `&`, `<`, or `>` before the split desyncs the byte cursor, placing or dropping style runs on the wrong characters.

## Fix

Replace the markup re-serialisation workaround with direct re-indexing of the already-parsed attribute list using the now-available `get_iterator()` API (introspectable again on every supported GI stack). Extract the re-indexing logic into a new import-light module `gramps/plugins/lib/libcairodocattr.py` so both production code and tests exercise the same function and the test remains headless (Pango requires no display). Remove the `filterattr` method (which was incorrectly dropping boundary runs — a run with `start_index == index` should survive, clamped to 0, not be filtered out). Register the new module and test files in `po/POTFILES.skip` under new section headers (mirroring the existing `plugins/docgen/test` entries).

## Verified against

- `gramps/plugins/lib/libcairodoc.py:664-667` — the setup of the plaintext slice and the old `filterattr` call, now replaced
- `gramps/plugins/lib/libcairodoc.py:669, 674-684` — the GTK3 PROBLEM comment and OLD EASY CODE comment marking the obsolete approach
- `gramps/plugins/lib/libcairodoc.py:685-714` — the removed `## START OF WORKAROUND … ##END OF WORKAROUND` block (re-serialising and re-parsing markup)
- `gramps/plugins/lib/libcairodoc.py:734-740` — the removed `filterattr` method (callback that incorrectly filtered boundary attributes)
- `gramps/plugins/lib/libcairodoc.py:536` — the `__set_attrlist` method that receives the re-indexed list
- `po/POTFILES.skip:557-558` — existing `# plugins/docgen/test directory` section (pattern mirrored for the new `# plugins/lib/test directory`)

## Test

`gramps/plugins/lib/test/libcairodoc_test.py` — a new unit test that drives the production re-index seam (`reindex_split_attrlist`) on a `Pango.AttrList` from `Pango.parse_markup` (no display or cairo surface). Four test methods exercise the split boundary (run starting exactly at the split point, rebased to byte 0), a straddling run (split inside a run, clamped to 0), a wholly-after run (shifted by index), and a wholly-before run (dropped). The regression test fails RED on the current buggy `filterattr`-based code (the boundary bold run is filtered out, leaving an empty list) and passes GREEN after the patch applies (the bold run survives and is rebased to the correct byte offsets). This headless test can be run in isolation with `pytest gramps/plugins/lib/test/libcairodoc_test.py` or via the standard unit-test discovery (`python3 -m unittest gramps.plugins.lib.test.libcairodoc_test.ReindexSplitAttrListTest`).

Fixes #6250
