# Build notes — issue 6824 / html-report-relative-media-paths

Target branch: `gramps-project/gramps @ maintenance/gramps61`
Developed/verified in the isolated worktree `../gramps-6.1`
(detached at `upstream/maintenance/gramps61`, tip `0d9e148908`).

## Root cause

`HtmlDoc.add_media` (`gramps/plugins/docgen/htmldoc.py:610` on the target branch)
computes a single directory value and uses it for **two different purposes**:

```python
imdir = self._backend.datadirfull()          # :610
...
resize_to_jpeg(name, imdir + os.sep + refname, ...)   # :613  (filesystem copy dest)
...
Html("img", src=imdir + os.sep + refname, ...)        # :624,629,636,641  (HTML reference)
```

`datadirfull()` (`gramps/plugins/lib/libhtmlbackend.py:294`) returns
`os.path.join(os.path.dirname(self.getf()), self.datadir())` — the **absolute**
path of the report's data subdirectory on the generating host. That absolute path
is correct for the on-disk copy (where the resized JPEG must physically land) but
wrong for the `<img src>`: the browser resolves `src` relative to the `.html`
file, so an absolute host path only works on the machine that generated it. Copy
or share the report (the reporter's Dropbox / another computer) and every image
breaks — the reported `src="Y:\_me\Desktop\…\is654px-…jpg"`.

The backend already exposes the report-relative form:
`datadir()` (`libhtmlbackend.py:288`) returns `self._subdir` — the data
subdirectory *basename* (`"myreport"` for `myreport.html`, set in
`_checkfilename`, `libhtmlbackend.py:241`). This is exactly what `build_header`
(`htmldoc.py:154-156`) already uses to reference favicon/CSS relatively. `add_media`
is the one place that reached for the absolute `datadirfull()` for its reference.

## The fix (smallest change that restores the invariant)

`gramps/plugins/docgen/htmldoc.py`:
- Keep `imdir = self._backend.datadirfull()` for the copy destination — the resize
  call at `:613` is **unchanged**, so the JPEG still lands in the correct absolute
  on-disk location (Scope: "the on-disk copy destination is correct and must stay
  absolute").
- Add `imref = self._backend.datadir()` — the report-relative subdirectory basename.
- Change only the four `Html("img", src=…)` sites to use `imref` instead of `imdir`.

The invariant to restore is document-portability, not diff size. The join separator
for the `src` is switched from `os.sep` to a literal `"/"`: `src` is a URL, whose
separator is `/` on every platform, so a report generated on Windows no longer
emits backslashes into the reference either. `refname`/`imref` never contain a path
separator themselves, so `"/"` is safe. This is what makes the reference "valid
wherever the document is opened" rather than merely stripping the drive prefix.

## Alternatives considered and rejected

1. **Change `datadirfull()` to return a relative path** — rejected. `datadirfull()`
   is the on-disk copy destination used across the class (`open` mkdir at
   `htmldoc.py:261-263`, `copy_file` at `:295`, `write_support_files` at `:323,334`);
   making it relative would break the physical file writes and violate the Scope
   ("copy destination … must stay absolute"). It also touches ~6 call sites vs. the
   4-line change here.
2. **Post-process the emitted HTML to rewrite absolute `src`** — rejected: a symptom
   guard bolted onto output, not a cause fix; brittle (path-string matching) and
   larger. The cause is a single wrong variable at the reference site.
3. **Keep `os.sep` for the relative join** — rejected: on Windows it re-introduces
   backslashes into a URL, so a Windows-generated report opened on macOS/Linux (the
   Dropbox-share scenario in the ticket) would still break. `"/"` costs nothing extra
   and fully restores the invariant.

## Test — `gramps/plugins/test/htmldoc_relmedia_test.py`

Drives the **production** path: constructs a real `HtmlDoc(StyleSheet(), None)`,
`open()`s it on a temp `myreport.html` (which really creates the `myreport/` data
subdir on disk), then calls the real `HtmlDoc.add_media`. Only the image encoder is
stubbed (`mock.patch.object(htmldoc, "resize_to_jpeg", …)`) — as the brief directs —
so no real image/GdkPixbuf is needed; the stub also records the destination it was
handed and writes a placeholder file there. It then renders the produced HTML
(`str(doc.htmllist[-1])`) and extracts the `<img src>` with a regex.

Assertions:
- `test_add_media_src_is_report_relative` (over `pos` ∈ {single, right, left}, with
  and without a caption, covering all four `Html("img")` sites): `src` does **not**
  contain the absolute `datadirfull()` prefix, is **not** absolute, and equals
  `"myreport/isphoto.jpg"`.
- `test_copy_destination_stays_absolute`: the resize destination is
  `datadirfull()/isphoto.jpg` and the file exists there — proving the on-disk copy
  location is unchanged.

Import-safety (headless C4 runner): `gramps.plugins.docgen.htmldoc` imports only
`gramps.gen.*` / `gramps.plugins.lib.*`; `resize_to_jpeg` imports `gi`/`GdkPixbuf`
lazily *inside* the function (`gramps/gen/utils/image.py:88`), never at module load,
and the test stubs it — so nothing pulls in Gtk/gi/display at import. No
`gramps.gui.*` import anywhere.

New file registered in `po/POTFILES.skip` (test, no translatable strings), inserted
alphabetically among the `gramps/plugins/test/*_test.py` entries.

## Verification performed

The authoritative C4 gate (`engine/scripts/ubuntu/run-verify.sh`, docker) could not
be executed from this Do session — docker invocation requires an approval this
sandbox denied. Instead I ran an **honest** red→green against the real production
code from the worktree source (no mock/copy of production): I built a minimal
`GRAMPS_RESOURCES` tree (so `gramps.gen.const` initialises without a `build/` step)
and ran `python3 -m unittest gramps.plugins.test.htmldoc_relmedia_test` twice:

- **Fix applied → GREEN** (both tests / all subTests pass).
- **Production change reverted, test kept → RED**: all three subTests of
  `test_add_media_src_is_report_relative` fail with
  `'…/myreport' unexpectedly found in '…/myreport/isphoto.jpg'` — i.e. the test
  really catches the absolute-path bug. (`green_rc=0 red_rc=1`.)

This mirrors exactly what `run-verify.sh` asserts (green-with-fix ∧
red-without-the-prod-change). The docker C4 gate should be re-run by the harness as
the system of record; it is expected to pass on clean `upstream/maintenance/gramps61`
(the change has no dependency on any essential fix).

## Commit-readiness

`black` is not installed in this environment (no network/pip to add it), so I could
not run it. I hand-verified black conformance: 88-col limit (the only borderline
line — the collapsed `doc.add_media(...)` call — is 89 chars, so black keeps my
wrapped form), double-quoted strings, trailing commas as black emits. The htmldoc
edits only shorten existing already-black-formatted lines. If the maintainer's
commit hook reformats, it should be a no-op.
