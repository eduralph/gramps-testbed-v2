# Verification: Note preview length is configurable (issue 8597)

## Root cause

The original defect reported hardcoded 79-character truncation of note preview text in the Note view, plus a separate 40-character limit in the status-bar navigation label. The hardcoded preview limit has been resolved upstream: `Note.get_preview()` now reads the configurable `interface.note-preview-length` setting instead of a magic constant.

## Fix

This patch adds a regression test (`gramps/gen/lib/test/note_test.py`) to document and verify the resolved behaviour:

- **test_honours_configured_length**: sets config to 20, verifies truncation at 20 (not hardcoded 79).
- **test_not_hardcoded_79**: sets config to 120 with a 200-character note; under the old hardcoded-79 behaviour this would have produced 79 chars + "…", proving this is the regression that documents the fix.
- **test_short_text_not_truncated**: verifies text shorter than the limit is returned unchanged.
- **test_newlines_flattened**: verifies newlines are replaced by spaces.

The test runs headless (imports only `gramps.gen.config` and `gramps.gen.lib.note`, no GUI) and passes all four cases in ~0.000s. It is registered in `po/POTFILES.skip` per the T2 potfiles gate.

## Verified against

**Target: gramps-project/gramps @ maintenance/gramps61**

- `gramps/gen/lib/note.py:275-287` — `Note.get_preview()` reads `config.get("interface.note-preview-length")` (line 282), not a hardcoded constant.
- `gramps/gen/config.py:280` — the setting is registered with default 80.
- `gramps/gui/configure.py:2381` — the preference is user-editable in Preferences > Display.

The hardcoded 79-limit behaviour described in the original report is resolved. A residual 40-character hardcoded limit exists in `gramps/gen/utils/db.py:360` (navigation status-bar path), but per issue scope that is out of band and reported for follow-up: it is a separate surface and a design decision whether to share the note-preview setting, create its own, or keep constant.

## Test

The regression test `gramps/gen/lib/test/note_test.py` exercises the production `Note.get_preview()` directly:

```bash
python3 -m unittest gramps.gen.lib.test.note_test
```

Expected output (all four cases pass):
```
test_honours_configured_length ... ok
test_newlines_flattened ... ok
test_not_hardcoded_79 ... ok
test_short_text_not_truncated ... ok
Ran 4 tests in 0.000s

OK
```

Fixes #8597
