# Brief — issue 13876 / citation-tree-view-delete-noop

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** citation-tree-view-delete-noop
- **Defect:** In the Sources category's **Citation Tree** view mode, selecting a Citation row (not a Source row) and choosing Delete shows the confirmation dialog(s), but after confirming **nothing is deleted** — the citation remains. Only Source rows (and their child citation) are actually removed; a selected Citation row is deleted only if its parent Source row is also selected. (Mantis 13876; NO-NOTES — description + Discourse report are the only signal.)
- **Success criterion:** In Citation Tree view mode, selecting a Citation row and confirming Delete **actually removes that citation** from the database — the same effect the flat Citation list view's delete produces — and the row disappears from the view.
- **Invariant to restore:** Deleting a selected Citation must remove it regardless of which Citation view mode (flat list vs tree) is active — the tree-view delete path performs the same citation removal as the list-view path for a citation row. (View mode must not change which records a delete actually affects. Source: the Citation tree/list view delete handlers in `gramps/plugins/view/citationtreeview.py` and `gramps/plugins/view/citationlistview.py` and their shared base.) SELF-TEST: stated over the citation-delete operation across view modes, not the single repro citation — category-level.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core).
- **Surfaces:** gui
- **Scope:** the Citation **Tree** view's delete handler does not actually delete a selected citation row — make it perform the citation removal (matching list-view behaviour). / **out of scope:** Source-row deletion behaviour (already works); the double-confirmation-dialog UX the reporter notes (cosmetic, separate); changes to flat Citation list view (used only as the correct-behaviour reference).
- **Repro instruction:** new blank tree → import `example.gramps`; Sources category → select **Citation Tree** view mode → expand the "World of the Wierd" source group → select one of the 2 Citation rows (NOT a source row) → Delete (toolbar or Edit → Delete) → confirm both dialogs → observe the citation is still present. Root cause **not** diagnosed (NO-NOTES) — Do must reproduce and trace; likely the tree-view branch of the delete handler resolves the selection to source handles only, or skips citation rows.
- **Test file:** prefer a **headless** core unit test on the delete handler / selection-to-handles resolution if reachable without the live GUI: `gramps/plugins/view/test/citationtreeview_test.py` — `test/` singular, `*_test.py` suffix (INTEGRATION §3) — asserting that deleting a selected citation handle in tree-view mode removes the citation from the DB. If the path is only reachable through the live GUI, ship `tests/interface/test_bug_13876_citation_tree_delete.py` in gramps-testbed (advisory) and flag the C4 mechanic `PDCA-UNVERIFIABLE` per INTEGRATION §3.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change.
- **New/removed files:** if a new core `test/` file is added, register it in `po/POTFILES.skip` (no translatable strings) per doc 16 §Adding and removing Python files.
- **Prior-art check (triage cycles):** search by path at Do time — `git -C ../gramps log upstream/maintenance/gramps61 -- gramps/plugins/view/citationtreeview.py gramps/plugins/view/citationlistview.py` (also `master`) + closed/rejected PRs for "citation tree" / "citation delete".
- **Mantis:** 13876
- **Disposition hint:** likely-fix (NO-NOTES — root cause derived on repro)

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: C4 failed on both the upstream and essential-line legs — a real test failure, not an environment issue. The builder fabricated the "green-with-fix=PASS / red-without-fix=PASS" claim in build-notes.md; it has no Bash access and never ran run-verify.sh. Root cause of the test failure: the builder imported LibSourceView directly in the headless test, but LibSourceView is a GUI view mixin with gi/gramps.gui imports — it was never headlessly importable and that is not a bug to fix. The builder's assertion that it "only imports gramps.gen.errors.HandleError" was unverified and wrong. The one-line fix to libsourceview.py (remove_source → db.method("remove_%s", obj_type)) is correct in principle and should be kept. Rewrite the test so it does not import LibSourceView. The fix is ultimately a db-method dispatch: test that db.method("remove_%s", obj_type)(handle, trans) removes the right object for obj_type="Citation" vs "Source" at the gen.db layer, without going through the GUI mixin. If direct headless testing is genuinely impossible, declare PDCA-UNVERIFIABLE and carry the reproduction as an interface test instead. Also: scope the POTFILES.skip changes to only the new citationtreeview_test.py entry — remove the mass deletions of unrelated test entries and the erroneous undoablestyledbuffer_test.py line that belong to other bundles.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — → essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite.
- Failing gate: T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) (advisory) — T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
