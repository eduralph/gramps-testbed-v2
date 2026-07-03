# Reference HTML-report images by a report-relative path

## Root cause

The HTML backend of the text reports writes each embedded image's `<img src>` using the
**absolute** filesystem path of the report's data directory (`HtmlDoc.add_media`
→ `self._backend.datadirfull()` — `gramps/plugins/docgen/htmldoc.py:608`). The generated
`.html` therefore only renders on the machine that produced it: copy or share it (Dropbox,
another computer) and every image breaks, because `src` points at e.g.
`Y:\_me\Desktop\…\isphoto.jpg` instead of a path relative to the document (Mantis 6824).

## Fix

`HtmlDoc.add_media` now references images by the **report-relative** data-directory path
(`self._backend.datadir()` — the data-subdirectory basename) while the on-disk copy still
targets the absolute `datadirfull()` location. The backend already copies images into that
report-relative subdirectory, so the written `src` now matches the on-disk layout and the
document stays valid wherever it is opened. Only the reference changes; the copy
destination is unchanged.

## Verified against

- `gramps/plugins/docgen/htmldoc.py:608` — `imdir = datadirfull()` (absolute) is kept for
  the copy destination; a new `imref = datadir()` (relative) is used for every `<img src>`
  written in `add_media` (the four `pos`/`alt` branches).
- `po/POTFILES.skip` — registers the new test file (no translatable strings).

## Test

`gramps/plugins/test/htmldoc_relmedia_test.py` drives the production `HtmlDoc.add_media`
path (opening a real `HtmlDoc` on a temp file; only the image-resize encoder is stubbed)
and inspects the emitted `<img>`:

- `test_add_media_src_is_report_relative` — across the `single` / `right` / `left` layouts,
  the `src` carries no absolute `datadirfull()` prefix, is not an absolute path, and equals
  the expected `myreport/isphoto.jpg`. Fails pre-fix, where `src` was the absolute path.
- `test_copy_destination_stays_absolute` — the resized image still lands at the absolute
  `datadirfull()` destination, confirming only the reference changed.

Fixes #6824
