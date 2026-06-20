# Brief — issue 13920 / ftv-pango-extents-to-pixels

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** ftv-pango-extents-to-pixels
- **Defect:** FamilyTreeView crashes on launch with
  `TypeError: Pango.extents_to_pixels() takes exactly 2 arguments (1 given)` from
  `family_tree_view_canvas_manager.py:1265`, after a system Pango update. The root cause is
  an upstream GTK/Pango behaviour change (GNOME GTK issue 7651) surfacing in
  FamilyTreeView — an **external, experimental addon maintained outside addons-source**
  (ztlxltl/FamilyTreeView), not an addons-source target.
- **Success criterion:** Confirmed external + already fixed: FamilyTreeView v0.1.164 adds a
  fallback for the upstream Pango change (note 4), and the underlying GTK issue is tracked
  upstream. There is no patch.diff to carry (external repo, already fixed), so the bundle is
  discontinued as superseded, referencing the FTV v0.1.164 release and the upstream GTK
  issue.
- **Repo + branch target:** N/A — external repo (ztlxltl/FamilyTreeView). Not an
  addons-source / gramps-core target; nothing to branch or patch here.
- **Surfaces:** gui (external addon) — out of this repo's scope.
- **Scope:** confirm external ownership + the v0.1.164 fix, and close. / out of scope: any
  patch (the addon is not in addons-source); the Pango downgrade workaround (notes 2–3, a
  user stopgap); the upstream GTK fix.
- **Repro instruction:** Run FamilyTreeView (pre-v0.1.164) against a recent Pango; the
  crash fires on every FTV launch (note: external addon, reproduced by the reporter, not in
  this testbed's addon set).
- **Test file:** none — external repo; no testbed/addons-source artifact applies.
- **Citations expected:** n/a (no patch in scope).
- **Prior-art check (triage cycles):** FamilyTreeView is not in addons-source (it lives in
  ztlxltl/FamilyTreeView); fix shipped externally as FTV v0.1.164 (note 4), with FTV issues
  60/61 and upstream GTK issue 7651 tracking the cause. No addons-source path to search.
- **Mantis:** 13920
- **Disposition hint:** external

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — external repo, already fixed.
**Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by FamilyTreeView v0.1.164 (external fallback) + upstream GTK issue 7651 — per
INTEGRATION §7. No PR (not an addons-source / gramps-core target).
