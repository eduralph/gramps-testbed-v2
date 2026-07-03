# Brief — issue 6824 / html-report-relative-media-paths

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** html-report-relative-media-paths
- **Defect:** The HTML backend of the text reports (e.g. Detailed Ancestor Report,
  Detailed Descendant Report) writes each embedded image's `<img src=…>` as the
  **absolute** filesystem path of the report's data directory. The generated `.html`
  therefore only renders on the machine that produced it — copy/share it (Dropbox,
  another computer) and every image breaks. sam888 confirmed on 4.2.0 and master; the
  emitted tag looks like `src="Y:\_me\Desktop\…\is654px-Aksel_Andersson.jpg"` where a
  report-relative `src="<report-subdir>/is654px-…jpg"` is expected.
- **Success criterion:** After the fix, `HtmlDoc.add_media(...)` emits an `<img>` whose
  `src` is the report-relative data-dir path (the report subdirectory basename +
  filename), containing no absolute directory prefix; the copied image file still lands
  in the correct on-disk location. Demonstrable by a C4 unit test that drives
  `HtmlDoc.add_media` and asserts the emitted `src` is relative (fails pre-fix because
  `src` carries the absolute `datadirfull()` path, passes post-fix).
- **Invariant to restore:** A generated document must reference its bundled assets by a
  path that is valid wherever the document is opened — i.e. relative to the document —
  not by a path tied to the generating host's filesystem. (Gramps report-portability
  rule; no external canon — the HTML backend already copies images into a
  report-relative data subdirectory, so the reference must match that layout.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** In the HTML docgen, the image reference written into the HTML is the
  absolute data-directory path instead of the report-relative one; the on-disk copy
  destination is correct and must stay absolute. Make the written reference relative
  while leaving the copy destination unchanged. / out of scope: other output backends
  (they render images correctly per sam888); the report modules themselves; CSS/favicon
  handling; NarrativeWeb/WebCal (separate code, not this report backend).
- **Repro instruction:** On `maintenance/gramps61`, load `example.gramps`, run
  Reports → Text Reports → Detailed Ancestor Report on a person with gallery media,
  tick "Include Photo/Images from Gallery", choose HTML output, generate, and inspect
  the produced `.html`: the `img src` attributes are absolute host paths.
- **Test file:** `gramps/plugins/test/htmldoc_relmedia_test.py` (core `test/` package,
  `*_test.py` suffix). The test MUST drive the production `HtmlDoc.add_media` path (open
  an `HtmlDoc` on a temp filename, stub only the image-resize step so no real image
  encoder is required) and assert on the `src` of the emitted `<img>` — not a
  reimplementation of the path-joining logic.
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause: `gramps/plugins/docgen/htmldoc.py:610-641` `add_media`, where
  `imdir = self._backend.datadirfull()` is used both for the copy destination and for
  the `src`; `gramps/plugins/lib/libhtmlbackend.py:288-298` `datadir()` vs
  `datadirfull()`).
- **New/removed files:** adds `gramps/plugins/test/htmldoc_relmedia_test.py` (a test, no
  translatable strings) → register in `po/POTFILES.skip`. No other `.py` added/removed.
- **Prior-art check (triage cycles):** searched `gramps/plugins/docgen/htmldoc.py` on
  `upstream/maintenance/gramps61` merged history — only license/black/`unique-cropped-
  filename` churn, no relative-path fix; no open/closed PR found on this path. Not
  already upstream.
- **Mantis:** 6824
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.
