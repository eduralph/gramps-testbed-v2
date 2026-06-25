# Brief — issue 3068 / detdescendant-duplicate-person-number

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** detdescendant-duplicate-person-number
- **Defect:** In the Detailed Descendant Report, a person reachable by two descent paths
  (e.g. the child of two first cousins) was assigned the descendant reference number from
  the LAST path visited rather than the first, so the "is the same person as [N]" line
  cited the wrong number. Reported on 4.1.0 (originally ~3.1).
- **Success criterion:** For the reported repro (default Henry numbering, "Omit duplicate
  ancestors" unchecked) a duplicated descendant keeps the smaller/first reference number
  and the "same person as" line cites it correctly.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** confirm the reported (Henry / default numbering) case is fixed and not
  regressed. / out of scope: a new patch — PR #100 already merged the Henry-filter
  keep-the-smaller-number guard; the d'Aboville (`apply_daboville_filter`, line ~294) and
  Modified-Henry (`apply_mhenry_filter`, line ~271) paths still assign `dnumber`
  unconditionally and may exhibit the same wrong-number behaviour for those numbering
  modes — note this for the human as a possible residual, but it is NOT this issue's
  reported repro (which uses the default Henry numbering).
- **Repro instruction:** Import the issue's bug.gramps (cousins-have-a-child structure),
  centre on person "a", run Reports → Text → Detailed Descendant Report with "Omit
  duplicate ancestors" unchecked, and check the trailing "is the same person as [N]"
  reference number against the person's own number.
- **Test file:** gramps/plugins/textreport/test/detdescendantreport_test.py (new) — a
  regression that runs the report (or drives the Henry-numbering filter) on a small
  in-memory tree and asserts the duplicate keeps the first/smaller number. NOTE: the fix
  is already in the tree, so there is no patch to revert — the C4 red→green mechanic
  cannot run (`PDCA-UNVERIFIABLE` → §6 NEEDS-HUMAN, expected for verify-first); if a
  report-level assertion proves impractical, this becomes a manual verification at
  sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61.
- **New/removed files:** adds gramps/plugins/textreport/test/__init__.py (the dir exists
  but is empty) and detdescendantreport_test.py — neither has translatable strings →
  po/POTFILES.skip.
- **Prior-art check (triage cycles):** searched
  gramps/plugins/textreport/detdescendantreport.py history on the pinned worktree —
  PR #100 (merge commit 9a516b1, "bug3068", SNoiraud) added the keep-the-smaller-number
  guard in `apply_henry_filter` (present at lines ~239–243 on maintenance/gramps61).
  **Reported Henry case already fixed** — this is verify-first.
- **Mantis:** 3068
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: C4 hard-fails in the automated run-verify.sh runner ("essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite"). The builder's manual out-of-band green is not sufficient — the automated gate must pass. Diagnose why the test fails under run-verify.sh on the 6.1 tree and fix either the test or the runner invocation so C4 goes green in the automated check.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — → essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
