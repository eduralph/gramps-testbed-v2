# Brief — issue 13326 / gallerytab-iconlist-cleanup

> CLOSE-disposition brief. Plan verified the defect is already fixed and merged on the
> contribution target, so there is no patch to build — the bundle is carried straight to
> sign-off and discontinued. Keep the `- **Label:** value` field shape (driver-parsed).

- **Slug:** gallerytab-iconlist-cleanup
- **Defect:** On Forms-addon form close (Cancel), `GalleryTab.clean_up()` removed
  `self.iconlist` via `track_ref_for_deletion` without disconnecting the live
  `Gtk.IconView` `selection-changed` handler; a late emission re-entered
  `_selection_changed → get_selected() → self.iconlist.get_selected_items()` → `AttributeError: 'GalleryTab' object has no attribute 'iconlist'`.
- **Success criterion:** N/A (close) — no patch lands. Verified already fixed on the target
  branch: `clean_up()` now captures `_sel_changed_handler` at connect and disconnects it,
  guarded by `GObject.signal_handler_is_connected`.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Scope:** none — no fix to author (already resolved upstream). / out of scope: everything.
- **Repro instruction:** install Forms, configure a Source as a form, new form, switch to
  the gallery tab, add an image, select it, click Cancel (steveyoungs, Mantis note 4).
- **Prior-art check (triage cycles):** searched by file path
  `gramps/gui/editors/displaytabs/gallerytab.py` on canonical `upstream/maintenance/gramps61`
  — **MERGED**: commit `7afa8df737` "Fix AttributeError on iconlist when GalleryTab parent
  dialog closes" ("Fixes #13326"), an ancestor of `upstream/maintenance/gramps61`; was
  upstream PR 2330 (merged). Disconnect now present at gallerytab.py:241 (connect) and
  gallerytab.py:670-681 (`clean_up`).
- **Mantis:** 13326
- **Disposition hint:** likely-close — already fixed and merged on the contribution target
  (commit 7afa8df737, "Fixes #13326", upstream PR 2330). No actionable fix remains.

## STOP discipline

Draft only until Check sign-off. No patch, no PR — this bundle is a verified close.
