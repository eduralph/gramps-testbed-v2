# Brief — issue 13819 / editfamily-parent-family-order

> CLOSE-disposition brief. Plan verified the defect is already fixed and merged on the
> contribution target, so there is no patch to build — the bundle is carried straight to
> sign-off and discontinued. Keep the `- **Label:** value` field shape (driver-parsed).

- **Slug:** editfamily-parent-family-order
- **Defect:** Editing a family (e.g. adding a child) reordered the parent families of the
  edited family's children in the Relationships view. Cause: in `editfamily.save()` the
  original vs new child-ref lists were diffed by Python object identity, so equal-but-
  distinct instances marked every child both removed and re-added, losing family order.
- **Success criterion:** N/A (close) — no patch lands. Verified already fixed on the target
  branch: the diff now compares by handle (`set(ref.ref for ref in …)`), so an unchanged
  child list produces no remove/add cycle and order is preserved.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Scope:** none — no fix to author (already resolved upstream). / out of scope: everything.
- **Repro instruction:** a person with ≥2 parent families; edit one family, add a child, OK;
  observe the parent-family order change in the Relationships view.
- **Prior-art check (triage cycles):** searched by file path
  `gramps/gui/editors/editfamily.py` on canonical `upstream/maintenance/gramps61` —
  **MERGED**: commit `f7c6444a34` "Ensure family order is unaffected by family edits"
  ("Fixes #13819", by the note-1 author), an ancestor of `upstream/maintenance/gramps61`.
  Handle-based diff now present at editfamily.py:1322-1323.
- **Mantis:** 13819
- **Disposition hint:** likely-close — already fixed and merged on the contribution target
  (commit f7c6444a34, "Fixes #13819"). No actionable fix remains.

## STOP discipline

Draft only until Check sign-off. No patch, no PR — this bundle is a verified close.
