# Brief — issue 9267 / name-format-change-rebuilds-sort

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** name-format-change-rebuilds-sort
- **Defect:** Changing the Display Name format in Preferences refreshes what each row
  *shows* in a list view, but does NOT rebuild the list's **sort order**. Rows keep the
  ordering computed from the previous format until the database is reopened (which rebuilds
  the sort from the display name).
- **Success criterion:** After changing the Display Name format in Edit→Preferences→
  Display, the People (flat) list re-sorts according to the new display name without
  reopening the database.
- **Invariant to restore:** A list view's row order is consistent with the display-name
  format currently in effect — the same configuration change that triggers a row
  redisplay also refreshes the sort key. (Behavioural consistency invariant; rationale:
  the sort key is derived from the displayed name, so display and order must not diverge.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — a redisplay path exists; the change is to also invalidate/
  rebuild the sort cache on the name-format change, which a reviewer must trace from the
  preferences callback into the view's model.
- **Scope:** the missing sort-order rebuild when the active display-name format changes
  (the name-format change callback in `gramps/gui/configure.py` and the people-view model
  rebuild it should trigger). / out of scope: creating/editing/deleting custom name
  formats, the name-format editor UI, sorting of other columns.
- **Repro instruction:** example.gramps → People flat view → Edit→Preferences→Display →
  change "Name format" → Close. Display updates but row order is unchanged; reopen the DB
  → order is now correct (proving it is a sort-rebuild-on-change gap).
- **Test file:** engine/interface/test_bug_9267_name-format-sort.py (committed AT-SPI
  repro; `Surfaces: gui` → drives `C4-verify-interface`). If Do can reach the model's
  sort-rebuild through the production path headlessly, additionally ship a core
  `*_test.py` under the matching view `test/` package and have production route through the
  same unit the test drives (principles §3.4); otherwise record C4 (unit) as unverifiable
  for human sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected for the gramps tree (the interface repro lives in
  the testbed mount). If a core `*_test.py` is added, register it in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/gui/configure.py` on
  `upstream/maintenance/gramps61` — name-format model build/add/edit/delete exist, no
  sort-rebuild-on-format-change fix. No matching fork PR by this path. → unfixed.
- **Mantis:** 9267
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: _format_changed() calls self.model.rebuild_sort() on BasePersonView, which is shared with PersonTreeView; PersonTreeModel inherits TreeBaseModel, not FlatBaseModel, so rebuild_sort() is absent there and would raise AttributeError at runtime. Add a safety guard (hasattr check or no-op on TreeBaseModel) before shipping.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
