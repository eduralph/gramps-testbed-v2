# Build notes — issue 13888 / treedoc-image-source-option

## Target branch
`gramps-project/gramps @ maintenance/gramps61`. I built and verified against
**`upstream/maintenance/gramps61`** (commit `b679c084f6`), which is the clean
contribution base the C4 runner patches (`gramps-6.1` worktree). The local
`maintenance/gramps61` ref (674e3be80a) is an *older* testbed state that lacks the
`gen.plug.docgen.test` package + its POTFILES.skip section; a patch generated against
it does NOT apply to clean upstream (first attempt failed `git apply` at
`po/POTFILES.skip:230`). `treedoc.py` is byte-identical on both bases, so the code
hunks are unaffected; only the POTFILES.skip context differs. Always target upstream.

## What I changed (citations on the target file)
`gramps/gen/plug/docgen/treedoc.py` (one file, as the brief scopes):

1. **`_IMAGES` constant** — added after `_DETAIL` (`treedoc.py:65-69`). Two items:
   `thumbnail` → _("Thumbnails (smaller PDF)") (default) and `original` →
   _("Original images (full resolution)").
2. **`TreeOptions.__init__`** — `self.images = None` next to `self.detail = None`
   (`treedoc.py:169`).
3. **`TreeOptions.add_menu_options`** — new `EnumeratedListOption("Images", "thumbnail")`
   in the `_("Node Options")` category, immediately after the `detail` option
   (`treedoc.py:201-202`), with `set_help(...)` describing the size/standalone
   trade-off, `menu.add_option(category, "images", images)`, `self.images = images`.
4. **`TreeDocBase.__init__`** — `self.images = get_option("images").get_value()` next
   to `self.detail = ...` (`treedoc.py:379`).
5. **`write_node`** image block (`treedoc.py:593-604`): compute `original =
   media_path_full(db, media.get_path())` once; branch on `self.images`:
   - `"original"` → `path = original` (the verbatim pre-PR-1620 emission removed in
     core commit 7335883f68), then `image = {path}`, **no** comment.
   - else (`"thumbnail"`, default) → `path = get_thumbnail_path(original,
     rectangle=...)` (unchanged), and *additionally* write `%% original image: %s` %
     `original` (renders to the LaTeX comment `% original image: <path>`) before the
     `image = {path}` line.
   The `media.get_mime_type().startswith("image")` guard, `os.path.isfile(path)`
   check, `win()` backslash fix, and `break  # first image only` are all preserved.

`po/POTFILES.skip` — registered the new test in the `gen.plug.docgen.test` section
(`POTFILES.skip:241-242`), as a test with no translatable strings (T2-potfiles).
`treedoc.py` is already in `POTFILES.in`, so the new `_()` option strings are covered
with no POTFILES.in change.

## Test — `gramps/gen/plug/docgen/test/treedoc_test.py`
Drives the production `write_node` path: builds a real `Menu` via
`TreeOptions().add_menu_options`, sets the `images` option, instantiates the concrete
`TreeGraphDoc(options, None)` subclass, and a stub db returning one `image/png` Media.
Asserts both Success-criterion branches:
- `original` → tex contains `image = {<original path>}`, no `original image:` comment.
- `thumbnail` → tex contains `image = {<thumb path>}` (not the original) plus
  `% original image: <original path>`.

### Headless import-safety (why `get_thumbnail_path` is stubbed)
The C4 runner is headless (plain `python3 -m unittest`, no display). `write_node`'s
first line is `from ...utils.thumbnails import get_thumbnail_path`; **calling** the real
`get_thumbnail_path` loads thumbnailer plugins and transitively a Gtk widget
(`grampletpane.LinkTag` builds a `Gtk.Label` at import) which aborts a display-less
interpreter with SIGTRAP — the `headless-ut-segfault` essential dependency
(`engine/essential-fixes.tsv`, fix `f4f94f34db`). My **first** version called the real
`get_thumbnail_path` and the runner flagged exactly this: it FAILED on clean upstream
and only passed on the essential line (`essential-dependency.json`,
`depends_on: ["headless-ut-segfault"]`).

The brief warns (and so do the builder instructions) to make the test import-safe
rather than depend on an unlanded fix. So the thumbnail test replaces
`get_thumbnail_path` (an **unchanged collaborator**, not the code under test) with a
stub returning a real temp file. The code under test — the new branch routing and the
`% original image:` comment emission — is still the production `write_node`. This is
seam injection on an external collaborator, not a parallel copy of the emission logic
(principles §3.4): production routes through the same `write_node`. After this change
the runner reports green-with-fix / red-without-fix on **clean upstream** and clears
the stale `essential-dependency.json`.

Importing `gramps.gen.utils.thumbnails` to patch it loads only `gi` typelibs
(GLib/GdkPixbuf/Gtk) — that prints PyGIWarnings but builds no widget, so it is safe
headless (it is the plugin-loading inside `get_thumbnail_path` that segfaults, not the
module import).

## Red→green proof
`PDCA_BUNDLE=…/issue_13888 ./engine/scripts/ubuntu/run-verify.sh`
→ `C4-verify: green-with-fix=PASS / red-without-fix=PASS` against clean
`upstream/maintenance/gramps61`. Red leg (treedoc.py reverted): the `images` option no
longer exists, so `menu.get_option_by_name("images")` is `None` → `AttributeError` →
all three tests error (genuinely catches the missing feature).

## Alternatives considered / rejected
- **Real `get_thumbnail_path` in the test** (first attempt): rejected — fails on clean
  upstream (headless segfault dependency), exactly what the instructions say to avoid.
  Cost of keeping it: the fix could only land *after* essential `f4f94f34db`, a
  merge-order coupling; the stub removes it entirely. Concrete: the runner moved from
  writing `essential-dependency.json` (upstream FAIL) to clearing it (upstream PASS).
- **Asserting the exact hash thumbnail filename** rather than stubbing: would require
  running the real thumbnailer (same segfault risk) and ties the assertion to the
  thumbnail-cache hash — brittle and headless-unsafe. The stub asserts the *routing*
  (thumbnail path ≠ original) and the comment, which is the behaviour the option adds.
- **Putting the original filename inside the thumbnail's filename** (vs a `%` comment):
  re-breaks LaTeX on comma/space paths — the exact hazard PR 1620 fixed; a `%` comment
  is inert. (Brief's rejected alternative; kept rejected.)

## Formatter
`black --target-version py311` over both touched `.py` files: "left unchanged"
(commit-ready for gramps's pre-commit `black` hook).
