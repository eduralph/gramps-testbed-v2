# Keep a matched source's existing citations reachable in the citation selector

## Root cause

The base tree model builds **independent** primary (source) and secondary (citation) search
filters on the same column and text (`TreeBaseModel.set_search`
— `gramps/gui/views/treemodels/treebasemodel.py:450`). In the "Select Source or Citation"
dialog, a search that matches a source *title* therefore also filters the citation rows by
that same title text — and since a citation's page rarely contains the source title, every
citation under a matched source is dropped. The source shows with no expandable children, so
the user is forced to create a **new** citation instead of reusing an existing one
(Mantis 8622).

## Fix

Introduce `CitationTreeSelectorModel` (a subclass of `CitationTreeModel` wired to the
selector only) that regroups a **positive** plain text search **by source**:

- A source is shown if its own title matches the search, or if one of its citations' pages
  matches; then **all** of that source's citations stay reachable underneath it (its
  siblings too). The primary and secondary filters become a pure set-membership test
  (`_SourceGroupSearchFilter`) over the precomputed set of shown sources.
- The standalone Citation Tree View keeps the plain `CitationTreeModel` unchanged; an
  **inverted** ("does not contain") search keeps the base model's independent citation-level
  exclusion, so a citation matching the excluded term stays hidden.
- Guards: an **orphan** citation (source deleted) never drives `add_row2` to dereference a
  missing source handle, and the selector's public `skip` set is honoured — grouping cannot
  resurrect a hidden source/citation via `add_row2`'s force-add-parent fallback. An empty
  search box short-circuits (no wasted regrouping scan).

## Verified against

- `gramps/gui/views/treemodels/treebasemodel.py:450` — `set_search` builds `search`/`search2`
  independently on the same column/text (the root cause); `:552` — `__rebuild_search` applies
  the `skip` set at row level.
- `gramps/gui/views/treemodels/citationtreemodel.py:202` — `add_row2`'s force-add-parent
  fallback (the surface that both drops citations and, unchecked, defeats `skip`). The new
  `CitationTreeSelectorModel`, `_SourceGroupSearchFilter`, and `grouped_shown_sources()` are
  appended to this module.
- `gramps/gui/selectors/selectcitation.py` — `get_model_class` now returns
  `CitationTreeSelectorModel`; `gramps/gui/selectors/baseselector.py:78,353` — the public
  `skip` parameter flows into the model.
- `gramps/gui/views/treemodels/__init__.py` — exports the new model.
- `po/POTFILES.skip` — registers the new test file (no translatable strings).

## Test

`gramps/gui/views/treemodels/test/citationtreemodel_search_test.py` drives the production
model-build path (`CitationTreeSelectorModel(...search=...)` → `set_search()`/`rebuild_data()`)
against a lightweight in-memory database and asserts on the resulting node map — 9 tests:
title-matched source keeps both citations, citation-matched source keeps its siblings, orphan
citation doesn't crash, inverted search stays exclusive, skipped source not resurrected,
skipped citation not resurrected, empty search shows the full tree, standalone non-regression,
and selector wiring.

Without the fix the reachability tests fail behaviourally (`[] != ['CIT_B1','CIT_B2']` for a
title match; `['CIT_B1'] != ['CIT_B1','CIT_B2']` for the sibling case) and the orphan test
errors with `HandleError` — the exact #8622 symptoms; with the fix all 9 pass. The full core
unit suite passes with no new failures.

Fixes #8622
