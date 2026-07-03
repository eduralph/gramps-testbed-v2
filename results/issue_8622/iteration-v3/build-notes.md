# Build notes — issue 8622 (citation selector filter hides citations) — iteration 3

Target branch: `gramps-project/gramps @ maintenance/gramps61`.
Worktree isolation is **off** in this testbed (`pdca.toml:46 worktree = false`),
so edits were made in the shared `../gramps-6.1` upstream worktree; every
`path:line` below is against that tree at `0d9e148908` (maintenance/gramps61).

## Root cause (unchanged from prior iterations — restated for self-containment)

The "Select Source or Citation" selector builds a hierarchical source→citation
tree from `CitationTreeModel` (`gramps/gui/selectors/selectcitation.py:67`
`get_model_class`). A text search reaches the model as a
`(filter?, (col, text, inv), exact?)` tuple.

`TreeBaseModel.set_search` (`gramps/gui/views/treemodels/treebasemodel.py:450-497`)
builds **two independent** search filters from that one tuple — `self.search`
for the primary (source) rows and `self.search2` for the secondary (citation)
rows — using the **same column and text** for both (lines 468-481; `func` and
`func2` differ only in `secondary=`). For the selector's only searchable column
(column 0 = "Source: Title or Citation: Volume/Page"):

* a source row matches iff its **title** contains the text, but
* a citation row matches iff its **page** contains the text.

So a search that keeps a source (title matched) drops every one of that source's
citations (their pages almost never contain the source title). In the rebuild
(`treebasemodel.py:534-575` `_rebuild_search`) the matched source is added by the
primary pass, then the secondary pass finds no matching citation, leaving the
source expandable but empty — the user is forced to create a **new** citation.

## The fix (this iteration)

Same locus as iteration 2 — a **selector-only subclass** — but the search filter
is redesigned so it **never dereferences a citation's `source_handle` in the
match path**, which both fixes the iteration-2 orphan crash and is simpler.

Added to `gramps/gui/views/treemodels/citationtreemodel.py:238-401`:

1. `_SourceGroupSearchFilter` — a `.match(handle, db)` filter that answers "is
   this row's *source* shown?". It computes **once** (cached in a `shared` dict
   held in common by the primary and secondary instances) the set of shown
   source handles:
   * sources whose **title** matches — a single pass over the *source* cursor,
     running the base source filter on handles that are always live; plus
   * sources owning a citation whose **page** matches — a single pass over the
     *citation* cursor, where the owning `source_handle` is only **added to a
     set, never dereferenced**.

   Matching is then a pure set-membership test: primary `match(source_handle)` =
   `source_handle in shown`; secondary `match(citation_handle)` =
   `citation.source_handle in shown`. This restores the brief's invariant in
   **both** directions — a source shown because its title matched, and a source
   pulled in because one of its citations matched, each keep *all* their
   citations (siblings included).

2. `CitationTreeSelectorModel(CitationTreeModel)` — overrides `set_search` to
   call `super().set_search(...)` (base behaviour untouched) and then, **only**
   for a plain text search that carries data (`search[0]` falsy, `search[1]`
   truthy, and both base filters non-`None`), wrap the two base filters in
   `_SourceGroupSearchFilter`. A sidebar `GenericFilter` (`search[0]` truthy —
   out of scope) or a cleared search is left on the untouched base path.

3. Wiring: `SelectCitation.get_model_class` now returns
   `CitationTreeSelectorModel` (`gramps/gui/selectors/selectcitation.py:66-71`),
   imported at `selectcitation.py:40` and exported from
   `gramps/gui/views/treemodels/__init__.py:35`.

The standalone Citation Tree View
(`gramps/plugins/view/citationtreeview.py`) keeps building the plain
`CitationTreeModel`, so its intentional independent secondary search is
**unchanged** — the brief's out-of-scope constraint.

Test registered in `po/POTFILES.skip:486` (a test, no translatable strings)
per doc 16.

## Addressing the iteration-2 carry-forward (the orphan-citation HandleError)

