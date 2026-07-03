# Adversarial review — issue 8622 (citation-selector-filter-hides-citations)

Advisory only; never gates. Ground: `$PDCA_TARGET=/home/eddie/gramps/gramps` (read-only).

## Refutation attempts that FAILED (the fix held)

I tried hard to break the red→green story and the core logic, and could not:

- **Tautology check — refuted.** Traced the pre-fix behaviour of the fallback in
  `citationtreemodel_search_test.py:391` (`model_class = CitationTreeSelectorModel or CitationTreeModel`).
  With the fix reverted the test builds the plain `CitationTreeModel` and, for a `"Bible"` title
  search, the base secondary filter (`treebasemodel.py:480` `SearchFilter(func2, ...)` on the page
  column via `citationtreemodel.py:153` `citation_page`) drops both Bible citations, so
  `test_selector_keeps_citations_of_title_matched_source` fails on an empty child list — a genuine
  **behavioural** `AssertionError`, not the iteration-1 `TypeError`. Iteration-1 finding 2 is closed.
- **Production-path fidelity — refuted.** The search tuple `(False,(col,text,inv),False)` the test
  feeds matches exactly what the real dialog builds: `baseselector.py:328-334` reshapes
  `search_bar.get_value()` into `(flag, (col,text,inv), exact)` and `baseselector.py:347-355`
  constructs the model with `search=filter_info`. The filter `.match(handle, db)` contract
  (`_searchfilter.py:31`) and `_get_value`/`map2` wiring (`treebasemodel.py:961`) are the real ones.
- **Invariant completeness — refuted.** The citation-driven parent case (source pulled in only
  because a child citation matched) keeps its siblings: `_SourceGroupSearchFilter._source_shown`
  (patch.diff:108-115) unions title-match with `_sources_with_matching_citation`, and the secondary
  leg maps every citation to its parent source (patch.diff:117-125). Grouping is column-agnostic, so
  it holds for ID/author searches too. Iteration-1 finding 3 is addressed; the standalone view is
  pinned unchanged by `test_standalone_model_keeps_independent_secondary_search`.

## Findings a human should adjudicate

- **NEEDS-HUMAN — Patch baseline ≠ `$PDCA_TARGET`; the green evidence was demonstrated on a
  different tree.** The brief targets `maintenance/gramps61`, but `$PDCA_TARGET` is checked out on
  `master` (`git log`: `aef9f35ec6 "Gramps is still using GTK3"`), and the fix is **not present**
  there: `citationtreemodel.py` ends at line 235 (no `CitationTreeSelectorModel`),
  `selectcitation.py:40,67` still import/return `CitationTreeModel`, and
  `__init__.py:34` has no selector-model export. Worse, the POTFILES.skip hunk
  (`patch.diff:194-200`) uses a trailing context line
  `gramps/gui/views/treemodels/test/treebasemodel_test.py` that **does not exist** in the target —
  target `po/POTFILES.skip:456` has only `node_test.py` and the test dir contains only
  `__init__.py`/`node_test.py`. So that hunk will not apply cleanly to `$PDCA_TARGET`, and the
  C4/T2 "pass" rows in `check-gates.json` were produced against a tree that differs from the one
  under review (the gate itself flags "baseline tree drift: recorded detached@674e3b"). The
  reviewer's acceptance of C4/T2 as target-grounded is not warranted until the patch is confirmed to
  apply and re-run on this checkout.

- **NEEDS-HUMAN — The fix widens the secondary-filter crash surface to orphan citations.**
  Pre-fix, deciding a citation row touches only citation data (`citation_page`), and the parent
  source is loaded (`self.map(data.source_handle)`, `citationtreemodel.py:219`) **only** for
  citations that already passed the page filter. Post-fix, the secondary leg routes **every**
  citation through `_citation_source_handle` → `map2(handle).source_handle` → `source_filter.match`
  → `map(source_handle)` (patch.diff:117-125, 187-189). A citation with a dangling/deleted
  `source_handle` therefore triggers `get_raw_source_data` on a missing handle **during search**,
  regardless of whether its page matched — a `HandleError` path that pre-fix search never hit for
  non-matching citations. The fake DB (`citationtreemodel_search_test.py:310`, 3 clean rows, no
  orphans) cannot exercise this; a source/citation integrity test should.

- **NEEDS-HUMAN — Wiring (dialog→model) is asserted only in the green leg; nothing drives
  `build_tree` end-to-end.** `test_selector_wiring_uses_selector_model`
  (`citationtreemodel_search_test.py:479-480`) `skipTest`s whenever `CitationTreeSelectorModel` is
  absent, i.e. exactly in the C4 full-revert red leg — a skip is not a red. The behavioural tests
  import the model class directly and never call `SelectCitation.get_model_class` or
  `baseselector.build_tree`. Combined with `check-gates.json` C4-verify-interface =
  `unverifiable` (no dogtail repro), **no test exercises the real dialog build path**. A
  `get_model_class` typo is caught only because the green run would fail its `assertIs`; the brief's
  claim that iteration-1 finding 1 ("selector wiring untested") is *closed* is only partially true —
  it is guarded going forward but never proven via red→green.

## Advisory (non-blocking) note

- **Performance regression the row-count masks.** For a search matching no source title,
  `_sources_with_matching_citation` (patch.diff:92-106) scans the entire citation cursor once, and
  the secondary leg then does a source lookup per citation. On a real tree with thousands of
  citations this is a full extra table scan + per-row source fetch per keystroke-search; the 3-row
  fake DB cannot reveal it. Grouping correctness is fine — only the cost is untested.
