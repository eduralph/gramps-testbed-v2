# Brief — issue 6571 / gedcom-multiple-surname-comma-export

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** gedcom-multiple-surname-comma-export
- **Defect:** When a person has multiple surnames (the compound-surname facility) and the
  tree is exported to GEDCOM, the `2 SURN` line is written as a comma-joined list
  (`", ".join(surns)`) and only the first surname's prefix is written to `2 SPFX`. Other
  programs — and Gramps' own GEDCOM importer — do not split that comma list back into
  separate surnames, so a Gramps→GEDCOM→Gramps round-trip collapses the multiple surnames
  into one and concatenates the prefixes.
- **Success criterion:** N/A — disposed as **by-design**, no patch. The reporter himself
  notes "According to the written standard, the use of comma's on export is right", and the
  developer (dsblank, ~0033473) ruled it by design: GEDCOM is a lossy interchange format and
  the comma-separated `SURN` Gramps emits is GEDCOM-5.5.1-conformant. The two ways forward the
  reporter proposed (A: emit the compound name in a single `SURN`, abandoning the standard
  comma form; B: make Gramps' importer split the comma list) are mutually-exclusive **design
  choices about GEDCOM round-trip semantics**, not a single correct fix — they need a
  maintainer design decision before any code is touched.
- **Invariant to restore:** N/A — no implementable invariant; the current behaviour follows
  the GEDCOM 5.5.1 written standard. This is a contribution-policy / format-design question,
  not a behavioural defect with a determinate correct answer.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** none — this is a triage disposition, not a fix. / out of scope: changing the
  GEDCOM export surname serialization (`gramps/plugins/export/exportgedcom.py:1380-1390`) or
  the GEDCOM import surname split, either of which is a design change.
- **Repro instruction:** Import a tree with a person having multiple surnames; export to
  GEDCOM (`gramps/plugins/export/exportgedcom.py` writes `2 SURN A, B`); re-import the GEDCOM
  and observe the surnames collapse to a single comma-joined surname.
- **Test file:** none (no patch).
- **Citations expected:** n/a.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/plugins/export/exportgedcom.py` — no surname-serialization change; the comma-join
  has stood since the multiple-surname feature landed. The "by design" ruling is on the
  Mantis thread itself.
- **Mantis:** 6571
- **Disposition hint:** by-design
