# Build notes — issue 6698 / xml-export-strips-media-path-whitespace

## Root cause (verified against source, maintenance/gramps61)

`exportxml.py:1395` serialized the media path through `self.fix(path)`, and
`fix()` (`exportxml.py:490-492`) does `l.strip().translate(strip_dict)`. The
`.strip()` removes leading/trailing whitespace — which is **significant in a
filename**. Meanwhile the package archiver stores the file under the
**un-stripped** name: `exportpkg.py:192` `archname = str(mobject.get_path())`.
So for a path like `" image.png"` the XML `<file src>` said `image.png` while the
tar entry was ` image.png` → the two disagree → media "missing" on re-import.

This is the invariant the brief names: the path written into `<file src>` MUST
equal the archived/on-disk name. The fix restores agreement by making the path
serializer faithful (no whitespace stripping).

## The fix

A dedicated path serializer that does NOT strip whitespace, only removing
XML-illegal control chars and escaping XML metacharacters (so the attribute
round-trips on parse):

- `gramps/plugins/lib/libgrampsxml.py` — new `fix_media_path(path)` (+ the
  control-char `_STRIP_DICT` and an `xml.sax.saxutils.escape` import). This is an
  **import-light** module (no `gi` / `gramps.gui`), already a dependency of
  exportxml (`exportxml.py:67`).
- `gramps/plugins/export/exportxml.py:1395` — `self.fix(path)` →
  `libgrampsxml.fix_media_path(path)`. Only the `<file src>` path routes through
  the new serializer; `desc`/`mime_type` keep `self.fix` (out of scope).
- `po/POTFILES.skip` — register the new test (doc 16; no translatable strings).

Behaviour parity for the empty path: old `fix("")` → `""`; new
`fix_media_path("")` → `escape("")` → `""`. Same.

## Why this design (and what I ruled out)

- **Why a new function, not just dropping `.strip()` from `fix()`:** `fix()` is
  the general free-text serializer used for ~20 fields (note text, types,
  attribute values…); stripping there is intended for those. The bug is specific
  to the *path*, so a path-specific serializer is the smallest change that
  restores the invariant without changing unrelated field behaviour.

- **Why put it in `libgrampsxml.py` rather than a `fix_path` *method* on
  `GrampsXmlWriter`:** the C4 runner is **headless**. `exportxml.py` imports
  `from gramps.gui.plug.export import …` at load (`exportxml.py:66`), so any test
  that imports `exportxml` crashes the headless runner (core dump). The logic had
  to live in an import-free module so the test can drive the *real* production
  function without pulling in Gtk. `libgrampsxml` was the natural home (already
  imported by exportxml; no gui deps). Production routes through it
  (`exportxml.py:1395` calls `libgrampsxml.fix_media_path`), so the test exercises
  the production path, not a copy — and a source-level guard test asserts exactly
  that (`fix_media_path(path)` present in exportxml.py).

- **Why NOT centralize `escxml`/`strip_dict` into libgrampsxml too (the "tidier"
  refactor):** that is larger and touches code unrelated to the invariant. Cost:
  it would move the `escxml` def (`exportxml.py:86-98`, 13 lines) and the
  `strip_dict` assignment (`exportxml.py:83`) out of exportxml and convert them to
  imports, and exportxml has ~24 `escxml(...)` call-sites (verified:
  `grep -c escxml exportxml.py`) plus a second `strip_dict` consumer at
  `exportxml.py:552` — all of which would then depend on the move being correct.
  The brief names an **Invariant to restore**, so the target is the *smallest
  change that restores it*, not the tidiest. The cost of the chosen approach is
  one duplicated 1-line control-char table (`_STRIP_DICT`) and one duplicated
  3-key escape dict — matching the existing precedent that `check.py:98` already
  keeps its own `strip_dict` copy. Net new production lines: ~26 in libgrampsxml +
  1 changed line in exportxml, vs. the refactor's churn across 25+ call sites.

## Verification

- **Logic (host):** `fix_media_path` produces the expected output for leading /
  trailing / interior whitespace, plain paths, control-char removal, `&`/`<`/`>`
  escaping, empty string, and archiver-name agreement (`== str(path)`). All pass.
- **Old behaviour is genuinely caught:** old `fix(" image.png")` → `image.png`
  (stripped) ≠ `" image.png"`, so the whitespace asserts are real regression
  asserts, not just an existence check for the new function.
- **black:** `black --check` clean on all three patched files (gramps's commit
  hook) — reconstructed the patched files in a scratch tree and ran black 26.5.0.
- **Patch applies clean** to clean `upstream/maintenance/gramps61` (lane worktree
  `git apply --check`).
- **C4 red→green (engine runner):** could NOT be executed in this Do session —
  `engine/scripts/ubuntu/run-verify.sh` cd's into `/home/eddie/workspace` and runs
  `docker run` with mounts of the lane worktrees, which are outside this session's
  sandbox-allowed paths; the call is hard-denied (not approvable from here). The
  contract nonetheless holds by construction: the runner classifies
  `exportxml_mediapath_test.py` as the test and reverts the prod files
  (exportxml.py, libgrampsxml.py, POTFILES.skip) for the red leg → `fix_media_path`
  vanishes from libgrampsxml → `ImportError` at test import → RED; with the patch
  → GREEN (logic verified). Check re-runs the authoritative C4-verify.

## Files

- `gramps/plugins/lib/libgrampsxml.py` (+~26)
- `gramps/plugins/export/exportxml.py:1395` (1 line)
- `gramps/plugins/export/test/exportxml_mediapath_test.py` (new test)
- `po/POTFILES.skip` (register test)
