# Brief — issue 6988 / surname-count-includes-patronymic-nonprimary

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** surname-count-includes-patronymic-nonprimary
- **Defect:** The Top Surnames and Statistics gramplets treat a person's non-primary
  *patronymic*-origin surname as part of the surname, so people sharing one family surname but
  with different patronymics (e.g. "Иванов Петрович", "Иванов Сергеевич", "Иванов Андреевич")
  are counted and displayed as separate surnames instead of the single surname "Иванов". Root
  cause: the gramplets enumerate the full multi-surname string
  (gramps/plugins/gramplet/surnamecloudgramplet.py:111–117 via `name.get_surname()`;
  gramps/plugins/gramplet/statsgramplet.py:112–114 iterating `name.get_surname_list()`) without
  distinguishing surname origin, so patronymic components inflate and fragment the counts.
- **Success criterion:** for a person whose name carries a primary family surname plus a
  separate `Patronymic`-origin surname, the surname gramplets count/display the family surname
  (e.g. "Иванов") as one surname rather than one entry per patronymic combination.
  Demonstrable by C4-verify driving the production counting routine on a fixture name.
  **Whether patronymics are excluded vs grouped is a human design call (see Disposition).**
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: surname tallying reflects the family-surname identity, not the
  accidental product of family-surname × patronymic.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** how patronymic-origin (non-primary) surname components participate in the
  surname-counting/listing of the surname & statistics gramplets. / out of scope: the
  cross-gramplet *count-consistency* unification (that is issue 6793); name-display formatting;
  the relationship calculator.
- **Repro instruction:** on maintenance/gramps61, add people with surname "Иванов" plus a
  Patronymic-origin secondary surname (steps in the tracker row), then read the Top Surnames /
  Statistics "unique surnames" — observe three separate surnames where one is expected.
- **Test file:** gramps/plugins/gramplet/test/patronymic_surname_count_test.py (NEW). The test
  MUST drive the production counting routine on a constructed Name with a Patronymic-origin
  surname (principles.md §3.4), not a copy.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** ADDS the test (and possibly `test/__init__.py`) → register the new
  .py file(s) in `po/POTFILES.skip`.
- **Conflicts with:** 6793
- **Ordering note:** 6793 edits the same surname-counting gramplets (surnamecloudgramplet.py /
  statsgramplet.py / topsurnamesgramplet.py); never co-schedule 6988 and 6793 in the same
  concurrent wave. No build-on dependency.
- **Prior-art check (triage cycles):** searched by paths
  `gramps/plugins/gramplet/{topsurnamesgramplet,statsgramplet,surnamecloudgramplet}.py` on
  upstream/maintenance/gramps61 — only Black/license + the unrelated wrong-surname-report fix
  (e39dc09e2e); no patronymic-aware surname counting. No prior/closed PR found.
- **Mantis:** 6988
- **Disposition hint:** likely-fix — **NEEDS-HUMAN (fitness-to-purpose):** the correct
  treatment of patronymic surnames in counts is the human's call at sign-off.