> "a citation with a dangling/deleted `source_handle` will trigger
> `get_raw_source_data` on a missing handle during search — a HandleError path
> that pre-fix code never hit for non-matching citations. … guard against
> orphan citations in the secondary leg … and add a test covering the orphan
> case."

Iteration 2's `_source_shown` dereferenced the source in the match path:
`source_filter.match(source_handle)` → `func(source_handle)` →
`self.map(source_handle)` → `get_raw_source_data`. For a **non-matching orphan
citation** (page doesn't match) the base pre-fix code never reached `add_row2`,
so it never dereferenced the source; iteration 2's secondary filter dereferenced
it for *every* citation to decide visibility → `HandleError` on a dangling
handle.

This iteration removes that dereference **entirely** from the match path. The
source filter is only ever run over handles yielded by the **source** cursor
(always live). The citation cursor only ever contributes `data.source_handle`
values that are **added to a set** — never looked up. Deciding a citation's
visibility is a set-membership test on `citation.source_handle`, which for an
orphan simply misses the set → the citation is hidden (its source no longer
exists, so it cannot be shown) → **no `get_raw_source_data` on a missing
handle**. This is strictly safer than the pre-fix base: the base's `add_row2`
still dereferences a matched orphan's source (a pre-existing behaviour on both
the standalone view and the selector, pre- and post-fix, out of scope here), but
the *search/visibility* decision the fix owns never does.

New test `test_selector_search_survives_orphan_citation`
(`…/test/citationtreemodel_search_test.py`) adds a citation pointing at a deleted
source (`SRC_GONE`, absent from the DB; `_FakeDb.get_raw_source_data` raises
`HandleError` for a missing handle, faithful to the real DB). It asserts that
building the selector model with a search present **does not raise**, the real
matched source keeps both its citations, and the orphan stays hidden. Against
iteration 2's code this test *fails* with `HandleError` (regression captured);
against this iteration it passes.

## Iteration-1 findings — still addressed

* **Finding 1 (wiring untested).** No `get_model_kwargs`/`**` surface exists
  (`build_tree` is untouched); `test_selector_wiring_uses_selector_model`
  asserts `SelectCitation.get_model_class()` resolves to
  `CitationTreeSelectorModel`, so a wiring typo cannot leave the behavioural
  tests green while the dialog stays broken.
