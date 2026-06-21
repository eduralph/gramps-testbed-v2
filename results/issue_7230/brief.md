# Brief — issue 7230 / citation-tree-hides-sources-without-citations

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** citation-tree-hides-sources-without-citations
- **Defect:** As filed (v3.4.6): in the Citation Tree View, a source that has no citations
  does not appear in the tree at all — adding a new source and switching to the tree view shows
  nothing for it, so a freshly-created (citation-less) source is invisible and hard to manage.
- **Success criterion:** Every source is shown as a top-level node in the Citation Tree View,
  including sources that have zero citations (the source node exists whether or not it has
  citation children). **Verify-first**: Do MUST reproduce on maintenance/gramps61 before
  changing anything.
- **Invariant to restore:** The Citation Tree View lists every source as a parent node
  independent of how many citations reference it — a tree parent does not require children to
  exist. (Internal Gramps view-model rule; behavioural.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Scope:** how `CitationTreeModel` populates source (top-level) nodes,
  `gramps/gui/views/treemodels/citationtreemodel.py`. **Likely already fixed:** the model is
  now a two-cursor `has_secondary=True` model — the **primary** cursor iterates *all* sources
  (`citationtreemodel.py:83-85`: `number_items`/`map`/`gen_cursor` = `get_number_of_sources` /
  `get_raw_source_data` / `get_source_cursor`) and `add_row` (`:192-200`) adds each source as a
  top-level node, while the **secondary** citation cursor only adds citation children. Under
  that design every source appears regardless of citations, which is the opposite of the 2013
  report — so the defect appears closed by the tree-model refactor. Do should confirm a
  citation-less source is visible in the running view; if so, route to §6 (verify-first close,
  with a regression test if practical). / out of scope: the Citation **List** view; the
  source-list views.
- **Repro instruction:** On maintenance/gramps61: Sources category → Add a source (give it no
  citations) → switch the view to "Citation Tree View" → check whether the new source is listed.
- **Test file:** gramps/gui/views/treemodels/test/citationtreemodel_test.py — IF the source is
  still hidden, a data-layer test driving the **production** `CitationTreeModel` build against a
  db holding a citation-less source and asserting a top-level node exists for it; new `*_test.py`
  → `po/POTFILES.skip`. If sources already appear, no production patch — route to §6. A model
  test that needs a live `uistate`/GTK tree may be impractical headless → then it is a
  manual-verification §6 item.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/gui/views/treemodels/citationtreemodel.py` — history is JSON-data migration, attribute
  access, and black/license reformat; no targeted "show empty sources" commit, but the
  has_secondary source-cursor design already lists all sources. Closed-PR search by this path
  advised.
- **Mantis:** 7230
- **Disposition hint:** POSSIBLY-FIXED → verify first
