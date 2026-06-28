# Brief — issue 4862 / narrative-marriage-uses-preferred-not-birth-name

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** narrative-marriage-uses-preferred-not-birth-name
- **Defect:** In narrative text reports (Detailed Descendant/Ancestor and others) the spouse
  in the "He married <name> on <date>." sentence is rendered with the spouse's *currently
  preferred* name. When that person later divorced and remarried (so their preferred name is a
  later married/alternate name), the sentence becomes ambiguous — the reporter expects the name
  the spouse held at the time / their birth name. The sentence is produced by the shared
  narrator: detdescendantreport.py:624 `self.__narrator.get_married_string(...)` →
  gramps/plugins/lib/libnarrate.py.
- **Success criterion:** the marriage sentence in the narrative reports refers to the spouse by
  a stable name (the spouse's primary/birth name) that does not change when the spouse acquires
  a later preferred married name, removing the divorced-and-remarried ambiguity the reporter
  describes. **Exact name-selection rule is a human design call (see Disposition).**
  Demonstrable by C4-verify against a narrator-level test.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement, pending the design call: a person referenced in a past-tense
  narrative event is named unambiguously, independent of a later preferred-name change.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** high
- **Scope:** the spouse-name rendering inside the marriage/relationship sentence of the shared
  narrator. / out of scope: changing how names are displayed everywhere else; restructuring the
  name-display configuration; alternate-name *type* modelling.
- **Repro instruction:** on maintenance/gramps61, import a tree where a bride has a later
  remarriage giving her a different preferred name (reporter's test: select "Peter, Black",
  produce a Detailed Descendant Report) and observe "He married <later-preferred-name> on
  <date>." instead of the name expected for that marriage.
- **Test file:** gramps/plugins/lib/test/libnarrate_test.py (gramps/plugins/lib/test/ exists) —
  drive the production `get_married_string` path, not a copy (principles.md §3.4).
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** if a new core test .py is added, register it in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/lib/libnarrate.py` on
  upstream/maintenance/gramps61 — only license-text (d82eb0f460) and `Add support for Hebrew
  prefixes` (7703cb630d); neither addresses spouse name-selection ambiguity. No prior/closed PR
  found.
- **Mantis:** 4862
- **Disposition hint:** likely-fix — **NEEDS-HUMAN (fitness-to-purpose):** whether reports
  *should* switch from preferred to birth/primary name here is a design decision and is always
  the human's at sign-off (docs §4 human-only items). Do should produce the minimal change that
  satisfies the chosen rule; the reviewer/human ratifies the rule.
