# Brief — issue 13716 / sidebar-filter-type-list-stale

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** sidebar-filter-type-list-stale
- **Defect:** A view's sidebar filter "Type" selector (the same widget the Filter
  Gramplet hosts) is populated with the database's custom types only once — when the
  sidebar-filter widget is first constructed at view open — and is never refreshed.
  Custom types added afterwards (e.g. a "GEDCOM import" Note type created by importing
  a GEDCOM with errors, or any custom type added by editing) do not appear in the
  selector, and stay absent even across a Gramps restart, until the gramplet/view is
  torn down and rebuilt. Confirmed by the maintainer (Mantis note 3): the editor
  dialogs rebuild their type selector "anew every time" and so show updates, but the
  sidebar filters build theirs once and "never update them again."
- **Success criterion:** After a custom type is added to the already-open database
  (e.g. importing records that create a new custom Note type), the corresponding
  sidebar filter's Type selector offers that new custom type without recreating the
  view; and the shipped regression test asserts that the selector's offered options
  reflect the database's current custom-type set after those types change — exercised
  through the production repopulate path, red before the fix (new type absent), green
  after.
- **Invariant to restore:** A UI selector whose contents are derived from the database
  (here, the custom type-name list) must reflect the database's current contents
  whenever it is presented to the user, not a snapshot frozen at widget-construction
  time. Stated over the category: the sidebar-filter type selectors (the shared
  `SidebarFilter` behaviour across the note/event/family/person/place/repo sidebar
  filters) must stay consistent with their source as the source mutates — the same
  consistency contract the editor-dialog type selectors already honour by rebuilding
  per use. Source: Gramps maintainer diagnosis, Mantis 13716 note 3 (the editor
  dialogs as the reference contract; the sidebar filters are the lone outlier).
  SELF-TEST: a single-module guard (fixing only `_notesidebarfilter.py`) does NOT
  satisfy this — the invariant spans all the sidebar filter type selectors.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61   (core fix → current maintenance line, forward-merged to master; INTEGRATION §2)
- **Surfaces:** gui   (the change is a GUI widget-lifecycle fix; the gating regression is the headless unit test on the repopulate seam, the advisory interface gate is secondary)
- **Scope:** make the sidebar-filter Type selectors present the database's current
  custom types when the filter is shown after those types change, restoring the
  consistency the editor dialogs already have — done once in the shared
  `SidebarFilter` path so all affected sidebar filters benefit, not patched per
  filter subclass. / out of scope: redesigning the filter UI; the non-type filter
  fields (ID/Text/Tag/generic-filter); the Isotammi Filter+ addon (this is the
  built-in core gramplet, per the original cross-reference); and any change to how or
  when the db layer stores/reads custom types (the db side is correct — note 3).
- **Repro instruction:** fixture: a fresh tree (or `example.gramps`). GUI steps
  (Mantis description + notes 1–2): start Gramps, create/load a tree, open the Notes
  category, and in the Filter Gramplet confirm the "Type" selector has no "GEDCOM
  import" entry. Import the John Cardinal `assess.ged` (note 2 attachment), which
  creates Note records with a custom "GEDCOM import" type. Re-open the "Type" selector
  — the custom type is absent (and remains absent after a full restart), appearing
  only after the gramplet is removed and re-added. Headless test repro: with an open
  db, construct the sidebar filter; add a custom note type to the db; invoke the
  production repopulate path; assert the new custom type is now among the selector's
  offered options (and absent before the fix).
- **Test file:** `gramps/gui/filters/sidebar/test/_sidebarfilter_test.py` (core
  convention — `test/` package, singular, with `<module>_test.py` suffix; Do creates
  the package `__init__.py`). The test MUST drive the PRODUCTION repopulate path —
  production routing through the same repopulate unit the test calls — NOT a parallel
  copy that mirrors it (principles.md §3.4). Keep the seam as display-light as the
  widget allows so the red→green runs under the gramps GUI test harness the other
  `gramps/gui/.../test/*_test.py` files use.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** adds `gramps/gui/filters/sidebar/test/__init__.py` and
  `gramps/gui/filters/sidebar/test/_sidebarfilter_test.py` — both have no translatable
  strings → register in `po/POTFILES.skip`. If the fix factors out a new non-test core
  `.py`, place it per its content (translatable strings → `POTFILES.in`, else
  `POTFILES.skip`); the fix is expected to stay within the existing sidebar-filter
  modules, so no new production file is anticipated.
- **Prior-art check (triage cycles):** searched by file path on
  `upstream/maintenance/gramps61` (also `master`) for
  `gramps/gui/filters/sidebar/_notesidebarfilter.py`, `_placesidebarfilter.py`, and
  the shared `_sidebarfilter.py` — no refresh/rebuild fix merged; every sidebar filter
  still caches `dbstate.db.get_*_types()` once in `__init__` (note/event/family/person/
  place/repo, object-level verified). Upstream PR 809 ("enhanced places", maintainer
  note 3) added a place-only refresh but was never generalized and is not present on
  gramps61 (the place filter still caches once there). No `fix/bug-13716*` branch on
  the fork; no merged/closed upstream PR found on these paths. → not fixed upstream;
  actionable.
- **Mantis:** 13716
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: 1. _reposidebarfilter.py must use get_repository_types() instead of get_event_types(). The correct db method exists (base.py:826); the pre-existing wrong method was preserved by the patch but the goal is a working Type selector, so fix it here. 2. Add an interface repro test (engine/interface/test_bug_13716_*.py) so the GUI red→green gate is verifiable in the next Check pass. Notes carried forward: essential dependency on headless-ut-segfault (upstream PR #2357) must land first; §6.3 (MonitoredDataType.sel always StandardCustomSelector) is verified clear.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
