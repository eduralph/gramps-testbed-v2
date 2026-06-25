# Brief — issue 7984 / search-no-surname-typeahead

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** search-no-surname-typeahead
- **Defect:** The Ctrl+F type-ahead search in list views failed to find persons who have
  no surname: the user had to manually expand the "no surname" group folder before the
  search would reach those rows, and typing a given name did not locate them. Reported on
  a tree where no person has a surname.
- **Success criterion:** Confirm whether the reported repro still occurs on the current
  GUI: with a tree containing persons who have no surname (and a grouped People view),
  Ctrl+F type-ahead reaches and selects a no-surname person without the user first
  manually expanding the "no surname" group. Demonstrated by the committed AT-SPI repro
  running on the current target.
- **Invariant to restore:** n/a — non-structural behavioural / UX bug (principles.md §1.1).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui — selects the C4-verify-interface gate (the bug is only observable
  through the running People view's type-ahead search).
- **Difficulty:** medium
- **Scope:** verify the reported no-surname-folder type-ahead behaviour on the current
  code. The interactive search was reworked so `search_iter_slow()` traverses BOTH
  expanded and collapsed group rows and calls `expand_to_path()` on the match, which is
  the relevant change for the "can't reach the collapsed no-surname folder" complaint. /
  out of scope: a new patch; the residual design limitation that `search_equal_func()`
  matches only the configured search column (surname) with `startswith`, so a no-surname
  person still cannot be located by typing a GIVEN name — flag for the human as a
  separate UX decision, not this verify's reported behaviour.
- **Repro instruction:** Load a tree where persons have no surname (the issue's GEDCOM
  branch, or any tree with surname-less persons), open the People view, press Ctrl+F and
  type to find a surname-less person; observe whether the search reaches the collapsed
  "no surname" group and selects the person.
- **Test file:** engine/interface/test_bug_7984_search_no_surname.py — a committed
  AT-SPI/dogtail repro in the testbed mount (NOT in patch.diff), with a fixture tree at
  engine/interface/data/<TreeName>.gramps containing surname-less persons; subclasses the
  interface harness and drives the People-view type-ahead search. NOTE: verify-first has
  no patch, so the red↔green leg cannot run; the repro runs on the current target and the
  human verifies in the GUI at sign-off (`PDCA-UNVERIFIABLE` / manual verification
  expected).
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for any code it
  references.
- **New/removed files:** adds the committed repro under engine/interface/ (testbed mount,
  not the gramps package) → no POTFILES change.
- **Prior-art check (triage cycles):** searched gramps/gui/widgets/interactivesearchbox.py
  on the pinned worktree — `search_iter_slow()` documents and implements searching
  expanded *and* collapsed rows and auto-expands to the found path (lines ~443–481); this
  is the rework relevant to the reported "must open the folder manually" symptom. Possibly
  resolved — verify-first.
- **Mantis:** 7984
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
