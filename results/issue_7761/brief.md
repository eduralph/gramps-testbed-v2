# Brief — issue 7761 / date-column-sort-grouping

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** date-column-sort-grouping
- **Defect:** In the People view's birth-date column, dates that are *not* fully specified
  (year-only, "about YYYY", "before/after YYYY", "between …") collapse to the same numeric
  `Date.sortval` as the plain year, so within a year they appear in an arbitrary, unstable order.
  A developer (bubblegum, ~0039370) confirmed the cause: "all other dates are actually converted
  to the same numerical sort_value", needing a sort value that takes the date pre-descriptor /
  modifier into account. The reporter wants such same-year dates **grouped consistently** by
  qualifier rather than interleaved in arbitrary order.
- **Success criterion:** N/A — **do not contribute a fix from this bundle.** A developer
  (aviansid, ~0070543, 2026-04-26) has an **open upstream PR (upstream PR 2264)** implementing a
  modifier-aware date sort value for exactly this issue. Opening our own change would duplicate
  active upstream work and collide with that PR. The prior-art search (fork-discipline §5: span
  open upstream PRs) finds it, so the disposition is to defer.
- **Invariant to restore:** N/A — the property (a stable, modifier-aware ordering for partial /
  approximate dates sharing a year) is being addressed by the open upstream PR; this is a
  duplicate-of-upstream disposition, not an independent fix to design here.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Scope:** none — triage disposition (defer to the open upstream PR), not a fix. / out of
  scope: changing `Date.get_sort_value()` / `Date.sortval` (`gramps/gen/lib/date.py`) or the
  people-view birth-date column sort key — that is precisely what the open upstream PR touches;
  re-implementing it here would conflict.
- **Repro instruction:** People category view → sort the Birth Date column → within a single
  year, observe year-only / "about" / "before" / "after" dates ordered arbitrarily (all share
  one `sortval`) rather than grouped consistently.
- **Test file:** none (no patch — deferred to upstream PR 2264).
- **Citations expected:** n/a.
- **Prior-art check (triage cycles):** open **upstream PR 2264** (aviansid, 2026-04-26)
  addresses this issue directly; `gramps/gen/lib/date.py` `sortval` is otherwise long-standing
  with no merged modifier-grouping change on maintenance/gramps61. Defer rather than duplicate.
- **Mantis:** 7761
- **Disposition hint:** duplicate
