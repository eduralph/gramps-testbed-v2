# Add image source option to genealogytree Tree reports

## Root cause

Since PR 1620 (core commit 7335883f68), Tree reports embed only cached thumbnails to avoid unreasonably large PDFs and LaTeX parser failures on special-character paths. However, this reduced image quality (3–12 kB thumbnails vs 500 kB–2 MB originals) and machine-tied filenames make the generated `.tex` files non-standalone and unidentifiable.

## Fix

This adds a user-selectable `images` option to `gramps/gen/plug/docgen/treedoc.py` allowing users to choose between cached thumbnails (default, preserving PR 1620) and original full-resolution images (pre-1620 behaviour, now opt-in).

**Changes in `gramps/gen/plug/docgen/treedoc.py`:**

- New `_IMAGES` constant (around line 65) defining two items: `"thumbnail"` (default, _("Thumbnails (smaller PDF)")) and `"original"` (_("Original images (full resolution)")).
- `TreeOptions.__init__` (line 169): Add `self.images = None` alongside `self.detail`.
- `TreeOptions.add_menu_options` (line 201): Add `EnumeratedListOption("Images", "thumbnail")` in the Node Options category, immediately after the detail option, with help text explaining the size/standalone trade-off.
- `TreeDocBase.__init__` (line 379): Read the option with `self.images = get_option("images").get_value()`.
- `write_node` (line 593–604): Compute the full media path once, then branch on `self.images`:
  - When `"original"`: emit the full-resolution path (pre-1620 behaviour).
  - When `"thumbnail"` (default): emit the cached thumbnail path plus a LaTeX comment `% original image: <path>` so the `.tex` stays identifiable.

**Changes in `po/POTFILES.skip`:**

- Register the new test file `gramps/gen/plug/docgen/test/treedoc_test.py` in the `gen.plug.docgen.test` section (line 241), as a test with no translatable strings.

## Verified against

- `gramps/gen/plug/docgen/treedoc.py:65-69` — `_IMAGES` constant defines both image-source items and defaults to thumbnail (safety).
- `gramps/gen/plug/docgen/treedoc.py:169` — `self.images` initialized in `TreeOptions.__init__` alongside other node options.
- `gramps/gen/plug/docgen/treedoc.py:201-202` — Option added to the Node Options category menu immediately after detail, with translatable label and help text.
- `gramps/gen/plug/docgen/treedoc.py:379` — `self.images` value fetched in `TreeDocBase.__init__` from the options menu.
- `gramps/gen/plug/docgen/treedoc.py:593-604` — `write_node` branches on `self.images`: emits full path when `"original"`, or thumbnail path + `% original image:` comment when `"thumbnail"`.

## Test

`gramps/gen/plug/docgen/test/treedoc_test.py` — new test file driving the production `write_node` path. It instantiates a real `TreeOptions` menu, sets the `images` option, constructs a concrete `TreeGraphDoc` subclass with a stub database and a media reference, and asserts both branches:

- `original` → `.tex` contains `image = {<original media path>}`, no `% original image:` comment.
- `thumbnail` (default) → `.tex` contains `image = {<cached thumbnail path>}` (not the original path) and a `% original image: <original path>` comment.

The test stubs `get_thumbnail_path` (an unchanged collaborator that would load Gtk widgets in the headless runner) while keeping the branch routing and comment emission in the production `write_node` code. The runner reports green-with-fix / red-without-fix on clean upstream (both the option and the branching logic are required for the test to pass).

---

cc @codefarmer @azrdev — this reconciles the requirements you outlined (PR 1620 safety with user opt-in for original resolution + identifiability), defaulting to the current safe behaviour. Review appreciated.

Fixes #13888
