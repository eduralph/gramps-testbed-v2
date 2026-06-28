# Brief — issue 8597 / verify-note-preview-length-configurable

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** verify-note-preview-length-configurable
- **Defect:** Reported (v4.1.3): the Note view's Preview column truncated note text at a
  hardcoded 79 characters, and the bottom status bar at 40 — far less than the column could
  display, with the two not even matching.
- **Success criterion:** On `maintenance/gramps61`, confirm the note preview length is no
  longer a hardcoded 79/40 limit — `Note.get_preview()` truncates to the configurable
  `interface.note-preview-length` setting — so the original hardcoded-truncation defect is
  resolved. Verification, not a new fix (no patch if confirmed fixed). If Do finds a
  residual hardcoded limit on the status-bar path, that residue is reported for a follow-up
  decision, not silently fixed here.
- **Invariant to restore:** (already restored) the note-preview truncation length is
  user-configurable rather than a magic constant. Behavioural / configurability invariant.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low — verification only.
- **Scope:** verify the note-preview length is config-driven (`Note.get_preview` ⇒
  `config.get("interface.note-preview-length")`) and that the 79/40 hardcoding the report
  describes is gone. / out of scope: changing the default length, the status-bar widget
  layout, adding new preferences.
- **Repro instruction:** original repro — Note view, add a note ≥ 80 chars, widen the
  Preview column: under the old build it truncated at 79. On current `maintenance/gramps61`
  the preview length follows `interface.note-preview-length`.
- **Test file:** gramps/gen/lib/test/note_test.py — a unit test that sets
  `interface.note-preview-length` and asserts `Note.get_preview()` honours it (drives the
  production `get_preview`). This documents the resolved behaviour; it should pass on
  current code. If a `note_test.py` already exists, extend it; otherwise this is the
  verification artifact.
- **Citations expected:** cite `gramps/gen/lib/note.py` `get_preview` reading
  `interface.note-preview-length` as the evidence the hardcoded 79 limit is gone.
- **New/removed files:** if a new `gramps/gen/lib/test/note_test.py` is added, register it
  in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/gen/lib/note.py` on
  `upstream/maintenance/gramps61` — `get_preview` now truncates to the
  `interface.note-preview-length` config value (no hardcoded 79). → defect already
  addressed; this bundle validates and resolves it.
- **Mantis:** 8597
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
