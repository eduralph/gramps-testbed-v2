# Brief — issue 8622 / citation-selector-filter-hides-citations

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** citation-selector-filter-hides-citations
- **Defect:** In the "Select Source or Citation" dialog (Add Existing Citation…), the
  source/citation tree normally lets you expand a source and pick one of its existing
  citations. As soon as you type in the dialog's search/filter, the tree shows only
  source rows — the child citations disappear (no expander), so selecting a source is
  forced to create a NEW citation. The user can only reuse an existing citation if they
  do not search. Reported by clausimu and confirmed by sam888 (4.1.3).
- **Success criterion:** After the fix, applying a text search in the Select Source or
  Citation selector that matches a source keeps that source's existing citations
  reachable (expandable/selectable), so an existing citation can be added without forcing
  a new one. Demonstrable by a C4 test that builds the citation tree model with a search
  matching a source and asserts the source node still has its citation child rows (red
  pre-fix — citation children filtered out; green post-fix).
- **Invariant to restore:** Filtering a hierarchical source→citation selector must not
  make existing children unreachable under a parent that the filter keeps: if a source is
  shown, its citations remain selectable. (Gramps selector rule; no external canon — a
  text search currently filters the secondary/citation rows by the *same* column+text as
  the primary/source rows, so citations under a matching source are dropped because their
  page/volume text does not match the source title.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** high
- **Scope:** In the tree model that backs the selector, a text search applies the same
  match (column + text) independently to the secondary/citation rows as to the
  primary/source rows, so a search that selects sources filters those sources' citations
  out — leaving expandable sources with no visible citations. Keep child citations
  reachable under a source retained by the search. / out of scope: the sidebar filter
  (GenericFilter) path; changing the main Citation Tree View's search semantics if
  avoidable — the fix must NOT regress the standalone Citation/Place tree views (whose
  independent secondary search is intentional); the "little triangle"/expander styling.
  DESIGN NOTE for Do/Check: the correct locus (selector-only vs shared tree-model
  `set_search`) is a judgment call — prefer the change that does not alter the main tree
  views' behaviour; flag to the human if only a shared-model change is feasible.
- **Repro instruction:** On `maintenance/gramps61`, open a person, Source Citations tab →
  Add Existing Citation… → in the selector use the top search to narrow the list, click
  Find. The narrowed list shows only sources (no citation children to select); selecting
  one creates a new citation.
- **Test file:** `gramps/gui/views/treemodels/test/citationtreemodel_search_test.py`
  (existing core `test/` package, `*_test.py` suffix). The test MUST drive the production
  model-build path (`CitationTreeModel` with a `search=` tuple), not a reimplementation
  of the filter, and assert on the resulting node map / child rows (principles §3.4).
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause: `gramps/gui/views/treemodels/treebasemodel.py:466-482` `set_search`
  building `self.search2` for secondary rows with the same func/text as the primary
  `self.search`; selector build path `gramps/gui/selectors/baseselector.py:324-354`
  `build_tree` passing `search=filter_info` into
  `gramps/gui/views/treemodels/citationtreemodel.py:72-127`).
- **New/removed files:** adds
  `gramps/gui/views/treemodels/test/citationtreemodel_search_test.py` (a test, no
  translatable strings) → register in `po/POTFILES.skip`. No other `.py` added/removed.
- **Prior-art check (triage cycles):** searched
  `gramps/gui/views/treemodels/treebasemodel.py` and the selector on
  `upstream/maintenance/gramps61` — filter/black/license/crash-fix churn but no
  hierarchical-search reachability fix; no open/closed PR found for this defect. Not
  already upstream.
- **Mantis:** 8622
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Three adversarial findings require improvement before acceptance: 1. Selector wiring untested: the C4 test constructs CitationTreeModel directly and never exercises baseselector.py or selectcitation.py. A typo in get_model_kwargs() or a dropped ** in build_tree keeps all tests green while the user-visible bug persists in the dialog. A selector-level test or AT-SPI/dogtail interface repro is needed to close this gap. 2. Tautological pre-fix red: test_selector_keeps_citations_of_matched_source fails pre-fix with TypeError (unexpected keyword argument) rather than a semantic assertion about the defect. The companion test test_default_search_drops_citations partially mitigates this, but the primary C4 test should fail because of the wrong behaviour, not because the API does not exist yet. 3. Invariant only partially restored: the brief states "if a source is shown, its citations remain selectable." The fix holds for source-driven parents (source title matches search) but citation-driven parents (citation page matches, source forced in via add_row2 fallback) still leave sibling citations unreachable. The brief's invariant as stated is over-broad relative to what the patch delivers; either the fix must be extended to cover the citation-driven case or the brief/invariant must be narrowed to explicitly exclude it.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: The new secondary filter leg in _SourceGroupSearchFilter routes every citation through _citation_source_handle → map2(handle).source_handle → source_filter.match → map(source_handle), meaning a citation with a dangling/deleted source_handle will trigger get_raw_source_data on a missing handle during search — a HandleError path that pre-fix code never hit for non-matching citations. The fake DB in the test (3 clean rows, no orphans) cannot exercise this. The fix must guard against orphan citations in the secondary leg (e.g. catch HandleError / check handle existence before dereferencing) and add a test covering the orphan case.
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 3 — carry-forward (from the previous attempt)
- Sign-off rationale: Two substantive fixes required in CitationTreeSelectorModel: 1. Inverted-search regression: _SourceGroupSearchFilter.match must not discard the citation-level predicate for negative/inverted searches ("does not contain"). When the search rule is inverted, a citation whose page matches the exclusion term must not be shown — grouping by source cannot override the citation-level filter result. Fix the match logic so the citation-level predicate is applied before adding to the shown set. 2. Orphan guard half-delivered: an orphan citation whose page matches the search text currently gets its dangling source_handle added to shown unconditionally, causing HandleError in add_row2. The guard must cover the matching-orphan case (skip or safely handle citations with missing source handles) and a test must cover this path. "No new crash path" does not satisfy the iteration-2 requirement for a guard; the matching-orphan case must be explicitly handled and tested. Note: the C4 lane (gramps-6.1-lane2) is now clean — the dirty-worktree blocker is resolved for the next run.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — run-verify.sh: /home/eddie/gramps/gramps-6.1-lane2 has uncommitted or untracked changes — refusing to patch it
- Full previous attempt preserved in `iteration-v3/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
