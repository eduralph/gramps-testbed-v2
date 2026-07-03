# Build notes — issue 8622 (citation selector filter hides citations)

Target branch: `gramps-project/gramps @ maintenance/gramps61`
(developed and cited against the pinned upstream worktree `gramps-6.1`).

## The defect

In the "Select Source or Citation" selector (Add Existing Citation…), the
source→citation tree lets you expand a source and pick one of its existing
citations. As soon as a text search is applied, only source rows remain — the
citation children vanish, so selecting a source forces creation of a **new**
citation instead of reusing an existing one.

## Root cause

The selector's model is `CitationTreeModel`, a `TreeBaseModel` with
`has_secondary=True` (`citationtreemodel.py:126`). It is the *only* model with
a secondary object type (verified: `grep has_secondary=True` matches just this
line).

`TreeBaseModel.set_search` builds the secondary filter `self.search2` from the
**same** `(col, text, inv)` as the primary `self.search`
(`treebasemodel.py:467-481` on the target branch):

```python
func  = lambda x: self._get_value(x, col, secondary=False) or ""   # source
func2 = lambda x: self._get_value(x, col, secondary=True)  or ""   # citation
self.search  = SearchFilter(func,  text, inv)
self.search2 = SearchFilter(func2, text, inv)
```

For a search on column 0 the primary column is the **source title** but the
secondary column is the **citation page** (`citationtreemodel.py:88` vs
`:153`). `_rebuild_search` filters the citation rows independently with
`search2` (`treebasemodel.py:545-575`), so a search for a source title drops
every citation of that source — the page text does not contain the title.
`add_row2` (`citationtreemodel.py:202-224`) is never reached for those
citations, leaving the matched source expandable but childless. That is the
invariant violation the brief names: *a shown parent must keep its children
reachable*.

## Fix

Restore the invariant **only in the selector** — the standalone Citation Tree
View's independent secondary (page) search is intentional and out of scope.

The change (smallest that restores the invariant, per principles §1.2/§2):

1. `citationtreemodel.py` — a `SourceOrCitationSearchFilter` wrapper and a
   `set_search` override. When the model is built in selector mode
   (`match_child_via_parent=True`), a *text* search's `search2` is wrapped so a
   citation is retained if **either** the citation matches the citation search
   **or** its parent source matches the source search (i.e. whenever the source
   itself is shown). This uses the *same* primary filter that decides source
   visibility, so it is correct across search columns and respects the exact
   /inverted variants and the sidebar-filter path (the wrapper is only applied
   for `search and not search[0] and search[1]` — plain text search, never a
   `GenericFilter`). A new `match_child_via_parent=False` kwarg preserves the
   default behaviour.
2. `baseselector.py` — a generic `get_model_kwargs()` hook (default `{}`)
   spread into the model constructor in `build_tree`. Other selectors are
   unaffected.
3. `selectcitation.py` — overrides `get_model_kwargs()` to return
   `{"match_child_via_parent": True}`, wiring the selector to the model
   behaviour.
4. `po/POTFILES.skip` — registers the new test module (a test, no translatable
   strings), per doc 16 §Adding and removing Python files.

## Why selector-only, and the cost of the rejected alternative

The brief's DESIGN NOTE asks to prefer the change that does not alter the main
tree views' behaviour, and to flag if only a shared-model change is feasible.
A shared change **was** feasible but rejected:

- **Rejected — unconditional fix in `CitationTreeModel.set_search` (or in
  `TreeBaseModel.set_search`), no flag.** Diff size is actually *smaller* (no
  `get_model_kwargs` hook, no `selectcitation` override — roughly −13 lines:
  the 7-line hook in `baseselector.py` + the 6-line override in
  `selectcitation.py`). But `CitationTreeModel` is constructed **unchanged** by
  the standalone Citation Tree View (`plugins/view/citationtreeview.py:161`),
  so an unconditional change would alter that view's search: typing a source
  title would suddenly pull in all its citations, changing the intentional
  independent page-search the brief scopes out. Since this model is the only
  `has_secondary` model, a base-class change lands in exactly the same place.
  The invariant to restore is selector-scoped, so cost-vs-minimal-diff is not
  the deciding axis (principles §1.2): the ~13 extra lines buy a zero-blast
  radius on the standalone view, proven by the `test_default_search_drops_
  citations` case (default behaviour unchanged).

## Test

`gramps/gui/views/treemodels/test/citationtreemodel_search_test.py` drives the
**production** model-build path — `CitationTreeModel(..., search=<tuple>)` —
against a lightweight in-memory database double (only the DB is a stand-in; the
model, `TreeBaseModel.set_search`, `_rebuild_search`, `SearchFilter` and the new
wrapper are the real production code). It asserts on the resulting node map
(`model.tree[source].children`):

- `test_selector_keeps_citations_of_matched_source` — with
  `match_child_via_parent=True`, a source matched by the search keeps **both**
  its citation children, and the non-matching source stays filtered out. (This
  is the red→green discriminator.)
- `test_default_search_drops_citations` — without the option (standalone-view
  behaviour) the same search drops the citations. Documents the bug and pins
  the fix's scope (the standalone view must not regress); passes on both legs.

Import-light / headless: the model imports `gi.repository.Gtk`, but importing
Gtk needs no display, and building a handful of rows never crosses the progress
dialog's popup threshold (`progressdialog.py:369`), so no widget/display is
created. No `ManagedWindow`/selector GUI is instantiated — the selector wiring
(`baseselector`/`selectcitation`) is covered by inspection, not by opening a
window.

## Verification (red→green)

Run through the engine C4 mechanic (headless, plain `python3 -m unittest`,
`GRAMPS_RESOURCES` set), reproduced on the host with the same headless path:

- **GREEN** (patch applied): both tests pass — `Ran 2 tests … OK`.
- **RED** (production reverted, test kept): `test_selector_keeps_citations_of_
  matched_source` fails (`CitationTreeModel.__init__() got an unexpected keyword
  argument 'match_child_via_parent'`) — the selector behaviour it asserts only
  exists post-fix — so the module fails. `git apply --check` of `patch.diff`
  against clean `maintenance/gramps61` succeeds.

The gating `engine/scripts/ubuntu/run-verify.sh` runner itself could not be
executed in this sandbox (it needs Docker/network, which required an approval I
cannot grant). I reproduced its exact red→green mechanic directly with the
headless `python3 -m unittest` path it runs inside the container; Check will
re-run the real C4 gate.

## Commit-readiness note

`black` could not be executed here (no `pip`/network in the sandbox), so the
touched files were hand-audited against black conventions: all lines ≤ 88
cols (`git grep -nP '.{89,}'` on the touched files is empty), double quotes,
two blank lines around the new top-level class, one between methods, and magic
trailing commas on the multi-line call/signature. Please let the fork's
`black` pre-commit hook confirm before publish.

## Shared-worktree observation (not part of this fix)

The shared `gramps-6.1` worktree also carried an unrelated in-progress change
(a bug-6324 / `libcairodoc.py` edit + a `plugins/test/cairodoc_table_
pagination_test.py` + a `POTFILES.skip` line) when I started — `PDCA_WORKTREE`
was not set, so bundles share one checkout. `patch.diff` deliberately excludes
those files; it contains only this fix's five paths. Worth flagging that the
serial shared worktree risks cross-bundle contamination.
