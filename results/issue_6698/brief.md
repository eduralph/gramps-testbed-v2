# Brief — issue 6698 / xml-export-strips-media-path-whitespace

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** xml-export-strips-media-path-whitespace
- **Defect:** A media object whose stored path has leading (or trailing) whitespace —
  e.g. `" image.png"` — loses that whitespace when the tree is exported to Gramps XML
  (`.gramps`) or a Gramps XML Package (`.gpkg`). On re-import the media file can no longer be
  located and shows as "missing". The reporter's PNGs all had an unintended leading space
  (introduced by copy-paste); dsblank (~0047796) diagnosed it as "the filenames start with a
  space character, and it is getting removed along the way."
- **Success criterion:** A media object whose path begins with a space survives a Gramps-XML
  export → import round-trip with the path **byte-for-byte unchanged**; equivalently, the
  `<file src="…">` attribute written to the XML preserves the exact path string (leading space
  included), so it still matches the filename under which the `.gpkg` archives the media file.
  Demonstrable by C4-verify on the patch's own test (export serialization of a space-leading
  path).
- **Invariant to restore:** A stored media path round-trips through XML/gpkg serialization
  unchanged — the path written into the `<file src>` element MUST equal the path the package
  archiver stores the file under and the actual on-disk filename. (Internal Gramps
  reference-integrity invariant: a media path either resolves or is cleaned up — silently
  rewriting it on export breaks resolution. No external canon; stated as a project rule.)
  SELF-TEST: a one-module guard that only special-cases the reporter's PNGs would not satisfy
  this — the property is over *any* path the user legitimately stored, so the fix must make
  the serializer faithful, not patch one symptom.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** the Gramps-XML media-path serialization that alters the path. Root cause:
  `gramps/plugins/export/exportxml.py:1392` writes the `<file src="%s">` via `self.fix(path)`,
  and `fix()` (`exportxml.py:490-492`) does `l.strip().translate(strip_dict)` — the `.strip()`
  removes leading/trailing whitespace that is significant in a filename, while
  `gramps/plugins/export/exportpkg.py:192` archives the file under the **un-stripped**
  `archname = str(mobject.get_path())`; the two disagree, so the XML points at a name the archive
  doesn't contain. The fix restores agreement between the serialized path and the archived/on-disk
  name. / out of scope: control-character / XML-escaping behaviour of `fix()` for other text
  fields; sanitising or warning about pathological filenames at entry time (the reporter's
  "warning about cut-and-paste" musing) — that is a separate UX change.
- **Repro instruction:** On maintenance/gramps61, create a tree, add a media object whose
  path is `" example.png"` (leading space) pointing at a file of that exact name; export to
  `.gramps`; inspect the written `<file src=…>` — the leading space is gone. Re-import: the
  object is "missing".
- **Test file:** gramps/plugins/export/test/exportxml_mediapath_test.py — a new core
  `*_test.py` that drives the **production** export path (instantiate the real XML writer /
  run the export plugin on a small in-memory tree with a space-leading media path) and asserts
  the emitted `<file src>` preserves the path verbatim (or that an export→import round-trip
  preserves `media.get_path()`). It MUST exercise the real serializer, not a hand-copied
  `fix()` reimplementation.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds `gramps/plugins/export/test/exportxml_mediapath_test.py` (a test,
  no translatable strings) → register in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/plugins/export/exportxml.py` — recent commits are the NS-URI change + black reformat;
  no media-path-whitespace fix. Merged history clean; a closed/rejected-PR search by this path
  is advised at review.
- **Mantis:** 6698
- **Disposition hint:** likely-fix