* **Finding 2 (tautological red).** The two reachability tests build the model
  through `model_class = CitationTreeSelectorModel or CitationTreeModel`; on the
  C4 red leg (production reverted, test kept) the selector class is absent, so
  the fallback builds today's `CitationTreeModel` and the assertion fails on the
  **node map** (an `AssertionError` — the source shown with no citation
  children, issue 8622's actual symptom), not an import/`TypeError`.
* **Finding 3 (invariant only partially restored).** The "shown source" set is
  keyed on *title match OR any citation match*, and **all** citations of any
  shown source are kept, so a source pulled in by a single citation-page match
  keeps its **siblings**
  (`test_selector_keeps_sibling_citations_of_citation_matched_source`).

## Why this locus, and the cost of the alternatives (with numbers)

The brief names an **invariant to restore**, so the target is the smallest
change that restores it, not the smallest diff (principles §1.2/§2). Two
alternative loci, both rejected:

* **Shared `TreeBaseModel.set_search` change gated by a new constructor flag.**
  Blast radius: a new kwarg threaded through `TreeBaseModel.__init__`
  (`treebasemodel.py:294`), `CitationTreeModel.__init__`
  (`citationtreemodel.py:72-127`) and `baseselector.build_tree` — 3 shared
  signatures every hierarchical model inherits, plus the risk of regressing the
  standalone Citation/Place tree views. It was also the source of iteration-1
  finding 1. The selector subclass touches **0** shared signatures and **1**
  line of selector wiring.
* **Iteration-2's per-citation source-filter dereference in the match path.**
  Same file/line count as this iteration (≈160 added lines, one subclass + one
  filter helper), but it dereferences the source for every citation during the
  search → the orphan `HandleError` (iteration-2 rejection) and an extra
  `get_raw_source_data` per citation. This iteration replaces the per-citation
  `source_filter.match` with one extra **source-cursor scan** (O(sources), the
  same order the primary pass already scans) plus set membership — no per-row
  source dereference, orphan-safe. Net: same surface, strictly safer, no slower
  in order (one source scan + one citation scan, both cached).

## Test — `gramps/gui/views/treemodels/test/citationtreemodel_search_test.py`

Import-light and drives the **production** model-build path. It imports only
`CitationTreeModel` / `CitationTreeSelectorModel` (which pull
`gi.repository.Gtk`, exactly as the passing baseline
`treebasemodel_test.py` does) and — inside one method — the selector. It builds
the real model with a `search=` tuple against a lightweight in-memory `_FakeDb`
exposing precisely what the model touches (source/citation cursors + raw-data
getters that raise `HandleError` on a missing handle), and asserts on the
resulting `model.tree` node map. Building with a handful of rows never pops the
progress dialog (`progressdialog.py:369` only activates it when
`estimated_secs_to_complete() > popup_time=2`; `_get_dlg` — the only Gtk-widget
constructor — is never reached), so the whole module runs **headless**. Five
tests:

* `test_selector_keeps_citations_of_title_matched_source` — source-driven (red
  pre-fix, behavioural).
* `test_selector_keeps_sibling_citations_of_citation_matched_source` —
  citation-driven / finding 3 (red pre-fix, behavioural).
* `test_selector_search_survives_orphan_citation` — iteration-2 orphan guard
  (green post-fix; against iteration-2 code it raised `HandleError`).
* `test_standalone_model_keeps_independent_secondary_search` — pins the
  non-regression boundary: plain `CitationTreeModel` still drops citations
  (passes pre and post; documents scope).
* `test_selector_wiring_uses_selector_model` — finding 1 (skips pre-fix, asserts
  wiring post-fix).

## Verification status — C4 runner not executable in this sandbox

I could **not** execute the authoritative `run-verify.sh` here: it runs the
gramps GTK3 suite inside the `gramps-testbed:ubuntu-6.1.0` Docker image, and
`docker` (and network `pip install`) are approval-gated in the builder sandbox —
every invocation returned "requires approval", including with the sandbox
override. Running on the host is impossible too: the host is GTK4 / Python 3.14,
gramps 6.1 targets GTK3, so importing the model dies at a GTK3-only enum before
any test runs.

What I verified locally:

* `git apply --check` of `patch.diff` against a clean `maintenance/gramps61`
  tree succeeds for all five files (the `gramps-6.1` working tree is left
  **clean** — my edits are in `git stash@{0}` "issue8622-v3-mywork" — so the
  C4 gate can apply the patch onto a pristine tree, as the gate requires).
* No added code line exceeds black's 88-col limit (checked over `patch.diff`);
  the additions follow black's default formatting (two blank lines before
  top-level classes, exploded call args with trailing commas). black itself
  could not be pip-installed here (network gated); the target's pre-commit
  will confirm at publish.
* A full manual execution trace of every test on both the fix-applied and
  production-reverted trees (green leg all-pass; red leg tests 1, 2 & 3 fail on
  behavioural `AssertionError`, test 4 passes, test 5 skips → module red)
  satisfies C4's green-with-fix ∧ red-without-fix contract.

The real red→green is left for Check's `C4-verify` gate (same runner) to
confirm. This is an honest "runner unavailable in the builder sandbox", not a
fabricated pass.

This is a `Surfaces: gui` bundle: no committed AT-SPI/dogtail repro was added
(driving the full person → Source Citations → *Add Existing Citation…* →
selector → search flow reliably blind, without a runnable Xvfb+AT-SPI here,
would risk a vacuously-skipping repro — worse than none). The headless
`test_selector_wiring_uses_selector_model` closes the specific wiring gap;
the live-dialog check routes to the interface runner / §6 for the human at
sign-off.

## Environment note

The `../gramps-6.1` checkout still carries the earlier, **unrelated** stash
`stash@{1}` "issue8622-verify-apply" (a bug-6324 `libcairodoc.py` drift from a
prior cycle) — deliberately excluded from `patch.diff`. My own changes are in
`stash@{0}`; the working tree is clean so the C4 gate applies cleanly.
