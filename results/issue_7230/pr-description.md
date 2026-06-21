# Regression guard for citation-less sources in Citation Tree View

## Root cause
The original 2013 defect (bug 7230) existed because the CitationTreeModel used a single-cursor design where sources were only materialized as a side effect of iterating citations — a source with no citations never got a node. The current `maintenance/gramps61` tree model has been refactored to use a two-cursor `has_secondary=True` design, which decouples source visibility from citation count.

## Fix
No production code change is required — the defect is already fixed. This PR ships a regression test (`gramps/gui/views/treemodels/test/citationtreemodel_test.py`) that drives the **production** `CitationTreeModel.__init__` against an in-memory database holding both a cited source and a citation-less source, and verifies that both appear as top-level nodes. The test is registered in `po/POTFILES.skip` per the translation-file conventions.

## Verified against
- `gramps/gui/views/treemodels/citationtreemodel.py:83-85` — the primary cursor binding (`number_items` / `map` / `gen_cursor` to `get_number_of_sources` / `get_raw_source_data` / `get_source_cursor`); sources are enumerated independent of citations.
- `gramps/gui/views/treemodels/citationtreemodel.py:192-200` — `add_row` adds **every** source as a top-level node unconditionally (`self.add_node(None, handle, sort_key, handle)`), with no dependence on citation count.
- `gramps/gui/views/treemodels/citationtreemodel.py:202-224` — the secondary citation cursor only adds citation *children* via `add_row2`; the else-branch defensively back-fills sources only if the primary cursor failed (now unreachable).

## Test
The regression test (`gramps/gui/views/treemodels/test/citationtreemodel_test.py`, new):

- `test_citationless_source_is_a_top_level_node` — verifies a source with zero citations is present as a top-level node with no children.
- `test_every_source_is_listed_independent_of_citations` — verifies both a cited and a citation-less source appear as top-level nodes; the citation is a *child* of its source, not a top-level node.

The test runs headless with `uistate=None` (the `ProgressMonitor` only shows a dialog when operations exceed the popup threshold; a one/two-row database completes instantly, so no display is needed). Red→green verification cannot run on this bundle — there is no production line whose removal re-hides the source, so reverting `po/POTFILES.skip` alone leaves the test green. This is the expected signature of an already-fixed defect; the test ships as a durable guard against a future regression to the pre-refactor coupling.

Fixes #7230
