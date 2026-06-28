# Brief — issue 6793 / surname-gramplets-disagree-on-unique-count

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** surname-gramplets-disagree-on-unique-count
- **Defect:** For the same tree, "Top Surnames"/Surname-Cloud and the Statistics gramplet
  report different "Total unique surnames" (reporter: 244 vs 449) although "Total people" agree.
  Root cause (verified): the gramplets enumerate unique surnames by different rules. The Surname
  Cloud gramplet (gramps/plugins/gramplet/surnamecloudgramplet.py:104–117,183) builds its set
  from `name.get_group_name()` / `name.get_surname()` per primary name, while the Statistics
  gramplet (gramps/plugins/gramplet/statsgramplet.py:189–191) counts
  `len(set(database.surname_list))` (the db's individual-surname index). These count different
  things, so the totals diverge.
- **Success criterion:** the "unique surnames" total reported by the surname gramplets is
  computed by one consistent rule, so the same tree yields the same unique-surname count across
  the gramplets that report it. Demonstrable by C4-verify driving the production counting
  routine(s) on a fixture tree. **Which rule is canonical is a human design call (see
  Disposition).**
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: "unique surnames" denotes one well-defined quantity computed the
  same way wherever Gramps reports it.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** the divergent unique-surname enumeration between the surname/statistics gramplets.
  / out of scope: the cloud weighting/font-size visualisation, surname *grouping* config, and
  the patronymic-origin question (that is issue 6988 — keep the two changes separable).
- **Repro instruction:** on maintenance/gramps61 with example.gramps, add the Top Surnames /
  Surname Cloud and Statistics gramplets to the Dashboard and compare their "Total unique
  surnames" values.
- **Test file:** gramps/plugins/gramplet/test/surnamecount_test.py (NEW). The test MUST call
  the production counting routine(s) the gramplets use on a shared fixture and assert agreement
  (principles.md §3.4) — not re-implement the count.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** ADDS the test (and possibly `test/__init__.py`) → register the new
  .py file(s) in `po/POTFILES.skip`.
- **Conflicts with:** 6988
- **Ordering note:** 6988 also edits the surname-counting gramplets (topsurnamesgramplet.py /
  statsgramplet.py); never co-schedule 6793 and 6988 in the same concurrent wave. No build-on
  dependency — they are separable behaviours (count *consistency* vs patronymic *membership*).
- **Prior-art check (triage cycles):** searched by paths
  `gramps/plugins/gramplet/{surnamecloudgramplet,topsurnamesgramplet,statsgramplet}.py` on
  upstream/maintenance/gramps61 — only Black/license commits and an unrelated `Fix Top Surnames
  gramplet opening report for the wrong surname` (e39dc09e2e); no unification of the unique
  count. No prior/closed PR found.
- **Mantis:** 6793
- **Disposition hint:** likely-fix — **NEEDS-HUMAN (fitness-to-purpose):** which counting rule
  is the canonical "unique surnames" is the human's call at sign-off.
