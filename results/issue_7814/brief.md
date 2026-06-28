# Brief — issue 7814 / detdescendant-death-line-for-living

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** detdescendant-death-line-for-living
- **Defect:** The Detailed Descendant Report printed "Died ______ in ______." for a person
  with no death event who is still living (reporter, Gramps 4.0.3). **Likely already fixed:**
  current code guards both death-text sites with `if not probably_alive(...)` —
  gramps/gen/utils/alive.probably_alive is imported at detdescendantreport.py:54 and gates the
  death/burial output at lines 768–769 and 901–902. This bundle's job is to VERIFY whether the
  defect still reproduces on the target branch and, if it does not, close it with a regression
  guard rather than ship a speculative change.
- **Success criterion:** Generating a Detailed Descendant Report (or driving the report's
  death-text routine) for a person who is `probably_alive` and has no death event produces NO
  "Died …" line. If this already holds on maintenance/gramps61 (expected), the disposition is a
  no-fix close (already-fixed); a regression test that asserts the guard is the deliverable.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: report narrative emits death/burial text only for a person who is
  not probably alive.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** verify (and, only if it still reproduces, remove) the emission of death/burial
  narrative for a probably-alive, death-event-less person in the Detailed Descendant Report. /
  out of scope: the living-people privacy/option machinery (`run_living_people_option`); other
  reports unless the same routine is shared.
- **Repro instruction:** on maintenance/gramps61, with example.gramps, run Reports → Text →
  Detailed Descendant Report from a recent ancestor with living descendants (or seed a person
  born ~1990 with no death event); inspect whether any "Died ___ in ___" line appears for the
  living person.
- **Test file:** gramps/plugins/textreport/test/detdescendantreport_test.py (NEW if no
  test/ dir exists) OR a narrator-level test driving the production death-text path
  (principles.md §3.4) — Do selects the seam that exercises the shipped guard, not a copy.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** if a new core test .py is added, register it in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path
  `gramps/plugins/textreport/detdescendantreport.py` on upstream/maintenance/gramps61 — only
  Black reformat / license-text commits; the `probably_alive` guard predates them. The fix
  appears already present in the tree → verify-first.
- **Mantis:** 7814
- **Disposition hint:** POSSIBLY-FIXED → verify first
