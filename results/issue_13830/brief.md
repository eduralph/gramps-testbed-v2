# Brief — issue 13830 / graphview-path-to-home-keyerror

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** graphview-path-to-home-keyerror
- **Defect:** Graph View's "Show path to home person" makes the graph vanish and raises
  `KeyError` in `gramps/gen/filters/rules/person/_relationshippathbetween.py:130`
  (`new_rank = firstMap[person_handle]`). The traceback enters gramps core via the
  RelationshipPathBetween filter; the GraphView addon is only the caller.
- **Success criterion:** The core RelationshipPathBetween filter iterates the correct list
  so `firstMap[person_handle]` never raises `KeyError`, and "Show path to home person"
  renders the path. Already fixed in core on the target branch — the brief confirms the
  fixing commit is an ancestor of maintenance/gramps61; there is no patch.diff to carry
  (already-fixed-upstream in core, not an addon defect), so the bundle is discontinued as
  superseded, with the fixing commit and the test PR referenced.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core; the defect
  and fix are in gramps-core, not the GraphView addon)
- **Surfaces:** data (filter logic; the GUI symptom is downstream).
- **Scope:** confirm the core fix is present on gramps61 and close. / out of scope: any
  GraphView addon change; the user-side stale-uppercase-ini cleanup (note 3, a config-key
  casing change in addons-source commit 6357efb — separate, user cleanup).
- **Repro instruction:** On example.gramps in Graph View, right-click a non-home person and
  choose "Show path to home person." Pre-fix (regression from core commit 1280aa45a5) this
  raised the KeyError; post-fix the path renders.
- **Test file:** none in this bundle — core fix already merged. (A direct regression test
  for RelationshipPathBetween was filed separately as upstream gramps PR 2329; it ships in
  gramps core's own `test/` layout, not here.)
- **Citations expected:** n/a (no patch here). Fix present at
  gramps/gen/filters/rules/person/_relationshippathbetween.py — `init_list` now iterates a
  single list (firstMap keyed correctly), per commit 48a6cbfb05.
- **Prior-art check (triage cycles):** searched by file path
  gramps/gen/filters/rules/person/_relationshippathbetween.py — fixed by core commit
  48a6cbfb05 ("Fix regression in relationship path between people filter"), present on
  maintenance/gramps61; regression introduced by commit 1280aa45a5 ("Refactor, fix, and
  optimize filters/rules"). Shipped in 6.0.4–6.0.8 and 6.1.0-beta1.
- **Mantis:** 13830
- **Disposition hint:** upstream

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — the core fix is already merged.
**Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by core commit 48a6cbfb05 (regression test filed separately as upstream gramps
PR 2329) — per INTEGRATION §7. No new PR.
