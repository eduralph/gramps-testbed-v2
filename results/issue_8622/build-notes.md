# build-notes.md — issue 8622 / citation-selector-filter-hides-citations

Builder rationale (for the human; withheld from the reviewer). Target:
`gramps-project/gramps` @ `maintenance/gramps61` (checkout `gramps-6.1`).

## Success criterion (restated)

In "Select Source or Citation", a text search that matches a source must keep that
source's existing citations reachable (expandable/selectable), so an existing citation can
be reused instead of being forced to create a new one — without changing the standalone
Citation Tree View's independent secondary search.

## What the fix does

- **New `CitationTreeSelectorModel(CitationTreeModel)`** in
  `gramps/gui/views/treemodels/citationtreemodel.py`, wired into `SelectCitation`
  (`get_model_class`) only; the standalone view keeps plain `CitationTreeModel`.
- It overrides `set_search`: after the base builds the independent primary (source-title)
  and secondary (citation-page) filters, a **positive** plain text search is regrouped **by
  source**. `grouped_shown_sources(...)` computes the set of source handles to show — a
  source whose title matches, plus any source owning a citation whose page matches — and
  both the primary and secondary filters become a pure set-membership test
  (`_SourceGroupSearchFilter`) over that set. So a shown source keeps **all** its citations
  (title-matched or citation-matched), and its siblings stay reachable.

## Adversary findings addressed (beyond the shipped iteration-4)

1. **`skip`-set defeat (was NEEDS-HUMAN — now fixed).** `add_row2` force-adds a citation's
   parent source when a citation is added, which let the widened secondary filter resurrect
   a source the caller asked to hide via the public `BaseSelector` `skip` set. The model now
   **captures `skip` in `__init__`** (before `super().__init__` calls `set_search`, since
   the base does not otherwise retain it) and `grouped_shown_sources` **honours it**: a
   skipped source is never added to `shown`, and a skipped citation never pulls its source
   in. Mirrors the plain model, which hides skipped rows. Two new tests cover both the
   skipped-source and skipped-citation cases. (Today `SelectCitation`'s only caller passes
   no skip, so this was latent — now it is correct rather than documented-as-latent.)
2. **Empty-search-box double scan + wrong comment (fixed).** An empty search box yields a
   *truthy* `(col, "", inv)` tuple that the base treats as match-everything; the previous
   guard mis-described this and ran the full grouping scan (computing `shown` = all
   sources) on every dialog open. `set_search` now returns early when the search **text**
   is empty — no wasted cursor scan, correct comment. New test pins the full-tree result.
3. **Orphan citation (retained from iter-2/3).** `grouped_shown_sources` adds a citation's
   `source_handle` only when the source still exists, so a matching orphan citation never
   drives `add_row2` to dereference a missing source (`HandleError`). Covered by
   `test_selector_matching_orphan_citation_does_not_crash`.
4. **Inverted search (retained from iter-3).** Inverted ("does not contain") searches keep
   the base independent secondary filter, so a citation matching the excluded term stays
   hidden — grouping never overrides the citation-level exclusion. Covered.
5. **Wiring gap (retained from iter-1).** `test_selector_wiring_uses_selector_model` pins
   `SelectCitation.get_model_class()` to the selector model, so a wiring typo can't leave
   the behavioural tests green while the dialog stays broken.

## Tests & verification

`gramps/gui/views/treemodels/test/citationtreemodel_search_test.py` drives the **production
model-build path** (`CitationTreeSelectorModel(...search=...)` → `set_search`/`rebuild_data`)
against a lightweight in-memory DB and asserts on `model.tree` / node map. 9 tests: title
match, sibling reachability, orphan-no-crash, inverted-hides, skip-source, skip-citation,
empty-box full tree, standalone non-regression, wiring.

- **Verified in the Docker engine image** (`gramps-testbed:ubuntu-6.1.0`):
  - **RED** (production reverted, test kept): the reachability tests fail behaviourally
    (`[] != ['CIT_B1','CIT_B2']` and `['CIT_B1'] != ['CIT_B1','CIT_B2']`), the orphan test
    ERRORs with `HandleError` — the exact #8622 symptoms; skip/inverted/wiring skip
    (selector model absent), standalone + empty-box stay green.
  - **GREEN** (fix applied): all 9 pass.
- **Full core unit suite**: 32977 tests, only the 7 pre-existing baseline failures (zip
  imports + WebCal/NarrativeWeb, identical on the clean checkout). **Zero new regressions.**

## Citations (maintenance/gramps61)

- `gramps/gui/views/treemodels/treebasemodel.py:450-497` (`set_search` building
  `search`/`search2`), `:552-574` (`__rebuild_search` skip handling), `:294-367`
  (`__init__` calls `set_search` before `rebuild_data(skip=...)`).
- `gramps/gui/views/treemodels/citationtreemodel.py:202-224` (`add_row2` force-add-parent —
  the skip-defeat surface) + the appended `_SourceGroupSearchFilter`, `grouped_shown_sources`,
  `CitationTreeSelectorModel`.
- `gramps/gui/selectors/selectcitation.py` (`get_model_class` + import),
  `gramps/gui/selectors/baseselector.py:78,353` (`skip` public param → model).
- `gramps/gui/views/treemodels/__init__.py` (export), `po/POTFILES.skip` (test registration).
