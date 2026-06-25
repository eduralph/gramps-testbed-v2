# Brief — issue 8362 / gedcom-export-place-type-accented

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** gedcom-export-place-type-accented
- **Defect:** (Reported on 4.1.1, 2015.) GEDCOM export of a marriage place differed
  depending on the place TYPE ("Città" vs "Town"), and the reporter attributed the
  difference to the accented "à". At the time, the export mapped place parts into the
  GEDCOM ADDR/CITY structure by matching the (translated) place type against English
  "City"/"Town", and the Python-2-era handling interacted with the accented character.
  The maintainer's standing position in the thread: this is a translation-mapping issue,
  not an export bug.
- **Success criterion:** Exporting an event whose place has an accented title and a place
  type such as "Città" produces a correct UTF-8 `PLAC` line that round-trips the accented
  character intact, and the output does not differ by place type (the type no longer
  drives the place export). Demonstrable by C4-verify on a GedcomWriter test.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** confirm the reported export discrepancy no longer reproduces on the current
  code. The 5.0 place-model rewrite removed the place-type→ADDR/CITY mapping for event
  places — `__write_place()` now emits `PLAC = <display name>` (+ lat/long + notes)
  independent of the place type, and Python-3 / UTF-8 handles the accent. / out of scope:
  a new patch; redesigning the GEDCOM ADDR structure; the broader "which place types map
  to which GEDCOM fields" question the maintainer flagged as translation-dependent /
  by-design.
- **Repro instruction:** Build an in-memory tree with a family, a marriage event, and a
  place whose title contains an accented char and whose type is "Città"; export to GEDCOM
  via GedcomWriter; repeat with the place type changed to "Town"; assert both `PLAC`
  lines are correct UTF-8 and identical (modulo the title text), with the accent intact.
- **Test file:** gramps/plugins/export/test/exportgedcom_place_test.py (new). NOTE: this
  is a verification of current behaviour, not a red→green fix — there is no patch to
  revert, so `run-verify` will emit `PDCA-UNVERIFIABLE` → §6 NEEDS-HUMAN (expected); the
  test ships and must pass on the current target.
- **Citations expected:** Do must cite path:line on maintenance/gramps61.
- **New/removed files:** adds gramps/plugins/export/test/exportgedcom_place_test.py (no
  translatable strings) → po/POTFILES.skip. (export/test/ already exists.)
- **Prior-art check (triage cycles):** searched gramps/plugins/export/exportgedcom.py on
  the pinned worktree — `__write_place()` (line ~1593) writes only `PLAC` + MAP + notes
  from the place display object; there is no place-type-keyed ADDR/CITY branch for event
  places (the old type-dependent mapping is gone since the place-model rewrite). Reported
  symptom is OBE — this is verify-first; the human may instead close by-design at sign-off
  per the maintainer's standing position.
- **Mantis:** 8362
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
