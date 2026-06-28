# Brief — issue 10415 / familylines-graph-prunes-direct-ancestors

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** familylines-graph-prunes-direct-ancestors
- **Defect:** In the Family Lines Graph (Reports → Graphs), enabling "Try to remove extra
  people and families" removes *direct-line ancestors* of the person of interest when their
  surname spelling differs across generations. Root cause (verified):
  `remove_uninteresting_parents` (gramps/plugins/graph/gvfamilylines.py:664–822) keeps an
  ancestor only via a set of heuristics — among them a surname-equality test against each
  person of interest (lines 772–791: `surname_of_interest == surname or ==
  spouse_surname`). A top-of-tree direct ancestor with a single child of interest, no further
  kept parents, who is not themselves a person of interest, and whose surname spelling differs
  is dropped at lines 804–806. There is no "is a direct ancestor reached via parent links from
  a person of interest" criterion independent of surname text, so surname spelling drift prunes
  legitimate direct ancestors that "follow parents" had added.
- **Success criterion:** producing the Family Lines Graph with "follow parents" on and "Try to
  remove extra people and families" on retains every direct-line ancestor of the selected
  person of interest, regardless of surname-spelling changes between generations (the
  reporter's exclude.pdf matches include.pdf for the direct line). Demonstrable by C4-verify by
  driving the report's people/family-selection on a fixture tree.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: a direct-line ancestor included by "follow parents" is not removed
  by the extra-people pruning; ancestor membership is decided by lineage, not surname-string
  equality.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** the pruning decision that drops direct-line ancestors of a person of interest when
  surnames differ. / out of scope: surname-colour behaviour, the spouse/sibling inclusion
  heuristics for *non-ancestors*, and the "limit number of ancestors" option.
- **Repro instruction:** on maintenance/gramps61, import the reporter's tree (attach to the
  bundle) — or a tree where I0000's father/grandfather use spelling variants of the surname —
  select only I0000 as person of interest, follow parents+children, generate once with the
  remove option OFF and once ON; the ON output is missing direct ancestors present in the OFF
  output.
- **Test file:** gramps/plugins/graph/test/gvfamilylines_test.py (NEW). The fix needs a
  testable seam: the test MUST exercise the production people/family-selection routine
  (`find_parents` + `remove_uninteresting_parents` on a real db fixture), not a parallel copy
  of the pruning logic (principles.md §3.4). Do inverts the GUI-entangled report into a
  drivable unit.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** ADDS the test (and possibly a `test/__init__.py`) → register the new
  .py file(s) in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/graph/gvfamilylines.py`
  on upstream/maintenance/gramps61 — recent commit `Graph plugins: preserve date modifier in
  years-only mode` (115ff4da9a) + license text; neither touches the ancestor-pruning surname
  heuristic. Reported originally as #10400; no merged/closed fix found for this path.
- **Mantis:** 10415
- **Disposition hint:** likely-fix
