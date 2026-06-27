# Brief — issue 7832 / get-age-dateless-birth-masks-dated-fallback

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** get-age-dateless-birth-masks-dated-fallback
- **Defect:** When a person has a Birth event that carries only a place (no date) plus a
  Baptism (birth-fallback) event that *does* have a date, age computation yields no age, so
  Fan Chart colouring (and any age-based consumer) loses the colour. Root cause (verified):
  `get_birth_or_fallback` (gramps/gen/utils/db.py:53–71) returns the primary Birth event as
  soon as one exists (lines 58–62) regardless of whether it has a usable date, so the dated
  baptism fallback (lines 64–70) is never reached; `get_age` (line 95) then has a dateless
  birth and returns nothing. The reporter attached a patch and notes it benefits every
  caller of `get_age`. The symptom surfaces in fanchartview via `get_age`.
- **Success criterion:** For a person with a Birth event lacking a date and a dated Baptism
  event (and a dated Death event), `get_age(db, person)` returns the age computed from the
  dated baptism rather than `None`; a person whose primary Birth event *has* a date is
  unaffected. Demonstrable by C4-verify against gramps/gen/utils/test/db_test.py.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: age computation must use the best *dated* event available; a
  dateless primary event must not mask a dated fallback event of the same kind.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** the date-bearing event selection used to compute a person's *age* when the
  primary birth (or death) event has no date but a dated fallback exists. / out of scope:
  redesigning `get_birth_or_fallback` semantics for non-age callers that legitimately want
  the dateless primary event (e.g. displaying a birth place); the analogous
  `get_birth_of_fallback`/pedigreeview adjustments the reporter explicitly deferred.
- **Repro instruction:** on maintenance/gramps61, build a Person with a Baptism event
  (date set), a Death event (date set), and a Birth event with a place but NO date; call
  `gramps.gen.utils.db.get_age(db, person)` — observe no age is returned. Removing the
  dateless birth event restores the age.
- **Test file:** gramps/gen/utils/test/db_test.py (NEW). The test MUST drive the production
  `get_age` path (the same function fanchartview calls), not a re-implementation
  (principles.md §3.4).
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** ADDS gramps/gen/utils/test/db_test.py → register in
  `po/POTFILES.skip` (test, no translatable strings; matches the existing
  gramps/gen/utils/test/*_test.py entries).
- **Prior-art check (triage cycles):** searched by path `gramps/gen/utils/db.py` on
  upstream/maintenance/gramps61 — recent commits are Black reformat (b3a5cf346f) and
  `Preserve order in find_children` (0502ab2af3); neither touches the birth/age fallback. No
  prior/closed PR found for this fallback path.
- **Mantis:** 7832
- **Disposition hint:** likely-fix
