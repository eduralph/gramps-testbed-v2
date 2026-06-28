# Brief — issue 13876 / citation-tree-delete-citation

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** citation-tree-delete-citation
- **Defect:** In the Citations view's **Citation Tree** view mode, selecting a citation
  row and choosing Delete does not actually delete the citation. Two confirmation dialogs
  appear but the citation remains after confirming.
- **Success criterion:** Deleting a selected citation row in the Citation Tree view mode
  removes that citation from the database (it is gone from the view and the DB after the
  confirmation), the same as deletion behaves in the flat Citations list.
- **Invariant to restore:** A delete action on a selected row removes exactly the object
  that row represents — in the tree mode the selected node is resolved to its citation
  handle and that citation is deleted. (Behavioural / reference-integrity invariant;
  rationale: the tree groups citations under sources, so the delete path must distinguish
  and act on the citation node, not no-op or act on the wrong level.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — confined to the Citation Tree view's delete handling
  (`citationtreeview.py` has `_citation_row_delete` / `_source_row_delete`), but a reviewer
  must confirm the selected-node→handle resolution and the two-dialog flow.
- **Scope:** the failed citation deletion in
  `gramps/plugins/view/citationtreeview.py` (the citation-row delete path) when invoked
  from the tree view mode. / out of scope: source-row deletion, the flat Citations list
  view, the confirmation-dialog duplication (a separate cosmetic note in the report),
  drag/drop.
- **Repro instruction:** create a blank tree, import example.gramps → Sources category →
  Citation Tree view mode → expand the "World of the Wierd" source group → select one of
  its **citation** rows (not the source row) → click Delete (or Edit→Delete) → confirm →
  the citation is still present.
- **Test file:** engine/interface/test_bug_13876_citation-tree-delete.py (committed
  AT-SPI repro; `Surfaces: gui` → `C4-verify-interface`). If the row-delete path is
  reachable headlessly, additionally ship a core `*_test.py` driving the production
  `_citation_row_delete` (principles §3.4); otherwise record C4 (unit) unverifiable for
  human sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected for the gramps tree; a new core `*_test.py` →
  `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path
  `gramps/plugins/view/citationtreeview.py` on `upstream/maintenance/gramps61` — only
  https/black/license commits; no delete-citation fix. No matching fork PR by this path. →
  unfixed.
- **Mantis:** 13876
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
