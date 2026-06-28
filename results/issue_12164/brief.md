# Brief — issue 12164 / verify-unique-surname-count-duplicate

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** verify-unique-surname-count-duplicate
- **Defect:** The Statistics gramplet shows "Unique surnames: 62" while double-clicking it
  (and the Top Surnames gramplet) reports "66" — the unique-surname total disagrees between
  the Statistics gramplet and the surname/filter count.
- **Success criterion:** Confirm 12164 is the **same defect** already captured by bundle
  6793 ("surname gramplets disagree on unique count") — the Statistics gramplet's
  `len(set(database.surname_list))` vs the recomputed surname/filter count — and resolve
  12164 as a duplicate of 6793 (and related 6988). No separate patch is produced here.
- **Invariant to restore:** (owned by 6793) the unique-surname total is computed one way
  and reported consistently across the surname/statistics gramplets and the matching
  filter. Behavioural consistency invariant.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low — duplicate determination only; no code change.
- **Scope:** verify 12164 is the same count-divergence as 6793 and close as duplicate. /
  out of scope: any fix to `statsgramplet.py` / the surname gramplets (that work belongs to
  bundle 6793); creating a new fix.
- **Repro instruction:** Dashboard → Statistics gramplet "Unique surnames" vs the
  double-click filter result / Top Surnames "total unique surnames" — the two numbers
  differ. (Identical symptom to 6793's repro.)
- **Test file:** none — duplicate disposition (no regression ships here; the regression
  belongs to bundle 6793). If Check requires an artifact, point at bundle 6793's test.
- **Citations expected:** cite `gramps/plugins/gramplet/statsgramplet.py` (the
  `len(set(database.surname_list))` "Unique surnames" line) and bundle `issue_6793` as the
  owning fix, establishing the duplication.
- **New/removed files:** none.
- **Prior-art check (triage cycles):** bundle `results/issue_6793` already targets this
  exact unique-surname count divergence (slug `surname-gramplets-disagree-on-unique-count`,
  Mantis 6793); bundle `issue_6988` covers the related patronymic/non-primary counting. →
  12164 is a duplicate, not a separate fix.
- **Mantis:** 12164
- **Disposition hint:** duplicate

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
