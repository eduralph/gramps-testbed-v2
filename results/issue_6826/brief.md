# Brief — issue 6826 / topsurnames-representative-wrong-surname

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** topsurnames-representative-wrong-surname
- **Defect:** The Top Surnames gramplet stored a person as the *representative* for every
  group name from their primary AND alternate names, then the Same Surnames quick view
  re-derived the surname from that representative's PRIMARY name. So double-clicking a
  surname that was only an alternate name of the chosen representative opened the report
  for a different surname. Reported repro: person with primary A + alternate B, plus a
  person with primary B; clicking "B" showed "People sharing the surname 'A'".
- **Success criterion:** For the reported repro the Same Surnames quick view opens for
  the clicked surname (B) and lists the matching people, not the representative's primary
  surname (A).
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data — the representative-selection logic is now a module-level helper
  testable without GTK or a live DB.
- **Difficulty:** low
- **Scope:** confirm the reported repro now resolves to the clicked surname. / out of
  scope: a new patch — commit e39dc09e2e already reworked representative selection to
  prefer a person whose PRIMARY group name matches the surname; the residual case where a
  surname appears ONLY as an alternate name (no person has it as primary) still re-derives
  from the representative's primary name in samesurnames.py `run()` — note this for the
  human as a deeper, separate concern, not this issue's reported repro.
- **Repro instruction:** Build a tree with person P1 (primary surname A, alternate B) and
  person P2 (primary surname B). Open the Top Surnames gramplet, double-click "B", and
  confirm the quick view title/content is for surname B.
- **Test file:** gramps/plugins/gramplet/test/topsurnamesgramplet_test.py (exists,
  extend) — assert `record_surnames()` picks a primary-matching representative for B
  regardless of iteration order. NOTE: the fix is already in the tree, so there is no
  patch to revert — the C4 red→green mechanic cannot run (`PDCA-UNVERIFIABLE` → §6
  NEEDS-HUMAN, expected for verify-first); the test still ships and must pass.
- **Citations expected:** Do must cite path:line on maintenance/gramps61.
- **New/removed files:** none (extends existing topsurnamesgramplet_test.py).
- **Prior-art check (triage cycles):** searched
  gramps/plugins/gramplet/topsurnamesgramplet.py history on the pinned worktree — commit
  **e39dc09e2e** "Fix Top Surnames gramplet opening report for the wrong surname"
  ("Fixes #11101", the same behaviour) reworked `record_surnames()` (lines ~54–78) to
  prefer a representative whose primary surname matches. **Reported case already fixed**
  — this is verify-first; 6826 is effectively a duplicate of 11101.
- **Mantis:** 6826
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
